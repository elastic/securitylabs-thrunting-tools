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
from typing import Dict, List, Optional

import typer
from rich import print_json
from scalpl import Cut

from elastic.securitylabs.common.elastic import connect_elasticsearch

logger = logging.getLogger(__name__)


app = typer.Typer()

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
def eqlquery(
    query: str,
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
):
    """eqlquery command main body

    Args:
        query (str): Query specified using EQL (See https://ela.st/eql)
        since (Optional[str], optional): Start of event timestamp. Defaults to "now-30d/d"
        before (Optional[str], optional): End of event timestamp. Defaults to "now"
        compact (Optional[bool], optional): If True, generate one event per line. Defaults to False
        fields (Optional[str], optional): Specify list of fields to retrieve. Defaults to all fields
        size (Optional[int], optional): Maximum event count. Defaults to 100
    """
    logger.info("Creating es client")
    esclient = connect_elasticsearch(DEFAULT_CFG)
    _filter = {"range": {"@timestamp": {"gte": since, "lt": before}}}

    _results = Cut(
        esclient.eql.search(index=DEFAULT_INDEX, query=query, filter=_filter, size=size)
    )

    logger.info("Found %s results", _results["hits.total.value"])

    field_view: List[str] = []
    if fields is not None:
        field_view = fields.split(",")

    indent: Optional[int] = None
    if not compact:
        indent = 4

    for item in _results["hits.events"]:
        _view: Cut = Cut({})
        item = Cut(item)

        if len(field_view) > 0:
            for _field in field_view:
                if item.get(f"_source.{_field}", None) is not None:
                    _view.setdefault(_field, item[f"_source.{_field}"])
        else:
            _view = item

        _json = json.dumps(dict(_view)).strip()
        print_json(_json, indent=indent, sort_keys=True)


def run():
    """Entrypoint for typer app used by installed script"""
    app()


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, format="%(message)s", level=logging.DEBUG)
    run()
