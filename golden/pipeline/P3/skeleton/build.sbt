// The ingestion build. Every version is pinned: Scala 2.13.18, Spark 3.5.9 (its Scala 2.13 build),
// ScalaTest 3.2.20; sbt 1.12.15 in project/build.properties. The JDK is 17.

ThisBuild / scalaVersion := "2.13.18"
ThisBuild / version := "0.1.0"

lazy val root = (project in file("."))
  .settings(
    name := "open-data-pipeline",
    libraryDependencies ++= Seq(
      "org.apache.spark" %% "spark-sql" % "3.5.9",
      "org.scalatest" %% "scalatest" % "3.2.20" % Test
    ),
    // Spark runs in a forked JVM (local[*]), from the repository root. On JDK 17 it needs these
    // module openings (the list spark-submit passes, from Spark's JavaModuleOptions).
    fork := true,
    outputStrategy := Some(StdoutOutput),
    javaOptions ++= Seq(
      "-Xmx4g",
      "-XX:+IgnoreUnrecognizedVMOptions",
      "--add-opens=java.base/java.lang=ALL-UNNAMED",
      "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED",
      "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED",
      "--add-opens=java.base/java.io=ALL-UNNAMED",
      "--add-opens=java.base/java.net=ALL-UNNAMED",
      "--add-opens=java.base/java.nio=ALL-UNNAMED",
      "--add-opens=java.base/java.util=ALL-UNNAMED",
      "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED",
      "--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED",
      "--add-opens=java.base/jdk.internal.ref=ALL-UNNAMED",
      "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED",
      "--add-opens=java.base/sun.nio.cs=ALL-UNNAMED",
      "--add-opens=java.base/sun.security.action=ALL-UNNAMED",
      "--add-opens=java.base/sun.util.calendar=ALL-UNNAMED",
      "-Djdk.reflect.useDirectMethodHandle=false"
    ),
    Test / parallelExecution := false
  )
