from .configuration import Configuration, MqttDaemonConfiguration
from .daemonize import Daemon
from .http import StoppableBottleHTTPServer
from .mqtt import MqttDaemon

__all__ = [
    "Configuration",
    "Daemon",
    "MqttDaemon",
    "MqttDaemonConfiguration",
    "StoppableBottleHTTPServer"
]

from .__version__ import __version__


import logging
import signal

logger = logging.getLogger(__name__)

daemon: Daemon = None
http_server: StoppableBottleHTTPServer = None
mqtt_client: MqttDaemon = None


def init(config: MqttDaemonConfiguration, mqtt: bool = False, http: bool = False, daemonize: bool = False):
    global daemon, http_server, mqtt_client

    logger.info("Initializing...")

    if config.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if daemonize:
        logger.info("Initializing daemon for multi-threaded task execution")
        daemon = Daemon()
    if mqtt:
        logger.info("Initializing MQTT client thread")
        mqtt_client = MqttDaemon(config)
    if http:
        logger.info("Initializing HTTP server thread")
        http_server = StoppableBottleHTTPServer(config)


def run():
    logger.info("Starting...")
    if mqtt_client is not None:
        logger.info("Starting MQTT client")
        mqtt_client.start()
    if daemon is not None:
        logger.info("Starting daemon threads")
        daemon.run()


def shutdown(signum, frame):
    global daemon, http_server, mqtt_client
    logger.info("Shutdown...")
    if mqtt_client is not None:
        logger.info("Stopping MQTT client")
        mqtt_client.stop()
    if daemon is not None:
        logger.info("Stopping daemon threads")
        daemon.stop()
    if http_server is not None:
        logger.info("Stopping HTTP server")
        http_server.stop()
    logger.info("Bye!")
    exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)
