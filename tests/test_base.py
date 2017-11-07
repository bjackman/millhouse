# SPDX-License-Identifier: Apache-2.0
#
# Copyright (C) 2017, ARM Limited and contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

from trappy import FTrace

class MillhouseTestBase(TestCase):
    def setUp(self):
        self.test_dir = mkdtemp()

    def tearDown(self):
        rmtree(self.test_dir)

    def make_ftrace(self, in_data):
        filename = 'trace_{}.txt'.format(self.id())
        path = os.path.join(self.test_dir, filename)
        with open(path, 'w') as f:
            f.write(in_data)

        return FTrace(path, scope='custom',
                      events=['cpu_idle', 'cpu_frequency', 'cpu_frequency_devlib',
                              'thermal_temperature'],
                      normalize_time=False)

