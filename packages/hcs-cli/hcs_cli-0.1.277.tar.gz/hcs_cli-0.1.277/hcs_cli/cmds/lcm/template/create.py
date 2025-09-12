"""
Copyright 2023-2023 VMware Inc.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import random
import sys

import click
import hcs_core.sglib.cli_options as cli
import hcs_core.util.duration as duration
from hcs_core.ctxp import recent

import hcs_cli.service.lcm as lcm
from hcs_cli.support import predefined_payload


@click.command()
@click.option(
    "--file",
    "-f",
    type=click.File("rt"),
    default=sys.stdin,
    help="Specify the template file name. If not specified, STDIN will be used.",
)
@cli.org_id
@click.option(
    "--predefined",
    "-p",
    required=False,
    help="Use a predefined template.",
)
@cli.wait
def create(file: str, org: str, predefined: str, wait: str, **kwargs):
    """Create a template"""

    org_id = cli.get_org_id(org)

    if predefined:
        payload = predefined_payload.load(f"lcm/{predefined}.json")
    else:
        with file:
            payload = file.read()

    try:
        template = json.loads(payload)
    except Exception as e:
        msg = "Invalid template: " + str(e)
        return msg, 1

    template_id = template.get("id")
    if not template_id:
        template_id = _rand_id(16)
        template["id"] = template_id

    template["orgId"] = org_id

    if template["providerType"] == "ZEROCLOUD":
        provider = _create_zerocloud_provider(org_id)
        template["provider"]["providerAccessId"] = provider["id"]

        if template["id"].find("$") > -1:
            template["id"] = "zero-" + _rand_id(3)

    ret = lcm.template.create(template)

    recent.require("template", ret["id"])
    if wait != "0":
        ret = lcm.template.wait(template_id, org_id, duration.to_seconds(wait))
    return ret


def _rand_id(n: int):
    return "".join(random.choices("abcdefghijkmnpqrstuvwxyz23456789", k=n))


def _create_zerocloud_provider(org_id: str):
    data = {"name": "nanw-test-" + _rand_id(4), "orgId": org_id, "type": "ZEROCLOUD"}

    return lcm.provider.create(data)
