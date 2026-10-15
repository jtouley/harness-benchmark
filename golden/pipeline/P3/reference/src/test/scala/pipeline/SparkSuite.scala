package pipeline

import java.nio.file.{Files, Path}

import scala.jdk.CollectionConverters._

import org.apache.spark.sql.SparkSession
import org.scalatest.{BeforeAndAfterAll, Suite}

/** One local SparkSession per suite, and temporary folders removed after it. */
trait SparkSuite extends BeforeAndAfterAll { self: Suite =>
  lazy val spark: SparkSession = SparkSession.builder()
    .master("local[2]")
    .appName(getClass.getSimpleName)
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.sql.shuffle.partitions", "2")
    .config("spark.ui.enabled", "false")
    .getOrCreate()

  private var temps = List.empty[Path]

  def tempDir(): Path = {
    val dir = Files.createTempDirectory("pipeline-test")
    temps ::= dir
    dir
  }

  override def afterAll(): Unit = {
    temps.foreach(d => Files.walk(d).iterator().asScala.toSeq.reverse.foreach(Files.deleteIfExists))
    super.afterAll()
  }
}
