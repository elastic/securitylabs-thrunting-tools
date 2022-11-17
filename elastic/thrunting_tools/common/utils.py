"""Functionality common to this package's modules"""
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

from importlib.metadata import version
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, List

import typer
from ruamel.yaml import YAML

logger = getLogger(__name__)


def choose_config_entry(config: Path, group: str, name: str = None) -> Dict[str, Any]:
    """
    filters entries in a YAML configuration file for a given group (top-level key)
    and a given name
    """
    _config = []
    if config is not None and config.exists():
        logger.info("Reading configuration from %s", config)
        yaml = YAML()
        _config: List[Dict[str, Any]] = yaml.load(config.read_text())

        _config = list(
            filter(lambda entry: entry.get("name") == name, _config.get(group, []))
        )
        if len(_config) == 0:
            logger.error(
                "Failed to find environment for group '%s' for name '%s' in file '%s'",
                group,
                name,
                config,
            )
            raise typer.Exit(code=-1)

    if len(_config) > 0:
        # If we have at least one match, return the first
        return _config[0]
    else:
        return {}


def version_callback(value: bool):
    if value:
        _version = version("thrunting-tools")
        print(f"Elastic Security Labs Thrunting Tools, {_version}")
        print("https://github.com/elastic/securitylabs-thruntingtools")
        raise typer.Exit()
