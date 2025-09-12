from cacholong_sdk.connection import connection as Conn
import os
import configparser
from xdg import BaseDirectory


class Connection(Conn):
    def __init__(self, headers={}):
        # Read the user.ini file
        configpath = BaseDirectory.save_config_path("cacholong-cli")
        self.cfg = configparser.ConfigParser()
        self.cfg.read(os.path.join(configpath, "config.ini"))

        api_url = self.cfg["DEFAULT"]["api_url"].strip("'")
        api_key = self.cfg["DEFAULT"]["api_key"].strip("'")

        # Call parent constructor
        super().__init__(api_url, api_key, headers)
