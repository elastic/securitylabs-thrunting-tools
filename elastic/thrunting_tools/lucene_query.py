#!/usr/bin/env python3
"""CLI utility for querying Elasticsearch using Lucene syntax"""
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
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from appdirs import AppDirs
from rich import print_json
from scalpl import Cut

from elastic.thrunting_tools.common.elastic import connect_elasticsearch
from elastic.thrunting_tools.common.settings import ElasticsearchSettings
from elastic.thrunting_tools.common.utils import choose_config_entry, version_callback

logger = logging.getLogger(__name__)


app = typer.Typer(add_completion=False)
dirs = AppDirs(appname="thrunting-tools", appauthor="elastic")

DEFAULT_INDEX = "logs-*,metrics-*"


@app.command()
def lucene_query(
    query: str = typer.Argument(
        ...,
        help="Query specified using Lucene (See https://ela.st/lucene)",
        show_default=False,
    ),
    index: str = typer.Option(
        None,
        "--index",
        "-i",
        help=f"Index pattern to search. Defaults to '{DEFAULT_INDEX}'",
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
        False, "-c", "--compact", help="Output one event per line"
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
        envvar="CONFIG_PATH",
        show_envvar=False,
        help="Optional path to YAML configuration with settings for Elasticsearch",
    ),
    environment: Optional[str] = typer.Option(
        "default",
        "--environment",
        "-e",
        help="Environment name to use from config file (if present)",
    ),
    version: Optional[bool] = typer.Option(  # pylint: disable=unused-argument
        None, "--version", callback=version_callback, help="Show version info and exit"
    ),
):
    # pylint: disable=missing-function-docstring

    _cfg_dict: Dict[str, Any] = {"default_index": DEFAULT_INDEX}
    _local: Dict[str, Any] = choose_config_entry(config, "elasticsearch", environment)
    if _local:
        _cfg_dict |= _local

    _cfg = ElasticsearchSettings(**_cfg_dict)
    if index is None:
        index = _cfg.default_index

    logger.info("Creating es client")
    esclient = connect_elasticsearch(_cfg)
    _filter = {"range": {"@timestamp": {"gte": since, "lt": before}}}
    _query = {
        "bool": {
            "must": [
                {
                    "query_string": {
                        "query": query,
                        "analyze_wildcard": True,
                        "allow_leading_wildcard": True,
                    }
                }
            ],
            "filter": [_filter],
        }
    }

    field_view: List[str] = None
    if fields is not None:
        field_view = fields.split(",")

    _results = Cut(
        esclient.search(index=index, query=_query, fields=field_view, size=size)
    )

    logger.info("Found %s results", _results["hits.total.value"])

    indent: Optional[int] = None
    if not compact:
        indent = 4

    for item in _results["hits.hits"]:
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
