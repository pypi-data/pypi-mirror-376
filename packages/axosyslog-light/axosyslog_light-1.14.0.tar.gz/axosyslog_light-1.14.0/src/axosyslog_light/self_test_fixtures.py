#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import pytest
from axosyslog_light.testcase_parameters.testcase_parameters import TestcaseParameters


@pytest.fixture
def test_message():
    return "test message - öüóőúéáű"


@pytest.fixture
def fake_testcase_parameters(request, tmpdir):
    request.config.option.installdir = tmpdir.join("installdir")
    request.config.option.reports = tmpdir.join("reports")
    request.config.option.run_under = ""

    yield TestcaseParameters(request)


@pytest.fixture
def temp_file(tmpdir):
    return tmpdir.join("test_file.log")
