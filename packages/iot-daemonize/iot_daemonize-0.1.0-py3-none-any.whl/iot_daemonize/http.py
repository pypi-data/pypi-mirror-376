import logging

from bottle import ServerAdapter
from wsgiref.simple_server import make_server, WSGIRequestHandler


logger = logging.getLogger(__name__)


class StoppableBottleHTTPServer(ServerAdapter):
    _server = None

    def __init__(self, config):
        super().__init__(host=config.http_host, port=config.http_port)

    def run(self, handler):
        logger.info(f"Starting HTTP server on port {self.port}")
        self._server = make_server(self.host, self.port, handler, **self.options)
        self._server.serve_forever()

    def stop(self):
        logger.info(f"Stopping HTTP server on port {self.port}")
        self._server.shutdown()
