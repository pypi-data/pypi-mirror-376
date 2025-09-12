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

import psutil
from axosyslog_light.executors.command_executor import prepare_executable_command
from axosyslog_light.executors.command_executor import prepare_printable_command
from axosyslog_light.executors.command_executor import prepare_std_outputs

logger = logging.getLogger(__name__)


class ProcessExecutor(object):
    def __init__(self):
        self.process = None

    def start(self, command, stdout_path, stderr_path):
        printable_command = prepare_printable_command(command)
        executable_command = prepare_executable_command(command)
        stdout, stderr = prepare_std_outputs(stdout_path, stderr_path)
        env = psutil.Process().environ()
        if "VIRTUAL_ENV" in env:
            del env["VIRTUAL_ENV"]
        logger.info("Following process will be started:\n{}\n".format(printable_command))
        try:
            self.process = psutil.Popen(
                executable_command, stdout=stdout.open(mode="a"), stderr=stderr.open(mode="a"), env=env,
            )
        except (OSError, psutil.Error) as e:
            logger.error("Failed to start process: {}\nError: {}".format(printable_command, e))
            stdout.close()
            stderr.close()
        return self.process
