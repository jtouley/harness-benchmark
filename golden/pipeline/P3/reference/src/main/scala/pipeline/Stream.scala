package pipeline

import java.nio.file.Path

import scala.collection.mutable.ArrayBuffer
import scala.util.Try

import com.fasterxml.jackson.core.JsonParser
import com.fasterxml.jackson.databind.{DeserializationFeature, ObjectMapper}
import org.apache.spark.sql.functions.{col, get_json_object, timestamp_millis, udf}
import org.apache.spark.sql.streaming.Trigger
import org.apache.spark.sql.{DataFrame, SaveMode, SparkSession}

/** Stream ingestion: the recentchange SSE stream into the lake, through Spark Structured Streaming.
  *
  * Spark has no SSE source, so a small reader feeds it: an SSE client thread commits the frames it
  * receives to the spool (lake/_checkpoints/recentchange/spool/), and a streaming query reads the spool
  * as a file source, with its checkpoint in lake/_checkpoints/recentchange/query/, and lands each
  * micro-batch in the lake. Exactly once across restarts and disconnects:
  *
  *  - the reader resumes after the last spooled frame (its SSE id is committed with it), so a restart
  *    neither skips nor re-reads a frame the reader already committed;
  *  - the query's checkpoint records which spool files it has landed, and a micro-batch is written to
  *    its own folder (batch_id=N) by overwrite, so a batch re-run after a crash replaces its own files.
  *
  * Each landed row is the event exactly as received (`event`, the JSON text) plus load metadata:
  * `event_id` (meta.id), `sse_id`, `arrival_seq` (arrival order across restarts), `received_at` and the
  * `batch_id` partition. The server re-sends some events on a resume; the dbt staging model keeps the
  * first copy of each event. Frames that are not valid JSON, or have no meta.id, go to
  * recentchange_rejects.
  *
  *   sbt "runMain pipeline.Stream 60"      (seconds to consume)
  */
object Stream {
  val Events = "recentchange_events"
  val Rejects = "recentchange_rejects"
  val Url: String = sys.env.getOrElse("STREAM_URL", "http://localhost:8099/v2/stream/recentchange")
  private val FlushMs = 2000L

  def main(args: Array[String]): Unit = {
    val seconds = args.headOption.map(_.toDouble).getOrElse(sys.error("usage: Stream <seconds>"))
    val spark = Lake.session("stream")
    try println(s"stream: spooled ${consume(spark, (seconds * 1000).toLong)} frames")
    finally spark.stop()
  }

  def consume(spark: SparkSession, durationMs: Long): Long = {
    val base = Lake.Checkpoints.resolve("recentchange")
    val spool = new Spool(base.resolve("spool"))
    val query = spark.readStream
      .schema(Spool.Schema)
      .json(spool.dir.toString)
      .writeStream
      .option("checkpointLocation", base.resolve("query").toString)
      .trigger(Trigger.ProcessingTime("5 seconds"))
      .foreachBatch((frames: DataFrame, batchId: Long) => land(frames, batchId))
      .start()
    val received = read(spool, durationMs)
    query.processAllAvailable() // land every committed spool file before stopping
    query.stop()
    received
  }

  /** Read the stream for `durationMs`, committing to the spool every FlushMs. Returns frames read. */
  private def read(spool: Spool, durationMs: Long): Long = {
    val start = spool.position()
    val client = new SseClient(Url)
    val buffer = ArrayBuffer.empty[Received]
    var nextSeq = start.nextSeq
    var lastFlush = System.currentTimeMillis()
    val lock = new Object
    def flush(): Unit = lock.synchronized {
      spool.append(buffer.toSeq)
      buffer.clear()
      lastFlush = System.currentTimeMillis()
    }
    val thread = new Thread(() =>
      client.run(start.lastEventId) { frame =>
        lock.synchronized {
          buffer += Received(frame.id, nextSeq, System.currentTimeMillis(), frame.data)
          nextSeq += 1
        }
        if (System.currentTimeMillis() - lastFlush >= FlushMs) flush()
      })
    thread.setDaemon(true)
    thread.start()
    val deadline = System.currentTimeMillis() + durationMs
    while (System.currentTimeMillis() < deadline) {
      Thread.sleep(math.min(FlushMs, math.max(1L, deadline - System.currentTimeMillis())))
      flush() // a quiet stream still commits what it has
    }
    client.stop()
    thread.join(10000)
    flush()
    nextSeq - start.nextSeq
  }

  private object Json {
    lazy val mapper: ObjectMapper = new ObjectMapper()
      .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
      .disable(JsonParser.Feature.AUTO_CLOSE_SOURCE)
    def valid(text: String): Boolean = text != null && Try(mapper.readTree(text)).toOption.exists(_ != null)
  }

  private val isJson = udf((text: String) => Json.valid(text))

  /** Split spooled frames into landed events and rejects: frames that are not valid JSON, or are JSON
    * with no `meta.id` (`{}`, a bare number, an empty data line), which no event key can identify.
    */
  def split(frames: DataFrame): (DataFrame, DataFrame) = {
    val typed = frames
      .withColumn("received_at", timestamp_millis(col("received_at_ms")))
      .withColumn("event_id", get_json_object(col("data"), "$.meta.id"))
      .withColumn("valid", isJson(col("data")) && col("event_id").isNotNull)
    val events = typed.filter(col("valid")).select(
      col("data").as("event"), col("event_id"),
      col("sse_id"), col("arrival_seq"), col("received_at"))
    val rejects = typed.filter(!col("valid")).select(
      col("data").as("raw"), col("sse_id"), col("arrival_seq"), col("received_at"))
    (events, rejects)
  }

  /** Land one micro-batch. Each table's batch goes to its own folder, replaced on a re-run. */
  def land(frames: DataFrame, batchId: Long, lake: Path = Lake.Dir): Unit = {
    val (events, rejects) = split(frames.persist())
    Seq(Events -> events, Rejects -> rejects).foreach { case (table, rows) =>
      if (!rows.isEmpty)
        rows.write.mode(SaveMode.Overwrite).parquet(lake.resolve(table).resolve(s"batch_id=$batchId").toString)
    }
    frames.unpersist()
  }
}
