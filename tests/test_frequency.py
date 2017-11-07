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
          <idle>-0     [001]   500.000000: cpu_frequency_devlib:      state=110000 cpu_id=2
          <idle>-0     [002]   500.000000: cpu_frequency_devlib:      state=110000 cpu_id=3
          <idle>-0     [001]   550.000000: cpu_frequency:             state=200000 cpu_id=0
          <idle>-0     [002]   550.000000: cpu_frequency:             state=200000 cpu_id=1
          <idle>-0     [003]   550.000000: cpu_frequency:             state=210000 cpu_id=2
          <idle>-0     [003]   550.000000: cpu_frequency:             state=210000 cpu_id=3
          <idle>-0     [000]   600.000000: cpu_idle:             state=0 cpu_id=0
          <idle>-0     [001]   600.000000: cpu_idle:             state=0 cpu_id=1
          <idle>-0     [002]   600.000000: cpu_idle:             state=0 cpu_id=2
          <idle>-0     [003]   600.000000: cpu_idle:             state=0 cpu_id=3
          <idle>-0     [001]   650.000000: cpu_frequency:             state=250000 cpu_id=0
          <idle>-0     [002]   650.000000: cpu_frequency:             state=250000 cpu_id=1
          <idle>-0     [003]   650.000000: cpu_frequency:             state=260000 cpu_id=2
          <idle>-0     [003]   650.000000: cpu_frequency:             state=260000 cpu_id=3
          <idle>-0     [001]   700.000000: cpu_frequency:             state=300000 cpu_id=0
          <idle>-0     [002]   700.000000: cpu_frequency:             state=300000 cpu_id=1
          <idle>-0     [003]   700.000000: cpu_frequency:             state=310000 cpu_id=2
          <idle>-0     [003]   700.000000: cpu_frequency:             state=310000 cpu_id=3
          <idle>-0     [000]   800.000000: cpu_idle:             state=4294967295 cpu_id=0
          <idle>-0     [001]   800.000000: cpu_idle:             state=4294967295 cpu_id=1
          <idle>-0     [002]   800.000000: cpu_idle:             state=4294967295 cpu_id=2
          <idle>-0     [003]   800.000000: cpu_idle:             state=4294967295 cpu_id=3
          <idle>-0     [001]   900.000000: cpu_frequency:             state=400000 cpu_id=0
          <idle>-0     [002]   900.000000: cpu_frequency:             state=400000 cpu_id=1
          <idle>-0     [003]   900.000000: cpu_frequency:             state=410000 cpu_id=2
          <idle>-0     [003]   900.000000: cpu_frequency:             state=410000 cpu_id=3
          <idle>-0     [000]   950.000000: cpu_idle:             state=4294967295 cpu_id=0
"""
class TestCpufreq(MillhouseTestBase):
    def test_cpu_frequency_signal(self):
        ftrace = self.make_ftrace(TEST_TRACE_DATA)
        analyzer = TraceAnalyzer(ftrace)
        df = analyzer.cpufreq.signal.cpu_frequency()
        self.assertEqual(df.columns.tolist(), analyzer.cpus)

    # TODO test cluster coherency check

    def test_freq_residency(self):
        ftrace = self.make_ftrace(TEST_TRACE_DATA)
        analyzer = TraceAnalyzer(ftrace,
                                 cpufreq_domains=[[0, 1], [2, 3]])

        df1 = analyzer.cpufreq.stats.frequency_residency([0, 1])
        df2 = analyzer.cpufreq.stats.frequency_residency([2, 3])

        self.assertEqual(df1['active'][100000], 50)
        self.assertEqual(df1[ 'total'][100000], 50)
        self.assertEqual(df2['active'][110000], 50)
        self.assertEqual(df2[ 'total'][110000], 50)

        self.assertEqual(df1['active'][200000], 50)
        self.assertEqual(df1[ 'total'][200000],100)
        self.assertEqual(df2['active'][210000], 50)
        self.assertEqual(df2[ 'total'][210000],100)

        self.assertEqual(df1['active'][250000],  0)
        self.assertEqual(df1[ 'total'][250000], 50)
        self.assertEqual(df2['active'][260000],  0)
        self.assertEqual(df2[ 'total'][260000], 50)

        self.assertEqual(df1['active'][300000],100)
        self.assertEqual(df1[ 'total'][300000],200)
        self.assertEqual(df2['active'][310000],100)
        self.assertEqual(df2[ 'total'][310000],200)

        self.assertEqual(df1['active'][400000], 50)
        self.assertEqual(df1[ 'total'][400000], 50)
        self.assertEqual(df2['active'][410000], 50)
        self.assertEqual(df2[ 'total'][410000], 50)
