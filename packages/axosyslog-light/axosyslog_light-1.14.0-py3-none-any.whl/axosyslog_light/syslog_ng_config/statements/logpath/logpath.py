#!/usr/bin/env python
#############################################################################
# Copyright (c) 2015-2018 Balabit
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
from axosyslog_light.syslog_ng_ctl.prometheus_stats_handler import MetricFilter
from axosyslog_light.syslog_ng_ctl.prometheus_stats_handler import PrometheusStatsHandler


class LogPath(object):
    def __init__(self, prometheus_stats_handler: PrometheusStatsHandler, name=None):
        self.__group_type = "log"
        self.__name = name
        self.__logpath = []
        self.__flags = []

        self.__metric_filters = []
        if name:
            self.__metric_filters += [
                MetricFilter("syslogng_route_ingress_total", {"id": name}),
                MetricFilter("syslogng_route_egress_total", {"id": name}),
            ]

        self.__prometheus_stats_handler = prometheus_stats_handler

    @property
    def group_type(self):
        return self.__group_type

    @property
    def name(self):
        return self.__name

    @property
    def logpath(self):
        return self.__logpath

    @property
    def flags(self):
        return self.__flags

    def add_group(self, group):
        self.logpath.append(group)

    def add_groups(self, groups):
        for group in groups:
            self.add_group(group)

    def add_flag(self, flag):
        self.flags.append(flag)

    def add_flags(self, flags):
        for flag in flags:
            self.add_flag(flag)

    def get_prometheus_stats(self):
        return self.__prometheus_stats_handler.get_samples(self.__metric_filters)
