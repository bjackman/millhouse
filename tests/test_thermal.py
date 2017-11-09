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

from millhouse.trace_analyzer import TraceAnalyzer

from test_base import MillhouseTestBase

TEST_DATA="""
kworker/5:1-28858 [005]  100.000000: thermal_temperature:  thermal_zone=cls0 id=0 temp_prev=10000 temp=20000
kworker/5:1-28858 [005]  200.000000: thermal_temperature:  thermal_zone=cls0 id=0 temp_prev=20000 temp=30000
kworker/5:1-28858 [005]  300.000000: thermal_temperature:  thermal_zone=cls0 id=0 temp_prev=30000 temp=10000
"""

class TestThermal(MillhouseTestBase):
    def test_temp_signal(self):
        ftrace = self.make_ftrace(TEST_DATA)

        analyzer = TraceAnalyzer(ftrace)
        df = analyzer.thermal.signal.temperature()

        self.assertEqual(df['cls0'].tolist(),
                         [20000, 30000, 10000])


    def test_avg_temp(self):
        ftrace = self.make_ftrace(TEST_DATA)

        analyzer = TraceAnalyzer(ftrace)

        exp_avg = (
            (100 * 20000) + (100 * 10000. / 2) +
            (100 * 10000) + (100 * 20000. / 2)) / 200

        df = analyzer.thermal.stats.avg_temperature()

        self.assertEqual(df['avg_temperature']['cls0'], exp_avg)
