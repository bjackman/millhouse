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

class TestFrequency(MillhouseTestBase):
    def test_cpu_frequency_signal(self):
        ftrace = self.make_ftrace("""
          <idle>-0     [000]   000.000000: cpu_idle:             state=4294967295 cpu_id=0
          <idle>-0     [001]   001.000000: cpu_idle:             state=4294967295 cpu_id=1
          <idle>-0     [002]   002.000000: cpu_idle:             state=4294967295 cpu_id=2
          <idle>-0     [003]   003.000000: cpu_idle:             state=4294967295 cpu_id=3
          <idle>-0     [004]   004.000000: cpu_idle:             state=4294967295 cpu_id=4
          <idle>-0     [004]   519.022147: cpu_frequency:             state=200000 cpu_id=4
          <idle>-0     [004]   519.022641: cpu_frequency:             state=100000 cpu_id=4
          <idle>-0     [001]   519.022642: cpu_frequency:             state=100000 cpu_id=1
          <idle>-0     [002]   519.022643: cpu_frequency:             state=100000 cpu_id=2
          <idle>-0     [001]   519.022788: cpu_frequency:             state=200000 cpu_id=1
          <idle>-0     [002]   519.022831: cpu_frequency:             state=300000 cpu_id=2
          <idle>-0     [003]   519.022867: cpu_frequency:             state=100000 cpu_id=3
          <idle>-0     [003]   519.023045: cpu_frequency:             state=300000 cpu_id=3
          <idle>-0     [004]   519.023080: cpu_frequency:             state=400000 cpu_id=4
        """)
        analyzer = TraceAnalyzer(ftrace)
        df = analyzer.frequency.signal.cpu_frequency()
        self.assertEqual(df.columns.tolist(), analyzer.cpus)

    # TODO test devlib events
    #           cluster coherency check
