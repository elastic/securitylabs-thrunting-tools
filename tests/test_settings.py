"""Unit tests for settings objects"""
# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
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
