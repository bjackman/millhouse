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

class TestThermal(MillhouseTestBase):
    def test_temp_signal(self):
        ftrace = self.make_ftrace("""
        kworker/5:1-28858 [005]  4427.940375: thermal_temperature:  thermal_zone=cls0 id=0 temp_prev=54578 temp=53759
kworker/5:1-28858 [005]  4428.940596: thermal_temperature:  thermal_zone=cls0 id=0 temp_prev=53759 temp=57648
     kworker/5:1-28858 [005]  4429.940507: thermal_temperature:  thermal_zone=cls0 id=0 temp_prev=57648 temp=58877
        """)


        analyzer = TraceAnalyzer(ftrace)
        df = analyzer.thermal.signal.temperature()

        self.assertEqual(df['cls0'].tolist(),
                         [53759, 57648, 58877])

