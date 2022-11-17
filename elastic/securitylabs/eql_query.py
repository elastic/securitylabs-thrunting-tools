#!/usr/bin/env python3
"""CLI utility for querying Elasticsearch using EQL syntax"""
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

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from appdirs import AppDirs
from rich import print_json
from scalpl import Cut

from elastic.securitylabs.common.elastic import connect_elasticsearch
from elastic.securitylabs.common.utils import choose_config

logger = logging.getLogger(__name__)


app = typer.Typer(add_completion=False)
dirs = AppDirs(appname="securitylabs-tools", appauthor="elastic")


DEFAULT_CFG: Dict[str, Optional[str | bool]] = {
    "hosts": os.environ.get("ES_HOSTS", None),
    "cloud_id": os.environ.get("CLOUD_ID", None),
    "cloud_auth": os.environ.get("CLOUD_AUTH", None),
    "api_key": os.environ.get("ES_APIKEY", None),
    "username": os.environ.get("ES_USER", None),
    "password": os.environ.get("ES_PASS", None),
    "ssl_verify": os.environ.get("ES_SSL_VERIFY", True),
}

DEFAULT_INDEX = os.environ.get(
    "ES_INDEX", ".alerts-security.alerts-default,apm-*-transaction*,logs-*"
)


@app.command()
def eql_query(
    query: str = typer.Argument(
        ...,
        help="Query specified using EQL (See https://ela.st/eql)",
        show_default=False,
    ),
    since: Optional[str] = typer.Option(
        "now-30d/d",
        "--since",
        "-s",
        help="Earliest time filter using datemath or datetime",
    ),
    before: Optional[str] = typer.Option(
        "now", "-b", "--before", help="Latest time filter using datemath or datetime"
    ),
    compact: Optional[bool] = typer.Option(
        False, "-c", "--compact", help="Output one event/sequence per line"
    ),
    fields: Optional[str] = typer.Option(
        None, "-f", "--fields", help="Comma separated list of fields to display"
    ),
    size: Optional[int] = typer.Option(
        100, "-s", "--size", help="Specify maximum size of result set"
    ),
    config: Optional[Path] = typer.Option(
        f"{dirs.user_config_dir}/config.yml",
        "--config",
        help="Optional path to YAML configuration with settings for Elasticsearch",
    ),
    environment: Optional[str] = typer.Option(
        "default",
        "--environment",
        "-e",
        help="Environment name to use from config file (if present)",
    ),
) -> None:
    # pylint: disable=missing-function-docstring

    _cfg: Dict[str, Any] = DEFAULT_CFG
    _local: Dict[str, Any] = choose_config(config, "elasticsearch", environment)
    if _local:
        _cfg = _local

    logger.info("Creating es client")
    esclient = connect_elasticsearch(_cfg)
    _filter = {"range": {"@timestamp": {"gte": since, "lt": before}}}

    field_view: List[str] = []
    if fields is not None:
        field_view = fields.split(",")

    _results = Cut(
        esclient.eql.search(
            index=DEFAULT_INDEX,
            query=query,
            filter=_filter,
            fields=field_view,
            size=size,
        )
    )

    logger.info("Found %s results", _results["hits.total.value"])

    indent: Optional[int] = None
    if not compact:
        indent = 4

    for item in _results["hits.events"]:
        _view: Cut = Cut({})
        item = Cut(item)

        if field_view is not None and len(field_view) > 0:
            for _field in field_view:
                if item.get(f"_source.{_field}", None) is not None:
                    _view.setdefault(_field, item[f"_source.{_field}"])
        else:
            _view = item

        _json = json.dumps(dict(_view)).strip()
        print_json(_json, indent=indent, sort_keys=True)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, format="%(message)s", level=logging.DEBUG)
    app()
