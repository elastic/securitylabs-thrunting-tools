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
from typing import Tuple

from elasticsearch import Elasticsearch

from elastic.thrunting_tools.common.settings import ElasticsearchSettings

logger = logging.getLogger(__name__)


def connect_elasticsearch(settings: ElasticsearchSettings) -> Elasticsearch:
    """Boilerplate to handle connecting to Elasticsearch"""
    _es: Elasticsearch
    _apikey: Tuple[str, str] | None = None
    _httpauth: Tuple[str, str] | None = None

    if settings.cloud_auth is not None:
        _httpauth = tuple(settings.cloud_auth.split(":"))
    elif settings.username and settings.password:
        _httpauth = (
            settings.username,
            settings.password,
        )

    if settings.api_key:
        _apikey = tuple(settings.api_key.split(":"))

    if settings.cloud_id:
        logger.debug("Connecting to Elasticsearch using cloud_id %s", settings.cloud_id)

        _es = Elasticsearch(
            cloud_id=settings.cloud_id,
            verify_certs=settings.ssl_verify,
            http_auth=_httpauth,
            api_key=_apikey,
            request_timeout=30,
            max_retries=10,
            retry_on_timeout=True,
        )
    else:
        logger.debug("Connecting to Elasticsearch using hosts: %s", settings.hosts)

        _es = Elasticsearch(
            hosts=settings.hosts,
            verify_certs=settings.ssl_verify,
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
    connect_elasticsearch(ElasticsearchSettings())
