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
from test_base import MillhouseTestBase

from millhouse.trace_analyzer import TraceAnalyzer
TEST_TRACE_DATA = """
          <idle>-0     [000]   100.000000: cpu_idle:             state=4294967295 cpu_id=0
          <idle>-0     [001]   101.000000: cpu_idle:             state=4294967295 cpu_id=1
          <idle>-0     [002]   102.000000: cpu_idle:             state=4294967295 cpu_id=2
          <idle>-0     [003]   103.000000: cpu_idle:             state=4294967295 cpu_id=3
          <idle>-0     [004]   104.000000: cpu_idle:             state=4294967295 cpu_id=4
          <idle>-0     [004]   519.000000: cpu_frequency:             state=100000 cpu_id=0
          <idle>-0     [004]   519.000000: cpu_frequency:             state=100000 cpu_id=1
          <idle>-0     [001]   519.000000: cpu_frequency:             state=100000 cpu_id=2
          <idle>-0     [002]   519.000000: cpu_frequency:             state=100000 cpu_id=3
          <idle>-0     [001]   559.000000: cpu_frequency:             state=200000 cpu_id=0
          <idle>-0     [002]   559.000000: cpu_frequency:             state=200000 cpu_id=1
          <idle>-0     [003]   559.000000: cpu_frequency:             state=200000 cpu_id=2
          <idle>-0     [003]   559.000000: cpu_frequency:             state=200000 cpu_id=3
          <idle>-0     [000]   600.000000: cpu_idle:             state=0 cpu_id=0
          <idle>-0     [001]   601.000000: cpu_idle:             state=0 cpu_id=1
          <idle>-0     [002]   602.000000: cpu_idle:             state=0 cpu_id=2
          <idle>-0     [003]   603.000000: cpu_idle:             state=0 cpu_id=3
          <idle>-0     [004]   604.000000: cpu_idle:             state=0 cpu_id=4
          <idle>-0     [001]   719.000000: cpu_frequency:             state=300000 cpu_id=0
          <idle>-0     [002]   719.000000: cpu_frequency:             state=300000 cpu_id=1
          <idle>-0     [003]   719.000000: cpu_frequency:             state=300000 cpu_id=2
          <idle>-0     [003]   719.000000: cpu_frequency:             state=300000 cpu_id=3
          <idle>-0     [000]   800.000000: cpu_idle:             state=4294967295 cpu_id=0
          <idle>-0     [001]   801.000000: cpu_idle:             state=4294967295 cpu_id=1
          <idle>-0     [002]   802.000000: cpu_idle:             state=4294967295 cpu_id=2
          <idle>-0     [003]   803.000000: cpu_idle:             state=4294967295 cpu_id=3
          <idle>-0     [004]   804.000000: cpu_idle:             state=4294967295 cpu_id=4
          <idle>-0     [001]   919.000000: cpu_frequency:             state=400000 cpu_id=0
          <idle>-0     [002]   919.000000: cpu_frequency:             state=400000 cpu_id=1
          <idle>-0     [003]   919.000000: cpu_frequency:             state=400000 cpu_id=2
          <idle>-0     [003]   919.000000: cpu_frequency:             state=400000 cpu_id=3
"""
class TestFrequency(MillhouseTestBase):
    def test_cpu_frequency_signal(self):
        ftrace = self.make_ftrace(TEST_TRACE_DATA)
        analyzer = TraceAnalyzer(ftrace)
        df = analyzer.frequency.signal.cpu_frequency()
        self.assertEqual(df.columns.tolist(), analyzer.cpus)

    # TODO test devlib events
    #           cluster coherency check

    def test_freq_residency(self):
        ftrace = self.make_ftrace(TEST_TRACE_DATA)
        analyzer = TraceAnalyzer(ftrace)

        df = analyzer.frequency.stats.frequency_residency()
        print df
        # TODO test actual values
