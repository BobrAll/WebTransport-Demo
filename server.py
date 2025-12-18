import asyncio
import os
from aioquic.asyncio import serve
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import HeadersReceived, WebTransportStreamDataReceived, DatagramReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import ProtocolNegotiated

class WebTransportProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.h3 = None
        self.webtransport_session_id = None

    def quic_event_received(self, event):
        if isinstance(event, ProtocolNegotiated):
            self.h3 = H3Connection(self._quic, enable_webtransport=True)

        if not self.h3:
            return

        for http_event in self.h3.handle_event(event):
            self._handle_http_event(http_event)

    def _handle_http_event(self, event):
        if isinstance(event, HeadersReceived):
            self._handle_headers(event)
        elif isinstance(event, WebTransportStreamDataReceived):
            self._handle_stream_data(event)
        elif isinstance(event, DatagramReceived):
            self._handle_datagram(event)

    def _handle_headers(self, event):
        headers = dict(event.headers)
        method = headers.get(b":method")
        protocol = headers.get(b":protocol")
        path = headers.get(b":path", b"/").decode()

        if method == b"CONNECT" and protocol == b"webtransport":
            self.webtransport_session_id = event.stream_id
            self.h3.send_headers(
                stream_id=event.stream_id,
                headers=[(b":status", b"200")]
            )
        elif method == b"GET":
            self._serve_static(event.stream_id, path)

    def _handle_stream_data(self, event):
        print(f"Stream received: {event.data}")
        response = b"Stream ECHO: " + event.data
        self._quic.send_stream_data(event.stream_id, response, end_stream=False)

    def _handle_datagram(self, event):
        print(f"Datagram received: {event.data}")
        if self.webtransport_session_id is not None:
            response = b"Dgram ECHO: " + event.data
            self.h3.send_datagram(self.webtransport_session_id, response)

    def _serve_static(self, stream_id, path):
        if path == "/" or path == "/index.html":
            self._send_file(stream_id, "index.html", b"text/html")
        elif path == "/script.js":
            self._send_file(stream_id, "script.js", b"application/javascript")
        elif path == "/style.css":
            self._send_file(stream_id, "style.css", b"text/css")
        else:
            self._send_error(stream_id, 404)

    def _send_file(self, stream_id, filename, content_type):
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                data = f.read()
            self._send_response(stream_id, 200, data, content_type)
        else:
            self._send_error(stream_id, 404)

    def _send_error(self, stream_id, code):
        self._send_response(stream_id, code, b"Error", b"text/plain")

    def _send_response(self, stream_id, status_code, data, content_type):
        headers = [
            (b":status", str(status_code).encode()),
            (b"content-type", content_type),
            (b"content-length", str(len(data)).encode()),
        ]
        self.h3.send_headers(stream_id=stream_id, headers=headers)
        self.h3.send_data(stream_id=stream_id, data=data, end_stream=True)

async def main():
    config = QuicConfiguration(
        is_client=False, 
        alpn_protocols=["h3"],
        max_datagram_frame_size=65536
    )
    config.load_cert_chain("cert.pem", "key.pem")

    print("Server running on https://127.0.0.1:4433")
    await serve(host="127.0.0.1", port=4433, configuration=config, create_protocol=WebTransportProtocol)
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped")
