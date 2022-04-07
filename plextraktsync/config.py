import json
from dataclasses import dataclass
from json import JSONDecodeError
from os import getenv
from os.path import exists

from dotenv import load_dotenv

from plextraktsync.path import (cache_dir, config_file, config_yml,
                                default_config_file, env_file)

"""
Platform name to identify our application
"""
PLEX_PLATFORM = "PlexTraktSync"

"""
Constant in seconds for how much to wait between Trakt POST API calls.
"""
TRAKT_POST_DELAY = 1.1


@dataclass
class RunConfig:
    """
    Class to hold runtime config parameters
    """

    dry_run: bool = False
    batch_delay: int = 5
    progressbar: bool = True

    def update(self, **kwargs):
        for name, value in kwargs.items():
            self.__setattr__(name, value)

        return self


class ConfigLoader:
    @staticmethod
    def load(path: str):
        if path.endswith('.yml'):
            return ConfigLoader.load_yaml(path)
        if path.endswith('.json'):
            return ConfigLoader.load_json(path)
        raise RuntimeError(f'Unknown file type: {path}')

    @staticmethod
    def load_json(path: str):
        with open(path, "r", encoding="utf-8") as fp:
            try:
                config = json.load(fp)
            except JSONDecodeError as e:
                raise RuntimeError(f"Unable to parse {path}: {e}")
        return config

    @staticmethod
    def load_yaml(path: str):
        import yaml

        with open(path, "r", encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
        return config

    @staticmethod
    def write_json(path: str, config):
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(json.dumps(config, indent=4))

    @staticmethod
    def write_yaml(path: str, config):
        import yaml

        with open(path, "w", encoding="utf-8") as fp:
            yaml.dump(config, fp)


class Config(dict):
    env_keys = [
        "PLEX_BASEURL",
        "PLEX_FALLBACKURL",  # legacy, used before 0.18.21
        "PLEX_LOCALURL",
        "PLEX_TOKEN",
        "PLEX_USERNAME",
        "TRAKT_USERNAME",
    ]

    initialized = False
    config_file = config_file
    config_yml = config_yml
    env_file = env_file

    def __getitem__(self, item):
        if not self.initialized:
            self.initialize()
        return dict.__getitem__(self, item)

    def __contains__(self, item):
        if not self.initialized:
            self.initialize()
        return dict.__contains__(self, item)

    def initialize(self):
        """
        Config load order:
        - load config.defaults.yml
        - if config.yml present, load and merge it
        """
        self.initialized = True

        loader = ConfigLoader()
        defaults = loader.load(default_config_file)
        self.update(defaults)

        if not exists(self.config_file):
            loader.write_json(self.config_file, defaults)

        config = loader.load_json(self.config_file)
        self.merge(config, self)
        override = self["config"]["dotenv_override"]

        load_dotenv(self.env_file, override=override)
        for key in self.env_keys:
            value = getenv(key)
            if value == "-" or value == "None" or value == "":
                value = None
            self[key] = value

        if self["PLEX_LOCALURL"] is None:  # old .env file used before 0.18.21
            self["PLEX_LOCALURL"] = self["PLEX_FALLBACKURL"]
            self["PLEX_FALLBACKURL"] = None

        self["cache"]["path"] = self["cache"]["path"].replace(
            "$PTS_CACHE_DIR", cache_dir
        )

    # https://stackoverflow.com/a/20666342/2314626
    def merge(self, source, destination):
        for key, value in source.items():
            if isinstance(value, dict):
                # get node or create one
                node = destination.setdefault(key, {})
                self.merge(value, node)
            else:
                destination[key] = value

        return destination

    def save(self):
        with open(self.env_file, "w") as txt:
            txt.write("# This is .env file for PlexTraktSync\n")
            for key in self.env_keys:
                if key in self and self[key] is not None:
                    txt.write("{}={}\n".format(key, self[key]))
                else:
                    txt.write("{}=\n".format(key))


CONFIG = Config()
