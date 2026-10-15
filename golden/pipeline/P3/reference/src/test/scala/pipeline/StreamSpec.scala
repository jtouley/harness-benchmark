package pipeline

import org.scalatest.funsuite.AnyFunSuite

class StreamSpec extends AnyFunSuite with SparkSuite {
  import spark.implicits._

  private def frames = Seq(
    ("[1]", 0L, 1700000000000L, """{"meta":{"id":"e1","domain":"en.wikipedia.org"},"type":"edit"}"""),
    ("[2]", 1L, 1700000001000L, """{"meta":{"id":"e2"""),
    ("[3]", 2L, 1700000002000L, """{"meta":{"id":"e3"}} trailing"""),
    ("[4]", 3L, 1700000003000L, """{"meta":{"id":"e1","domain":"en.wikipedia.org"},"type":"edit"}"""),
    ("[5]", 4L, 1700000004000L, "{}"),
    ("[6]", 5L, 1700000005000L, "42"),
    ("[7]", 6L, 1700000006000L, "")
  ).toDF("sse_id", "arrival_seq", "received_at_ms", "data")

  test("frames with a meta.id become events; the rest (not JSON, or JSON with no meta.id) become rejects") {
    val (events, rejects) = Stream.split(frames)
    assert(events.select("event_id", "arrival_seq").as[(String, Long)].collect().toSeq == Seq("e1" -> 0L, "e1" -> 3L))
    assert(rejects.select("arrival_seq").as[Long].collect().toSeq == Seq(1L, 2L, 4L, 5L, 6L))
    assert(events.schema("received_at").dataType.typeName == "timestamp")
  }

  test("an event lands exactly as it was received") {
    val (events, _) = Stream.split(frames)
    assert(events.select("event").as[String].head() ==
      """{"meta":{"id":"e1","domain":"en.wikipedia.org"},"type":"edit"}""")
  }

  test("landing a micro-batch again replaces it, never adds a second copy") {
    val lake = tempDir()
    Stream.land(frames, 7L, lake)
    Stream.land(frames, 7L, lake)
    Stream.land(frames.limit(1), 8L, lake)
    val landed = spark.read.parquet(lake.resolve(Stream.Events).toString)
    assert(landed.groupBy("batch_id").count().as[(Int, Long)].collect().toMap == Map(7 -> 2L, 8 -> 1L))
    assert(spark.read.parquet(lake.resolve(Stream.Rejects).toString).count() == 5)
  }
}
