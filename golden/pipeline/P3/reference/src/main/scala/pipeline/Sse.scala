package pipeline

import java.io.{BufferedReader, IOException, InputStreamReader}
import java.net.{HttpURLConnection, URI}
import java.nio.charset.StandardCharsets

import scala.collection.mutable.ArrayBuffer

/** One Server-Sent Events message: its data, and the last event id in effect after it (an SSE id
  * persists until a frame sets a new one).
  */
final case class Frame(id: Option[String], data: String)

/** Line by line SSE parsing: feed each line, get a frame at the blank line that ends it. */
final class SseParser {
  private var lastId: Option[String] = None
  private val data = ArrayBuffer.empty[String]

  def feed(line: String): Option[Frame] =
    if (line.isEmpty) {
      val frame = if (data.nonEmpty) Some(Frame(lastId, data.mkString("\n"))) else None
      data.clear()
      frame
    } else if (line.startsWith(":")) None // a comment or keep-alive
    else {
      val (field, value) = line.indexOf(':') match {
        case -1 => (line, "")
        case i  => (line.take(i), line.drop(i + 1).stripPrefix(" "))
      }
      field match {
        case "id"   => lastId = Some(value)
        case "data" => data += value
        case _      => ()
      }
      None
    }
}

/** An SSE client that reconnects with Last-Event-ID whenever the connection drops, until stopped. */
final class SseClient(url: String, readTimeoutMs: Int = 15000, retryMs: Long = 1000) {
  @volatile private var stopped = false
  @volatile private var current: Option[HttpURLConnection] = None

  /** Call `onFrame` for each frame, resuming after `lastId`, until `stop()`. */
  def run(lastId: Option[String])(onFrame: Frame => Unit): Unit = {
    var resumeAt = lastId
    while (!stopped) {
      try {
        val conn = URI.create(url).toURL.openConnection().asInstanceOf[HttpURLConnection]
        conn.setRequestProperty("Accept", "text/event-stream")
        conn.setRequestProperty("User-Agent", "open-data-pipeline/0.1 (stream consumer)")
        resumeAt.foreach(conn.setRequestProperty("Last-Event-ID", _))
        conn.setConnectTimeout(5000)
        conn.setReadTimeout(readTimeoutMs)
        current = Some(conn)
        val reader = new BufferedReader(new InputStreamReader(conn.getInputStream, StandardCharsets.UTF_8))
        try {
          val parser = new SseParser
          var line = reader.readLine()
          while (line != null && !stopped) {
            parser.feed(line).foreach { frame =>
              onFrame(frame)
              resumeAt = frame.id.orElse(resumeAt)
            }
            line = reader.readLine()
          }
        } finally reader.close()
      } catch {
        case _: IOException => () // dropped: reconnect from the last frame handed out
      } finally current = None
      if (!stopped) Thread.sleep(retryMs)
    }
  }

  /** Stop: closes the open connection, so a blocked read returns at once. A frame cut short is not
    * handed out, and the next run resumes after the last one that was.
    */
  def stop(): Unit = {
    stopped = true
    current.foreach(_.disconnect())
  }
}
