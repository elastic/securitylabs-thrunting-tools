"""Unit tests for settings objects"""
import os
from unittest import mock

from devtools import debug

from elastic.securitylabs.common.settings import ElasticsearchSettings


@mock.patch.dict(os.environ, {}, clear=True)
def test_es_settings():
    """Tests configuration via dict, which is what we do after loading YAML"""
    cfg_dict = {
        "name": "from_dict",
        "hosts": ["http://127.0.0.1:9092"],
        "username": "elastic",
        "password": "changeme",
    }

    cfg = ElasticsearchSettings(**cfg_dict)

    debug(cfg)

    assert cfg.name == "from_dict"
    assert cfg.hosts == ["http://127.0.0.1:9092"]
    assert cfg.username == "elastic"
    assert cfg.password == "changeme"

    assert (
        cfg.default_index == ".alerts-security.alerts-default,apm-*-transaction*,logs-*"
    )
    assert cfg.ssl_verify is True

    assert cfg.api_key is None
    assert cfg.cloud_auth is None
    assert cfg.cloud_id is None


ENV_SETTINGS = {
    "ES_HOSTS": "http://127.0.0.1:9092,http://127.0.0.2:9092",
    "ES_USER": "elastic",
    "ES_PASS": "changeme",
    "ES_INDEX": "logs-*",
}


@mock.patch.dict(os.environ, ENV_SETTINGS, clear=True)
def test_es_env_settings():
    """Test using a clean mock'd environment. This also validates the parsing of CSV for hosts"""
    debug(os.environ)
    cfg = ElasticsearchSettings()

    debug(cfg)
    assert cfg.hosts == ["http://127.0.0.1:9092", "http://127.0.0.2:9092"]
    assert cfg.username == "elastic"
    assert cfg.password == "changeme"
    assert cfg.default_index == "logs-*"
    assert cfg.ssl_verify is True

    assert cfg.name is None
    assert cfg.api_key is None
    assert cfg.cloud_auth is None
    assert cfg.cloud_id is None
