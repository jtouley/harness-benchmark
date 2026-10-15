package pipeline

import java.net.InetSocketAddress
import java.nio.charset.StandardCharsets
import java.util.concurrent.{ConcurrentLinkedQueue, CountDownLatch, TimeUnit}

import scala.jdk.CollectionConverters._

import com.sun.net.httpserver.HttpServer
import org.scalatest.funsuite.AnyFunSuite

class SseClientSpec extends AnyFunSuite {
  test("after a dropped connection the client reconnects with the last id it handed out") {
    val lastIds = new ConcurrentLinkedQueue[String]()
    val server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0)
    server.createContext("/stream", exchange => {
      lastIds.add(Option(exchange.getRequestHeaders.getFirst("Last-Event-ID")).getOrElse("-"))
      val body = if (lastIds.size == 1) "id: a\ndata: 1\n\nid: b\ndata: 2\n\n" else "id: c\ndata: 3\n\n"
      val bytes = body.getBytes(StandardCharsets.UTF_8)
      exchange.getResponseHeaders.add("Content-Type", "text/event-stream")
      exchange.sendResponseHeaders(200, bytes.length.toLong)
      exchange.getResponseBody.write(bytes)
      exchange.close() // the server drops the connection after each response
    })
    server.start()
    try {
      val client = new SseClient(s"http://127.0.0.1:${server.getAddress.getPort}/stream", retryMs = 10)
      val frames = new ConcurrentLinkedQueue[Frame]()
      val three = new CountDownLatch(3)
      val thread = new Thread(() => client.run(Some("start")) { f => frames.add(f); three.countDown() })
      thread.start()
      assert(three.await(10, TimeUnit.SECONDS))
      client.stop()
      thread.join(5000)
      assert(frames.asScala.toSeq.take(3) == Seq(Frame(Some("a"), "1"), Frame(Some("b"), "2"), Frame(Some("c"), "3")))
      assert(lastIds.asScala.toSeq.take(2) == Seq("start", "b"))
    } finally server.stop(0)
  }
}
