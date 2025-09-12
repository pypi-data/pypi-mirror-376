#!/usr/bin/env python
# -*- coding: utf-8 -*-
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


class BSDFormat(object):
    @staticmethod
    def format_message(message):
        formatted_message = ""
        if message.priority_value:
            formatted_message += "<{}>".format(message.priority_value)
        if message.bsd_timestamp_value:
            formatted_message += "{}".format(message.bsd_timestamp_value)
        if message.hostname_value:
            formatted_message += " {}".format(message.hostname_value)
        if message.program_value:
            formatted_message += " {}".format(message.program_value)
        if message.pid_value:
            formatted_message += "[{}]:".format(message.pid_value)
        if message.message_value:
            formatted_message += " {}".format(message.message_value)
        return formatted_message
