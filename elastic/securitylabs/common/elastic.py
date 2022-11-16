"""Common functionality for elastic APIs"""
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
import logging
import os
from typing import Dict, List, Optional, Tuple

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


DEFAULT_CFG: Dict[str, Optional[str | bool]] = {
    "hosts": os.environ.get("ES_HOSTS", None),
    "cloud_id": os.environ.get("CLOUD_ID", None),
    "cloud_auth": os.environ.get("CLOUD_AUTH", None),
    "api_key": os.environ.get("ES_APIKEY", None),
    "username": os.environ.get("ES_USER", None),
    "password": os.environ.get("ES_PASS", None),
    "ssl_verify": os.environ.get("ES_SSL_VERIFY", True),
}


# pylint: disable=dangerous-default-value
def connect_elasticsearch(
    es_config: dict[str, Optional[str | bool]] = DEFAULT_CFG
) -> Elasticsearch:
    """Boilerplate to handle connecting to Elasticsearch given a configuration dict"""
    _es: Elasticsearch
    _apikey: Tuple[str, str] | None = None
    _httpauth: Tuple[str, str] | None = None

    if es_config.get("cloud_auth", None) is not None:
        _httpauth = tuple(es_config.get("cloud_auth").split(":"))  # type: ignore
    elif es_config.get("username", None) and es_config.get("password", None):
        _httpauth = (
            es_config.get("username"),  # type: ignore
            es_config.get("password"),
        )

    if es_config.get("api_key", None):
        _apikey = tuple(es_config.get("api_key").split(":"))  # type: ignore

    if _httpauth is not None and _apikey is not None:
        logger.critical(
            "Either username/password or api_key should be used for elasticsearch, not both."
        )
        raise ValueError

    _ssl_verify: bool = bool(es_config.get("ssl_verify", True))

    if es_config.get("cloud_id", None):
        logger.debug(
            "Connecting to Elasticsearch using cloud_id %s", es_config.get("cloud_id")
        )
        _cloud_id: str = str(es_config.get("cloud_id"))

        _es = Elasticsearch(
            cloud_id=_cloud_id,
            verify_certs=_ssl_verify,
            http_auth=_httpauth,
            api_key=_apikey,
            request_timeout=30,
            max_retries=10,
            retry_on_timeout=True,
        )
    else:
        logger.debug(
            "Connecting to Elasticsearch using hosts: %s",
            es_config.get("hosts", ["127.0.0.1:9200"]),
        )

        _hosts: str | List[str] = es_config.get("hosts", ["127.0.0.1:9200"])  # type: ignore
        if isinstance(_hosts, str):
            _hosts = _hosts.split(",")

        _es = Elasticsearch(
            hosts=_hosts,  # type: ignore
            verify_certs=_ssl_verify,
            http_auth=_httpauth,
            api_key=_apikey,
            request_timeout=30,
            max_retries=10,
            retry_on_timeout=True,
        )

    if _es.ping():
        logger.info("Successfully connected to Elasticsearch")
    else:
        raise RuntimeError("Something went wrong with connecting to Elasticsearch")

    return _es


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    connect_elasticsearch()
