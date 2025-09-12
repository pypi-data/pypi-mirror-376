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
import logging
from pathlib import Path

from axosyslog_light.driver_io.file.file_io import FileIO
from axosyslog_light.syslog_ng_config.statements.sources.source_driver import SourceDriver
from axosyslog_light.syslog_ng_ctl.legacy_stats_handler import LegacyStatsHandler
from axosyslog_light.syslog_ng_ctl.prometheus_stats_handler import PrometheusStatsHandler

logger = logging.getLogger(__name__)


class FileSource(SourceDriver):
    def __init__(
        self,
        stats_handler: LegacyStatsHandler,
        prometheus_stats_handler: PrometheusStatsHandler,
        file_name,
        **options,
    ) -> None:
        self.driver_name = "file"
        self.set_path(file_name)
        self.io = FileIO(self.get_path())
        super(FileSource, self).__init__(stats_handler, prometheus_stats_handler, [self.path], options)

    def get_path(self):
        return self.path

    def set_path(self, pathname):
        self.path = Path(pathname)

    def write_log(self, log, counter=1):
        for _ in range(counter):
            self.io.write_message(log)
        logger.info(
            "Content has been written to\nresource: {}\n"
            "number of times: {}\n"
            "content: {}\n".format(self.get_path(), counter, log),
        )

    def write_logs(self, logs, counter=1):
        for _ in range(counter):
            self.io.write_messages(logs)
        logger.info(
            "Content has been written to\nresource: {}\n"
            "number of times: {}\n"
            "content: {}\n".format(self.get_path(), counter, logs),
        )

    def close_file(self):
        self.io.close_writeable_file()
