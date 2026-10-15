package pipeline

import java.nio.file.Files

import org.scalatest.funsuite.AnyFunSuite

class SpoolSpec extends AnyFunSuite with SparkSuite {
  test("an empty spool starts at the beginning") {
    assert(new Spool(tempDir().resolve("spool")).position() == Position(None, 0L))
  }

  test("the position follows the last committed frame, across files") {
    val spool = new Spool(tempDir())
    spool.append(Seq(Received(Some("a"), 0, 1L, "{}"), Received(Some("b"), 1, 2L, "not json")))
    spool.append(Seq(Received(Some("c"), 2, 3L, "{\"x\":\"line\\nbreak\"}")))
    spool.append(Nil)
    assert(spool.position() == Position(Some("c"), 3L))
    assert(Files.list(spool.dir).count() == 2)
  }

  test("a file being written is hidden from the reader and from the position") {
    val spool = new Spool(tempDir())
    spool.append(Seq(Received(Some("a"), 0, 1L, "{}")))
    Files.write(spool.dir.resolve(".0000000002.jsonl.tmp"), "{\"sse_id\":\"z\",\"arrival_seq\":9}".getBytes)
    assert(spool.position() == Position(Some("a"), 1L))
    val rows = spark.read.schema(Spool.Schema).json(spool.dir.toString).collect()
    assert(rows.map(_.getAs[String]("sse_id")).toSeq == Seq("a"))
  }

  test("spooled data reads back byte for byte") {
    val spool = new Spool(tempDir())
    val data = "{\"title\":\"Doña \\\"Ana\\\"\",\n\"n\":1}"
    spool.append(Seq(Received(None, 0, 1L, data)))
    val row = spark.read.schema(Spool.Schema).json(spool.dir.toString).head()
    assert(row.getAs[String]("data") == data)
    assert(row.isNullAt(row.fieldIndex("sse_id")))
  }
}
