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
          <idle>-0     [001]   100.000000: cpu_idle:             state=4294967295 cpu_id=1
          <idle>-0     [002]   100.000000: cpu_idle:             state=4294967295 cpu_id=2
          <idle>-0     [003]   100.000000: cpu_idle:             state=4294967295 cpu_id=3
          <idle>-0     [003]   500.000000: cpu_frequency_devlib:      state=100000 cpu_id=0
          <idle>-0     [003]   500.000000: cpu_frequency_devlib:      state=100000 cpu_id=1
          <idle>-0     [001]   500.000000: cpu_frequency_devlib:      state=100000 cpu_id=2
          <idle>-0     [002]   500.000000: cpu_frequency_devlib:      state=100000 cpu_id=3
          <idle>-0     [001]   550.000000: cpu_frequency:             state=200000 cpu_id=0
          <idle>-0     [002]   550.000000: cpu_frequency:             state=200000 cpu_id=1
          <idle>-0     [003]   550.000000: cpu_frequency:             state=200000 cpu_id=2
          <idle>-0     [003]   550.000000: cpu_frequency:             state=200000 cpu_id=3
          <idle>-0     [000]   600.000000: cpu_idle:             state=0 cpu_id=0
          <idle>-0     [001]   600.000000: cpu_idle:             state=0 cpu_id=1
          <idle>-0     [002]   600.000000: cpu_idle:             state=0 cpu_id=2
          <idle>-0     [003]   600.000000: cpu_idle:             state=0 cpu_id=3
          <idle>-0     [001]   700.000000: cpu_frequency:             state=300000 cpu_id=0
          <idle>-0     [002]   700.000000: cpu_frequency:             state=300000 cpu_id=1
          <idle>-0     [003]   700.000000: cpu_frequency:             state=300000 cpu_id=2
          <idle>-0     [003]   700.000000: cpu_frequency:             state=300000 cpu_id=3
          <idle>-0     [000]   800.000000: cpu_idle:             state=4294967295 cpu_id=0
          <idle>-0     [001]   800.000000: cpu_idle:             state=4294967295 cpu_id=1
          <idle>-0     [002]   800.000000: cpu_idle:             state=4294967295 cpu_id=2
          <idle>-0     [003]   800.000000: cpu_idle:             state=4294967295 cpu_id=3
          <idle>-0     [001]   900.000000: cpu_frequency:             state=400000 cpu_id=0
          <idle>-0     [002]   900.000000: cpu_frequency:             state=400000 cpu_id=1
          <idle>-0     [003]   900.000000: cpu_frequency:             state=400000 cpu_id=2
          <idle>-0     [003]   900.000000: cpu_frequency:             state=400000 cpu_id=3
          <idle>-0     [000]   950.000000: cpu_idle:             state=4294967295 cpu_id=0
"""
class TestFrequency(MillhouseTestBase):
    def test_cpu_frequency_signal(self):
        ftrace = self.make_ftrace(TEST_TRACE_DATA)
        analyzer = TraceAnalyzer(ftrace)
        df = analyzer.frequency.signal.cpu_frequency()
        self.assertEqual(df.columns.tolist(), analyzer.cpus)

    # TODO test cluster coherency check

    def test_freq_residency(self):
        ftrace = self.make_ftrace(TEST_TRACE_DATA)
        analyzer = TraceAnalyzer(ftrace,
                                 frequency_domains=[[0, 1], [2, 3]])

        df = analyzer.frequency.stats.frequency_residency()

        print df
        self.assertEqual(df.columns.tolist(), [(0, 'active'), (0, 'total'),
                                               (2, 'active'), (2, 'total')])
        self.assertEqual(df.index.tolist(), [100000, 200000, 300000, 400000])
        self.assertFalse(df.isnull().any().any())

