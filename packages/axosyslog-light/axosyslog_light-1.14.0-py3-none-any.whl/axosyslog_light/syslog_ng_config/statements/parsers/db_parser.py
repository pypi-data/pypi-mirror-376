#!/usr/bin/env python
#############################################################################
# Copyright (c) 2015-2019 Balabit
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# As an additional exemption you are allowed to compile & link against the
# OpenSSL libraries as published by the OpenSSL project. See the file
# COPYING for details.
#
#############################################################################
from pathlib import Path
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import tostring

from axosyslog_light.syslog_ng_config.statements.parsers.parser import Parser
from axosyslog_light.syslog_ng_ctl.legacy_stats_handler import LegacyStatsHandler
from axosyslog_light.syslog_ng_ctl.prometheus_stats_handler import PrometheusStatsHandler


class DBParserConfig(object):
    def __init__(self, ruleset_pattern, rules):
        self.ruleset_pattern = ruleset_pattern
        self.rules = rules

    def write_to(self, file_name):
        with file_name.open("wb") as f:
            node_patterndb = Element("patterndb", version="5")
            node_ruleset = SubElement(node_patterndb, "ruleset", name="some_name", id="1234")
            node_ruleset_pattern = SubElement(node_ruleset, "pattern")
            node_ruleset_pattern.text = self.ruleset_pattern
            node_rules = SubElement(node_ruleset, "rules")

            rule_id = 0
            for rule in self.rules:
                node_rule = SubElement(node_rules, "rule", id=str(rule_id))
                node_rule.set("class", rule["class"])
                rule_id += 1
                node_patterns = SubElement(node_rule, "patterns")
                node_pattern = SubElement(node_patterns, "pattern")
                node_pattern.text = rule["rule"]

            f.write(tostring(node_patterndb))


class DBParser(Parser):
    index = 0

    def __init__(
        self,
        stats_handler: LegacyStatsHandler,
        prometheus_stats_handler: PrometheusStatsHandler,
        config: DBParserConfig,
        **options,
    ) -> None:
        path = Path("patterndb-{}.xml".format(self.index))
        config.write_to(path)
        self.index += 1
        super(DBParser, self).__init__(
            "db-parser",
            stats_handler=stats_handler,
            prometheus_stats_handler=prometheus_stats_handler,
            file=path.resolve(),
            **options,
        )
