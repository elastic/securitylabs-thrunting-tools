"""Module to support pydantic settings classes"""
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
from logging import getLogger
from typing import Any, List, Optional

from pydantic import AnyHttpUrl, BaseSettings, root_validator

logger = getLogger(__name__)


class ElasticsearchSettings(BaseSettings):
    "Settings module for Elasticsearch"
    name: Optional[str]
    hosts: Optional[List[AnyHttpUrl]] = None
    cloud_id: Optional[str]
    cloud_auth: Optional[str]
    username: Optional[str]
    password: Optional[str]
    api_key: Optional[str]
    ssl_verify: bool = True
    default_index: str = ".alerts-security.alerts-default,apm-*-transaction*,logs-*"

    class Config:
        "Configures pydantic model"
        # Specify the environment variables
        fields = {
            "hosts": {"env": "ES_HOSTS"},
            "api_key": {"env": "ES_APIKEY"},
            "username": {"env": "ES_USER"},
            "password": {"env": "ES_PASS"},
            "ssl_verify": {"env": "ES_SSL_VERIFY"},
            "default_index": {"env": "ES_INDEX"},
        }

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            "Parses CSV entry for hosts"
            # pylint: disable=no-member
            if field_name == "hosts":
                return raw_val.split(",")
            return cls.json_loads(raw_val)

    @classmethod
    @root_validator
    def check_es_settings(cls, values):
        """
        Validates basic combinations of settings that would be
        non-deterministic if they existed
        """

        has_cloudauth = values.get("cloud_auth") is not None
        has_userpass = (
            values.get("username") is not None and values.get("password") is not None
        )
        has_apikey = values.get("api_key") is not None

        if has_cloudauth and has_userpass:
            logger.warning(
                "Using 'cloud_auth' when 'username/password' are also set for Elasticsearch'"
            )

        if (has_cloudauth or has_userpass) and has_apikey:
            raise ValueError(
                "Cannot use api_key when username/password or cloud_auth is used for Elasticsearch"
            )
