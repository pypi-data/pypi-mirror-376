import logging
import ssl
import time

import paho.mqtt.client as mqtt

from typing import Final

import iot_daemonize.configuration as configuration

logger = logging.getLogger(__name__)

verify_mode: Final = {
    'CERT_NONE': ssl.CERT_NONE,
    'CERT_OPTIONAL': ssl.CERT_OPTIONAL,
    'CERT_REQUIRED': ssl.CERT_REQUIRED
}

tls_versions: Final = {
    'TLSv1': ssl.PROTOCOL_TLSv1,
    'TLSv1.1': ssl.PROTOCOL_TLSv1_1,
    'TLSv1.2': ssl.PROTOCOL_TLSv1_2
}

class MqttDaemon:
    def __init__(self, config: configuration.MqttDaemonConfiguration):
        self._config = config
        self._init_mqtt_client()
        self._connect_mqtt_client()


    def publish(self, topic: str, payload: str):
        logger.info(f'Publishing to topic {topic} payload {payload}')
        self._mqtt_client.publish(topic, payload)
        if self._config.timestamp:
            self._mqtt_client.publish("{}/timestamp".format(topic), time.time(), retain=True)

    def start(self):
        if self._mqtt_client is None:
            raise Exception("MQTT client not initialized")
        self._mqtt_client.loop_start()


    def stop(self):
        if self._mqtt_client is None:
            raise Exception("MQTT client not initialized")
        logger.info('Stopping MQTT')
        self._mqtt_client.loop_stop()
        self._mqtt_client.disconnect()
        logger.info('MQTT disconnected')


    def _init_mqtt_client(self):
        mqtt_clientid = self._config.mqtt_clientid if self._config.mqtt_clientid else 'iot-daemonize'
        self._mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, mqtt_clientid)
        if self._config.mqtt_tls:
            cert_reqs = verify_mode[self._config.mqtt_verify_mode] if self._config.mqtt_verify_mode in verify_mode else None
            tls_version = tls_versions[self._config.mqtt_tls_version] if self._config.mqtt_tls_version in tls_versions else None
            ca_certs = self._config.mqtt_ssl_ca_path if self._config.mqtt_ssl_ca_path else None
            self._mqtt_client.tls_set(ca_certs=ca_certs, cert_reqs=cert_reqs, tls_version=tls_version)
            self._mqtt_client.tls_insecure_set(self._config.mqtt_tls_no_verify)
        if self._config.verbose:
            self._mqtt_client.enable_logger()
        if self._config.mqtt_user is not None and self._config.mqtt_password is not None:
            self._mqtt_client.username_pw_set(self._config.mqtt_user, self._config.mqtt_password)


    def _connect_mqtt_client(self):
        if self._mqtt_client is None:
            raise Exception("MQTT client not initialized")
        self._mqtt_client.connect(self._config.mqtt_host, self._config.mqtt_port, self._config.mqtt_keepalive)
