package pipeline

import java.nio.file.{Files, Path, StandardCopyOption}
import java.nio.charset.StandardCharsets

import scala.jdk.CollectionConverters._

import com.fasterxml.jackson.databind.ObjectMapper
import org.apache.spark.sql.types._

/** A frame as received, numbered in arrival order across restarts. */
final case class Received(sseId: Option[String], arrivalSeq: Long, receivedAtMs: Long, data: String)

/** Where the consumer stands: the SSE id to resume after and the next arrival number. */
final case class Position(lastEventId: Option[String], nextSeq: Long)

/** The reader's durable hand-off to Structured Streaming: numbered JSON Lines files, one per flush.
  *
  * A file is written under a hidden name and renamed into place, so it appears whole or not at all, and
  * the frames and the position they end at are committed in the same step. The streaming query reads
  * the folder as a file source; its checkpoint records which files it has landed.
  */
final class Spool(val dir: Path) {
  private val mapper = new ObjectMapper()

  Files.createDirectories(dir)

  private def files: Seq[Path] =
    Files.list(dir).iterator().asScala.toSeq.filter(_.getFileName.toString.endsWith(".jsonl"))
      .sortBy(_.getFileName.toString)

  /** The position after the last committed frame (the start, when nothing is spooled yet). */
  def position(): Position =
    files.lastOption.flatMap { last =>
      Files.readAllLines(last, StandardCharsets.UTF_8).asScala.filter(_.nonEmpty).lastOption
    } match {
      case None => Position(None, 0L)
      case Some(line) =>
        val node = mapper.readTree(line)
        Position(Option(node.get("sse_id")).filterNot(_.isNull).map(_.asText), node.get("arrival_seq").asLong + 1)
    }

  /** Commit frames atomically; nothing is written for an empty list. */
  def append(frames: Seq[Received]): Unit = if (frames.nonEmpty) {
    val number = files.lastOption.map(_.getFileName.toString.stripSuffix(".jsonl").toLong + 1).getOrElse(1L)
    val name = f"$number%010d.jsonl"
    val tmp = dir.resolve(s".$name.tmp")
    val lines = frames.map { f =>
      val node = mapper.createObjectNode()
      f.sseId match {
        case Some(id) => node.put("sse_id", id)
        case None     => node.putNull("sse_id")
      }
      node.put("arrival_seq", f.arrivalSeq)
      node.put("received_at_ms", f.receivedAtMs)
      node.put("data", f.data)
      mapper.writeValueAsString(node)
    }
    Files.write(tmp, (lines.mkString("\n") + "\n").getBytes(StandardCharsets.UTF_8))
    Files.move(tmp, dir.resolve(name), StandardCopyOption.ATOMIC_MOVE)
  }
}

object Spool {
  val Schema: StructType = StructType(Seq(
    StructField("sse_id", StringType),
    StructField("arrival_seq", LongType),
    StructField("received_at_ms", LongType),
    StructField("data", StringType)
  ))
}
