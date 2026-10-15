package pipeline

import java.nio.file.{Files, Path}
import java.util.zip.ZipFile

import scala.jdk.CollectionConverters._
import scala.util.Using

import com.fasterxml.jackson.databind.{JsonNode, ObjectMapper}
import org.apache.spark.sql.functions.lit
import org.apache.spark.sql.{DataFrame, SparkSession}

/** Batch ingestion: the raw files in data/raw/ into the Parquet lake.
  *
  * Every CSV column lands as text, exactly as the source wrote it (no schema inference), so codes keep
  * their leading zeros and amounts their exact decimal digits; the dbt staging models apply types.
  * Each table is replaced on every run.
  *
  *   sbt "runMain pipeline.Batch"
  */
object Batch {
  final case class Site(
      dbname: String,
      url: String,
      project_code: String,
      sitename: String,
      language_code: String,
      language_name: String,
      is_special: Boolean,
      is_closed: Boolean,
      is_private: Boolean
  )

  def main(args: Array[String]): Unit = {
    val spark = Lake.session("batch")
    try run(spark, Lake.Root.resolve("data").resolve("raw"))
    finally spark.stop()
  }

  def run(spark: SparkSession, raw: Path): Unit = {
    Seq("Assistance", "Contracts").foreach { kind =>
      withExtracted(raw.resolve("usaspending"), kind) { members =>
        Lake.replace(usaspending(spark, members), s"usaspending_${kind.toLowerCase}")
      }
    }
    Seq("2024", "2021").foreach { vintage =>
      // The Census Bureau publishes these files in Latin-1 (for example "Doña Ana County").
      val csv = raw.resolve("census").resolve(s"co-est$vintage-alldata.csv")
      Lake.replace(readText(spark, csv, encoding = "ISO-8859-1"), s"census_co_est$vintage")
    }
    Lake.replace(sitematrix(spark, new String(Files.readAllBytes(raw.resolve("sitematrix.json")), "UTF-8")),
      "wikimedia_sitematrix")
  }

  /** A CSV with a header, every column as a string. Quoted values may span lines and escape a quote
    * by doubling it (RFC 4180), as the USAspending files do.
    */
  def readText(spark: SparkSession, csv: Path, encoding: String = "UTF-8"): DataFrame =
    spark.read
      .option("header", "true")
      .option("inferSchema", "false")
      .option("multiLine", "true")
      .option("quote", "\"")
      .option("escape", "\"")
      .option("encoding", encoding)
      .csv(csv.toString)

  /** Each CSV member of one award type's agency zips, with its `zip/member` as source_file. */
  def usaspending(spark: SparkSession, members: Seq[(String, Path)]): DataFrame =
    members
      .map { case (source, file) => readText(spark, file).withColumn("source_file", lit(source)) }
      .reduce(_.unionByName(_, allowMissingColumns = true))

  /** Extract the CSVs of FY2024_*_<kind>_Full_*.zip to a temporary folder for the duration of `use`
    * (Spark reads files, not zip members). The folder is deleted afterwards.
    */
  private def withExtracted[A](dir: Path, kind: String)(use: Seq[(String, Path)] => A): A = {
    val tmp = Files.createTempDirectory(s"usaspending-$kind")
    try {
      val zips = Files.list(dir).iterator().asScala.toSeq
        .filter(p => p.getFileName.toString.matches(s"FY2024_.*_${kind}_Full_.*\\.zip"))
        .sortBy(_.getFileName.toString)
      val members = zips.flatMap { zip =>
        Using.resource(new ZipFile(zip.toFile)) { zf =>
          zf.entries().asScala.map(_.getName).filter(_.endsWith(".csv")).toSeq.sorted.zipWithIndex.map {
            case (name, i) =>
              val out = tmp.resolve(s"${zip.getFileName}-$i.csv")
              Using.resource(zf.getInputStream(zf.getEntry(name)))(in => Files.copy(in, out))
              (s"${zip.getFileName}/$name", out)
          }
        }
      }
      use(members)
    } finally {
      Files.walk(tmp).iterator().asScala.toSeq.reverse.foreach(Files.deleteIfExists)
    }
  }

  /** One row per Wikimedia site: the language groups ("0", "1", ...) and the specials. */
  def sitematrix(spark: SparkSession, json: String): DataFrame = {
    import spark.implicits._
    val matrix = new ObjectMapper().readTree(json).get("sitematrix")
    def text(node: JsonNode, field: String): String =
      Option(node.get(field)).filter(!_.isNull).map(_.asText).orNull
    def flag(node: JsonNode, field: String): Boolean =
      Option(node.get(field)).exists(_.asBoolean)
    val sites = matrix.fields().asScala.toSeq.filter(_.getKey != "count").flatMap { entry =>
      val special = entry.getKey == "specials"
      val group = entry.getValue
      val members = if (special) group.elements().asScala.toSeq
                    else Option(group.get("site")).map(_.elements().asScala.toSeq).getOrElse(Nil)
      members.map { site =>
        Site(
          dbname = text(site, "dbname"),
          url = text(site, "url"),
          project_code = text(site, "code"),
          sitename = text(site, "sitename"),
          language_code = if (special) text(site, "lang") else text(group, "code"),
          language_name = if (special) null else text(group, "localname"),
          is_special = special,
          is_closed = flag(site, "closed"),
          is_private = flag(site, "private")
        )
      }
    }
    sites.toDF()
  }
}
