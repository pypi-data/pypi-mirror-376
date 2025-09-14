import argparse
import json
import logging
import os

from typing import Any, Final, Optional, Union


logger = logging.getLogger(__name__)

# see https://docs.python.org/3/library/argparse.html#action
EXPECTED_OPTIONS: Final = (
    None,
    'store', 'store_const',
    'store_true', 'store_false',
    'append', 'append_const',
    'count',
    'help', 'version',
    'parsers', 'extend'
)

class Configuration:


    def __init__(self, program: str  = 'iot-daemonize configuration', description: Optional[str] = None, epilog: Optional[str] = None):
        self._program = program
        self._description = description
        self._epilog = epilog

        self._argument_parser: Optional[argparse.ArgumentParser] = None
        self._config_args: dict[str, dict[str, Union[str, int, float, bool]]] = {}
        self._config_args_flags_map: dict[str, str] = {}
        self._config_values: dict[str, Any] = {}


    def __getattr__(self, name: str) -> Any:
        if name not in self._config_values:
            return None
        return self._config_values[name]


    def add_config_arg(self, arg: str, default: Optional[Union[str, int, float, bool]] = None, help: Optional[str] = None, action: Optional[str] = None, flags: Optional[Union[str, list[str]]] = None):
        self._config_args[arg] = {}
        if default is not None:
            self._config_args[arg]['default'] = default
        if help is not None:
            self._config_args[arg]['help'] = help
        if action in EXPECTED_OPTIONS:
            self._config_args[arg]['action'] = action
        # if flags is a string, convert to a list, as we expect a list of flags
        if flags is not None and type(flags) is str:
            flags = [flags]
        if flags is not None and type(flags) is list:
            # ensure flags are unique and create mapping from flag to arg
            for flag in flags:
                flag = flag.replace('-', '')
                if self._config_args_flags_map.get(flag) is not None:
                    raise Exception(f"Flag {flag} already exists")
                self._config_args_flags_map[flag] = arg
            self._config_args[arg]['flags'] = flags


    def parse_args(self):
        self._init_argument_parser()
        args = self._argument_parser.parse_args()
        for flag, value in vars(args).items():
            if self._config_args_flags_map.get(flag) is None:
                raise Exception(f"No mapping found for {flag}")
            arg = self._config_args_flags_map[flag]
            self._config_values[arg] = value


    def parse_config(self, config_file: str):
        self._load_config_file(config_file)
        for arg, options in self._config_args.items():
            if arg in self._config_file:
                self._config_values[arg] = self._config_file[arg]


    def _init_argument_parser(self):
        parser = argparse.ArgumentParser(
            prog=self._program, description=self._description, epilog=self._epilog)
        for arg, options in self._config_args.items():
            if 'flags' in options:
                name_or_flags = options['flags']
                arg_action = options['action'] if 'action' in options else None
                arg_help = options['help'] if 'help' in options else None
                arg_default = options['default'] if 'default' in options else None
                parser.add_argument(*name_or_flags, action=arg_action, help=arg_help, default=arg_default)
        self._argument_parser = parser


    def _load_config_file(self, config_file: str):
        if not os.path.isfile(config_file):
            logger.error(f"Config file not found {config_file}")
            raise Exception(f"Config file not found {config_file}")
        with open(config_file, "r") as _cf:
            self._config_file = json.load(_cf)


class MqttDaemonConfiguration(Configuration):
    def __init__(self, program: str  = 'iot-daemonize MQTT configuration',
                 description: Optional[str] = 'The default configuration for iot-daemonize MQTT daemons',
                 epilog: Optional[str] = 'Have a lot of fun!'):
        super().__init__(program, description, epilog)
        self.add_config_arg('mqtt_host', default='localhost',
                            help='The hostname of the MQTT server. Default is localhost.',
                            flags=['-m', '--mqtt_host'])
        self.add_config_arg('mqtt_port', default=1883,
                            help='The port of the MQTT server. Default is 1883.',
                            flags=['--mqtt_port'])
        self.add_config_arg('mqtt_keepalive', default=30,
                            help='The keep alive interval for the MQTT server connection in seconds. Default is 30.',
                            flags=['--mqtt_keepalive'])
        self.add_config_arg('mqtt_user',
                            help='The username for the MQTT server connection.',
                            flags=['-u', '--mqtt_user'])
        self.add_config_arg('mqtt_password',
                            help='The password for the MQTT server connection.',
                            flags=['-p', '--mqtt_password'])
        self.add_config_arg('mqtt_tls', default=False, action='store_true',
                            help='Use SSL/TLS encryption for MQTT connection.',
                            flags=['--mqtt_tls'])
        self.add_config_arg('mqtt_tls_version', default='TLSv1.2',
                            help='The TLS version to use for MQTT. One of TLSv1, TLSv1.1, TLSv1.2. Default is TLSv1.2.',
                            flags=['--mqtt_tls_version'])
        self.add_config_arg('mqtt_verify_mode', default='CERT_REQUIRED',
                            help='The SSL certificate verification mode. One of CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED. Default is CERT_REQUIRED.',
                            flags=['--mqtt_verify_mode'])
        self.add_config_arg('mqtt_ssl_ca_path',
                            help='The SSL certificate authority file to verify the MQTT server.',
                            flags=['--mqtt_ssl_ca_path'])
        self.add_config_arg('mqtt_tls_no_verify', default=False, action='store_true',
                            help='Do not verify SSL/TLS constraints like hostname.',
                            flags=['--mqtt_tls_no_verify'])
        self.add_config_arg('timestamp', default=False, action='store_true',
                            help='Publish timestamps for all topics, e.g. for monitoring purposes.',
                            flags=['-t', '--timestamp'])
        self.add_config_arg('verbose', default=False, action='store_true',
                            help='Be verbose while running.',
                            flags=['-v', '--verbose'])
