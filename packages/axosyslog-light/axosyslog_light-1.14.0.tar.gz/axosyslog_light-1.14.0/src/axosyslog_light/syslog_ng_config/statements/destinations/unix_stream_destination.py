#!/usr/bin/env python
#############################################################################
# Copyright (c) 2022 One Identity
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

from axosyslog_light.common.asynchronous import BackgroundEventLoop
from axosyslog_light.common.blocking import DEFAULT_TIMEOUT
from axosyslog_light.common.network import SingleConnectionUnixStreamServer
from axosyslog_light.driver_io import message_readers
from axosyslog_light.syslog_ng_config.statements.destinations.destination_driver import DestinationDriver
from axosyslog_light.syslog_ng_ctl.legacy_stats_handler import LegacyStatsHandler
from axosyslog_light.syslog_ng_ctl.prometheus_stats_handler import PrometheusStatsHandler


class UnixStreamDestination(DestinationDriver):
    def __init__(
        self,
        stats_handler: LegacyStatsHandler,
        prometheus_stats_handler: PrometheusStatsHandler,
        file_name: str,
        **options,
    ) -> None:
        self.driver_name = "unix-stream"
        self.path = Path(file_name)

        self.__server = None
        self.__message_reader = None

        super(UnixStreamDestination, self).__init__(stats_handler, prometheus_stats_handler, [self.path], options)

    def start_listener(self):
        self.__server = SingleConnectionUnixStreamServer(self.path)
        self.__message_reader = message_readers.SingleLineStreamReader(self.__server)
        BackgroundEventLoop().wait_async_result(self.__server.start(), timeout=DEFAULT_TIMEOUT)

    def stop_listener(self):
        if self.__message_reader is not None:
            BackgroundEventLoop().wait_async_result(self.__server.stop(), timeout=DEFAULT_TIMEOUT)
            self.__message_reader = None
            self.__server = None

    def read_log(self, timeout=DEFAULT_TIMEOUT):
        return self.read_logs(1, timeout)[0]

    def read_logs(self, counter, timeout=DEFAULT_TIMEOUT):
        return self.__message_reader.wait_for_number_of_messages(counter, timeout)

    def read_until_logs(self, logs, timeout=DEFAULT_TIMEOUT):
        return self.__message_reader.wait_for_messages(logs, timeout)
