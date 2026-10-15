package pipeline

import java.nio.file.{Path, Paths}

import org.apache.spark.sql.{DataFrame, SaveMode, SparkSession}

/** The Parquet lake under lake/: one folder per source table. Paths resolve from the repository root,
  * where sbt forks the job.
  */
object Lake {
  val Root: Path = Paths.get("").toAbsolutePath
  val Dir: Path = Root.resolve("lake")
  val Checkpoints: Path = Dir.resolve("_checkpoints")

  def path(table: String): String = Dir.resolve(table).toString

  /** Local Spark, in UTC, writing timestamps as Parquet microseconds (not INT96). */
  def session(app: String): SparkSession =
    SparkSession
      .builder()
      .appName(app)
      .master("local[*]")
      .config("spark.sql.session.timeZone", "UTC")
      .config("spark.sql.parquet.outputTimestampType", "TIMESTAMP_MICROS")
      .config("spark.sql.shuffle.partitions", "4")
      .config("spark.ui.enabled", "false")
      .getOrCreate()

  /** Replace a whole lake table. SaveMode.Overwrite, so a second run leaves the same rows, never a
    * second copy beside the first (the default mode fails on an existing folder; Append doubles it).
    */
  def replace(df: DataFrame, table: String): Unit =
    df.write.mode(SaveMode.Overwrite).parquet(path(table))
}
