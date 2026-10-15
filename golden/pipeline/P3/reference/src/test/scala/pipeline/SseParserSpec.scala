package pipeline

import org.scalatest.funsuite.AnyFunSuite

class SseParserSpec extends AnyFunSuite {
  private def parse(lines: String*): Seq[Frame] = {
    val parser = new SseParser
    lines.flatMap(parser.feed)
  }

  test("a frame ends at a blank line and carries its id") {
    assert(parse(":ok", "", "event: message", "id: [1]", "data: {\"a\":1}", "") == Seq(Frame(Some("[1]"), "{\"a\":1}")))
  }

  test("data lines of one frame join with a newline") {
    assert(parse("data: one", "data: two", "") == Seq(Frame(None, "one\ntwo")))
  }

  test("comments and keep-alives yield nothing") {
    assert(parse(":", "", ": keep-alive", "") == Nil)
  }

  test("the last id persists to a frame that sets none") {
    assert(parse("id: a", "data: 1", "", "data: 2", "").map(_.id) == Seq(Some("a"), Some("a")))
  }

  test("a value keeps its text after the first colon and one space") {
    assert(parse("data:  x: y", "") == Seq(Frame(None, " x: y")))
  }
}
