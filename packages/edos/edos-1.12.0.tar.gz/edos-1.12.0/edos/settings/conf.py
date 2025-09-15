import configparser
import logging
import os

import yaml
from appdirs import AppDirs

from ..exceptions import UserReadableException


class LocalConfig(dict):
    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            raise UserReadableException(
                "Error: DO setup tool is not configured. Run {} first.".format("edos-configure")
            )


def _read_config(config_path):
    conf = configparser.ConfigParser()
    conf.read(config_path)
    conf = LocalConfig((s, dict(conf.items(s))) for s in conf.sections())
    return conf


class Config:
    LOG = logging.getLogger(__name__)

    def __init__(self):
        self.reload()

    def reload(self):
        if os.environ.get("TEST_MODE", False) == "true":
            self.config = {
                "DO": {"token": "test_token"},
                "AWS": {"aws_access_key": "test_key", "aws_secret_key": "test_secret"},
                "SWARMPIT": {"token": "test_token"},
                "INVOICE": {
                    "fakturoid_api_key": "test_key",
                    "clockify_api_key": "test_key",
                    "fakturoid_account_email": "test_account",
                    "fakturoid_account_slug": "test_slug",
                },
                                "SSH": {"user": "administrator", "hostname": "swarm1"},
            }
        else:
            self.config = _read_config(self.CONFIG_PATH) if os.path.exists(self.CONFIG_PATH) else LocalConfig()

        self.DIGITAL_OCEAN_CONFIG = self.config["DO"] if "DO" in self.config else {}
        self.AWS_CONFIG = self.config["AWS"] if "AWS" in self.config else {}
        self.SWARMPIT_CONFIG = self.config["SWARMPIT"] if "SWARMPIT" in self.config else {}
        self.INVOICE_CONFIG = self.config["INVOICE"] if "INVOICE" in self.config else {}
        self.SSH_CONFIG = self.config["SSH"] if "SSH" in self.config else {}

    # Interactive mode
    INTERACTIVE = bool(yaml.full_load(os.getenv("INTERACTIVE", "True")))

    USER_DIR = AppDirs("Endevel", "edos")
    CONFIG_PATH = os.path.join(USER_DIR.user_config_dir, "config.ini")

    AWS_ENDPOINT_URL = "https://fra1.digitaloceanspaces.com"
    AWS_REGION = "fra1"

    DOCKER_MAIN_SWARM_HOSTNAME = "swarm1"

    CLOCKIFY_ENDEVEL_WORKSPACE_ID = "5d19eacd1080ec307ed7ae12"
    CLOCKIFY_API_URL = "api.clockify.me/v1"
    FAKTUROID_USER_AGENT = "EDOS (stepan.binko@endevel.cz)"
    ENDEVEL_ICO = "11769327"

    PSQL_CLUSTER_ID = "c26441b7-d10a-453e-a367-ea2cdc27ea07"
    PSQL_DEV_CLUSTER_ID = "92ae8f86-bf35-4129-979a-de0889f7f5d4"
    MYSQL_CLUSTER_ID = "5ab58201-4008-4faf-bc38-f983633adef9"

    @property
    def SSH_USER(self):
        return self.SSH_CONFIG.get("user", "administrator")

    @property
    def SSH_HOSTNAME(self):
        return self.SSH_CONFIG.get("hostname", "swarm1")

    @property
    def SSH_CONNECTION(self):
        return f"{self.SSH_USER}@{self.SSH_HOSTNAME}"

    @property
    def DOCKER_SSH_BASE_URL(self):
        return f"ssh://{self.SSH_CONNECTION}"
