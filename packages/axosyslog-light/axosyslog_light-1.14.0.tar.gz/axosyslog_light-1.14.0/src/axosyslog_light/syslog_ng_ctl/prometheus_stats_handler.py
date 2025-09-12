#!/usr/bin/env python
#############################################################################
# Copyright (c) 2023 Attila Szakacs
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
import typing

import prometheus_client.parser
from axosyslog_light.syslog_ng_ctl.syslog_ng_ctl import SyslogNgCtl
from prometheus_client.samples import Sample

__all__ = ["PrometheusStatsHandler", "MetricFilter", "Sample"]


class MetricFilter(typing.NamedTuple):
    name: str
    labels: typing.Optional[typing.Dict[str, str]] = None


class PrometheusStatsHandler(object):
    def __init__(self, syslog_ng_ctl: SyslogNgCtl) -> None:
        self.__syslog_ng_ctl = syslog_ng_ctl

    def __filter_raw_samples(self, metric_filters: typing.List[MetricFilter], raw_samples: str) -> typing.List[Sample]:
        samples = []

        for metric_family in prometheus_client.parser.text_string_to_metric_families(raw_samples):
            for sample in metric_family.samples:
                for metric_filter in metric_filters:
                    if metric_filter.name == sample.name and metric_filter.labels.items() <= sample.labels.items():
                        samples.append(sample)

        return samples

    def get_samples(self, metric_filters: typing.List[MetricFilter]) -> typing.List[Sample]:
        if len(metric_filters) == 0:
            return []

        ctl_output = self.__syslog_ng_ctl.stats_prometheus()
        if ctl_output["exit_code"] != 0:
            return []

        return self.__filter_raw_samples(metric_filters, ctl_output["stdout"])
