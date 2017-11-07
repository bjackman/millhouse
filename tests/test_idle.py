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

import numpy as np

from test_base import MillhouseTestBase

from millhouse.trace_analyzer import TraceAnalyzer
from millhouse.utils import drop_consecutive_duplicates as drop_dupes

class TestIdle(MillhouseTestBase):
    def test_cpu_wakeups(self):
        ftrace = self.make_ftrace("""
          <idle>-0     [004]   519.021928: cpu_idle:             state=4294967295 cpu_id=4
          <idle>-0     [004]   519.022147: cpu_idle:             state=0 cpu_id=4
          <idle>-0     [004]   519.022641: cpu_idle:             state=4294967295 cpu_id=4
          <idle>-0     [001]   519.022642: cpu_idle:             state=4294967295 cpu_id=1
          <idle>-0     [002]   519.022643: cpu_idle:             state=4294967295 cpu_id=2
          <idle>-0     [001]   519.022788: cpu_idle:             state=0 cpu_id=1
          <idle>-0     [002]   519.022831: cpu_idle:             state=2 cpu_id=2
          <idle>-0     [003]   519.022867: cpu_idle:             state=4294967295 cpu_id=3
          <idle>-0     [003]   519.023045: cpu_idle:             state=2 cpu_id=3
          <idle>-0     [004]   519.023080: cpu_idle:             state=1 cpu_id=4
        """)

        analyzer = TraceAnalyzer(ftrace)
        df = analyzer.cpuidle.event.cpu_wakeup()

        exp_index=[519.021928, 519.022641, 519.022642, 519.022643, 519.022867]
        exp_cpus= [         4,          4,          1,          2,          3]
        self.assertListEqual(df.index.tolist(), exp_index)
        self.assertListEqual(df['cpu'].tolist(), exp_cpus)

    def test_cluster_active(self):
        ftrace = self.make_ftrace("""
          <idle>-0     [000]   519.021928: cpu_idle:             state=4294967295 cpu_id=0
          <idle>-0     [001]   519.022147: cpu_idle:             state=4294967295 cpu_id=1
          <idle>-0     [002]   519.022641: cpu_idle:             state=4294967295 cpu_id=2
          <idle>-0     [003]   519.022642: cpu_idle:             state=4294967295 cpu_id=3
          <idle>-0     [002]   519.022643: cpu_idle:             state=0 cpu_id=2
          <idle>-0     [000]   519.022788: cpu_idle:             state=1 cpu_id=0
          <idle>-0     [003]   519.022831: cpu_idle:             state=2 cpu_id=3
        """)

        analyzer = TraceAnalyzer(ftrace)
        df = drop_dupes(analyzer.cpuidle.signal.cluster_active([2, 3]))

        self.assertTrue(np.isnan(df['active'].iloc[0]))
        df = df.dropna()

        exp_index = [519.022641, 519.022831]
        exp_states = [        1,          0]

        self.assertListEqual(df.index.tolist(), exp_index)
        self.assertListEqual(df['active'].tolist(), exp_states)


    def test_cluster_active_single(self):
        ftrace = self.make_ftrace("""
          <idle>-0     [000]   100.000000: cpu_idle:             state=4294967295 cpu_id=0
          <idle>-0     [001]   101.000000: cpu_idle:             state=4294967295 cpu_id=1
          <idle>-0     [002]   102.000000: cpu_idle:             state=4294967295 cpu_id=2
          <idle>-0     [003]   103.000000: cpu_idle:             state=4294967295 cpu_id=3
          <idle>-0     [004]   104.000000: cpu_idle:             state=4294967295 cpu_id=4
          <idle>-0     [000]   600.000000: cpu_idle:             state=0 cpu_id=0
          <idle>-0     [001]   601.000000: cpu_idle:             state=0 cpu_id=1
          <idle>-0     [002]   602.000000: cpu_idle:             state=0 cpu_id=2
          <idle>-0     [003]   603.000000: cpu_idle:             state=0 cpu_id=3
          <idle>-0     [004]   604.000000: cpu_idle:             state=0 cpu_id=4
        """)

        analyzer = TraceAnalyzer(ftrace)
        df = drop_dupes(analyzer.cpuidle.signal.cluster_active([0]))
        df = df.dropna()

        exp_index = [  100., 600.]
        exp_states = [    1,    0]
        self.assertListEqual(df.index.tolist(), exp_index)
        self.assertListEqual(df['active'].tolist(), exp_states)

    def test_cpu_time(self):
        ftrace = self.make_ftrace("""
          <idle>-0     [000]   100.000000: cpu_idle:             state=4294967295 cpu_id=0
          <idle>-0     [001]   101.000000: cpu_idle:             state=4294967295 cpu_id=1
          <idle>-0     [002]   102.000000: cpu_idle:             state=4294967295 cpu_id=2
          <idle>-0     [003]   103.000000: cpu_idle:             state=4294967295 cpu_id=3
          <idle>-0     [004]   104.000000: cpu_idle:             state=4294967295 cpu_id=4
          <idle>-0     [000]   600.000000: cpu_idle:             state=0 cpu_id=0
          <idle>-0     [001]   601.000000: cpu_idle:             state=0 cpu_id=1
          <idle>-0     [002]   602.000000: cpu_idle:             state=0 cpu_id=2
          <idle>-0     [003]   603.000000: cpu_idle:             state=0 cpu_id=3
          <idle>-0     [004]   604.000000: cpu_idle:             state=0 cpu_id=4
        """)

        analyzer = TraceAnalyzer(ftrace)
        df = analyzer.cpuidle.stats.cpu_time()

        self.assertEqual(df['active_time'][0], 500)
        self.assertEqual(df['active_time'][1], 500)
        self.assertEqual(df['active_time'][2], 500)
        self.assertEqual(df['active_time'][3], 500)
        self.assertEqual(df['active_time'][4], 500)
