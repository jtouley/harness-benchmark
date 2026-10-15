package pipeline

import java.nio.file.Files

import org.scalatest.funsuite.AnyFunSuite

class BatchSpec extends AnyFunSuite with SparkSuite {
  import spark.implicits._

  test("CSV columns land as text: codes keep leading zeros, amounts their digits") {
    val csv = tempDir().resolve("t.csv")
    Files.write(csv, "STATE,COUNTY,amount,note\n01,001,-1250.10,\"two\nlines, \"\"quoted\"\"\"\n".getBytes("UTF-8"))
    val df = Batch.readText(spark, csv)
    assert(df.schema.fields.forall(_.dataType.typeName == "string"))
    assert(df.as[(String, String, String, String)].collect().toSeq ==
      Seq(("01", "001", "-1250.10", "two\nlines, \"quoted\"")))
  }

  test("a Latin-1 file is decoded as Latin-1") {
    val csv = tempDir().resolve("c.csv")
    Files.write(csv, "CTYNAME\nDoña Ana County\n".getBytes("ISO-8859-1"))
    assert(Batch.readText(spark, csv, "ISO-8859-1").as[String].head() == "Doña Ana County")
  }

  test("the site matrix flattens language groups and specials into one row per site") {
    val json =
      """{"sitematrix":{"count":3,
        |"0":{"code":"en","name":"English","localname":"English","site":[
        |  {"url":"https://en.wikipedia.org","dbname":"enwiki","code":"wiki","sitename":"Wikipedia"},
        |  {"url":"https://en.wikinews.org","dbname":"enwikinews","code":"wikinews","sitename":"Wikinews","closed":true}]},
        |"specials":[{"url":"https://commons.wikimedia.org","dbname":"commonswiki","code":"commons","lang":"commons",
        |  "sitename":"Wikimedia Commons","private":true}]}}""".stripMargin
    val sites = Batch.sitematrix(spark, json).as[Batch.Site].collect().sortBy(_.dbname).toSeq
    assert(sites.map(s => (s.dbname, s.language_code, s.is_special, s.is_closed, s.is_private)) == Seq(
      ("commonswiki", "commons", true, false, true),
      ("enwiki", "en", false, false, false),
      ("enwikinews", "en", false, true, false)))
  }
}
