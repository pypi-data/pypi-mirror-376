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
# flake8: noqa: F401, F811
from pathlib import PosixPath

import pytest
from axosyslog_light.self_test_fixtures import fake_testcase_parameters
from axosyslog_light.syslog_ng.syslog_ng_paths import SyslogNgPaths


def test_syslog_ng_paths(fake_testcase_parameters):
    syslog_ng_paths = SyslogNgPaths(fake_testcase_parameters)
    syslog_ng_paths.set_syslog_ng_paths(instance_name="server")
    assert set(list(syslog_ng_paths._SyslogNgPaths__syslog_ng_paths)) == {"dirs", "file_paths", "binary_file_paths"}
    assert set(list(syslog_ng_paths._SyslogNgPaths__syslog_ng_paths["dirs"])) == {"install_dir"}
    assert set(list(syslog_ng_paths._SyslogNgPaths__syslog_ng_paths["file_paths"])) == {
        "config_path",
        "persist_path",
        "pid_path",
        "control_socket_path",
        "stderr",
        "stdout",
        "syntax_only_stderr",
        "syntax_only_stdout",
    }
    assert set(list(syslog_ng_paths._SyslogNgPaths__syslog_ng_paths["binary_file_paths"])) == {
        "syslog_ng_binary",
        "syslog_ng_ctl",
        "loggen",
        "slogkey",
        "slogverify",
    }


def test_syslog_ng_paths_parent_class_of_paths(fake_testcase_parameters):
    syslog_ng_paths = SyslogNgPaths(fake_testcase_parameters)
    syslog_ng_paths.set_syslog_ng_paths(instance_name="server")
    for __key, value in syslog_ng_paths._SyslogNgPaths__syslog_ng_paths["file_paths"].items():
        assert isinstance(value, PosixPath) is True

    for __key, value in syslog_ng_paths._SyslogNgPaths__syslog_ng_paths["dirs"].items():
        assert isinstance(value, PosixPath) is True

    for __key, value in syslog_ng_paths._SyslogNgPaths__syslog_ng_paths["binary_file_paths"].items():
        assert isinstance(value, PosixPath) is True


def test_syslog_ng_paths_client_relay_server(fake_testcase_parameters):
    syslog_ng_paths_server = SyslogNgPaths(
        fake_testcase_parameters,
    ).set_syslog_ng_paths(instance_name="server")
    syslog_ng_paths_relay = SyslogNgPaths(
        fake_testcase_parameters,
    ).set_syslog_ng_paths(instance_name="relay")
    syslog_ng_paths_client = SyslogNgPaths(
        fake_testcase_parameters,
    ).set_syslog_ng_paths(instance_name="client")

    assert syslog_ng_paths_client.get_instance_name() == "client"
    assert syslog_ng_paths_relay.get_instance_name() == "relay"
    assert syslog_ng_paths_server.get_instance_name() == "server"


def test_instance_already_configured(fake_testcase_parameters):
    syslog_ng_paths_server = SyslogNgPaths(
        fake_testcase_parameters,
    ).set_syslog_ng_paths(instance_name="server")
    with pytest.raises(Exception):
        syslog_ng_paths_server.set_syslog_ng_paths(instance_name="client")
