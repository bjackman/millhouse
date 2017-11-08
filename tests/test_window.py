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

import pandas as pd

from millhouse.trace_analyzer import TraceAnalyzer

from test_base import MillhouseTestBase

TEST_DATA="""
<idle>-0     [001]   100.000000: cpu_frequency:             state=1000 cpu_id=0
<idle>-0     [002]   100.000000: cpu_frequency:             state=1000 cpu_id=1
<idle>-0     [003]   100.000000: cpu_frequency:             state=1000 cpu_id=2
<idle>-0     [003]   100.000000: cpu_frequency:             state=1000 cpu_id=3
<idle>-0     [001]   200.000000: cpu_frequency:             state=3000 cpu_id=0
<idle>-0     [002]   200.000000: cpu_frequency:             state=3000 cpu_id=1
<idle>-0     [003]   200.000000: cpu_frequency:             state=2000 cpu_id=2
<idle>-0     [003]   200.000000: cpu_frequency:             state=2000 cpu_id=3
<idle>-0     [001]   300.000000: cpu_frequency:             state=3000 cpu_id=0
<idle>-0     [002]   300.000000: cpu_frequency:             state=3000 cpu_id=1
<idle>-0     [003]   300.000000: cpu_frequency:             state=3000 cpu_id=2
<idle>-0     [003]   300.000000: cpu_frequency:             state=3000 cpu_id=3
"""

class TestAnalyzerWindow(MillhouseTestBase):
    def test_no_window(self):
        """Test having no window"""
        ftrace = self.make_ftrace(TEST_DATA)
        analyzer = TraceAnalyzer(ftrace)
        signal = analyzer.cpufreq.signal.cpu_frequency()
        self.assertEqual(signal.index[0], 100.0)
        self.assertEqual(signal.iloc[0].tolist(), [1000, 1000, 1000, 1000])

    def test_window_after(self):
        """Test having a window after the range of the trace events"""
        ftrace = self.make_ftrace(TEST_DATA)
        analyzer = TraceAnalyzer(ftrace, window=(400, 500))
        signal = analyzer.cpufreq.signal.cpu_frequency()
        self.assertEqual(len(signal), 2)
        self.assertEqual(signal.index[0], 400.0)
        self.assertEqual(signal.iloc[0].tolist(), [3000, 3000, 3000, 3000])
        self.assertEqual(signal.index[1], 500.0)
        self.assertEqual(signal.iloc[1].tolist(), [3000, 3000, 3000, 3000])

    def test_window_before(self):
        """Test having a window before the range of the trace events"""
        ftrace = self.make_ftrace(TEST_DATA)
        analyzer = TraceAnalyzer(ftrace, window=(10, 20))
        signal = analyzer.cpufreq.signal.cpu_frequency()
        self.assertEqual(len(signal), 2)
        self.assertEqual(signal.index[0], 10.0)
        self.assertTrue(signal.iloc[0].isnull().all())
        self.assertEqual(signal.index[1], 20.0)
        self.assertTrue(signal.iloc[1].isnull().all())

    def test_window_end(self):
        """Test having a window aligning with the end of the trace events"""
        ftrace = self.make_ftrace(TEST_DATA)
        analyzer = TraceAnalyzer(ftrace, window=(250, 300))
        signal = analyzer.cpufreq.signal.cpu_frequency()
        self.assertEqual(len(signal), 2)
        self.assertEqual(signal.index[0], 250.0)
        self.assertEqual(signal.iloc[0].tolist(), [3000, 3000, 2000, 2000])
        self.assertEqual(signal.index[1], 300.0)
        self.assertEqual(signal.iloc[1].tolist(), [3000, 3000, 3000, 3000])

    def test_window_end_overlap(self):
        """Test having a window overlapping the end of the trace events"""
        ftrace = self.make_ftrace(TEST_DATA)
        analyzer = TraceAnalyzer(ftrace, window=(150, 350))
        signal = analyzer.cpufreq.signal.cpu_frequency()
        self.assertEqual(len(signal), 4)
        self.assertEqual(signal.index[0], 150.0)
        self.assertEqual(signal.iloc[0].tolist(), [1000, 1000, 1000, 1000])
        self.assertEqual(signal.index[1], 200.0)
        self.assertEqual(signal.iloc[1].tolist(), [3000, 3000, 2000, 2000])
        self.assertEqual(signal.index[2], 300.0)
        self.assertEqual(signal.iloc[2].tolist(), [3000, 3000, 3000, 3000])
        self.assertEqual(signal.index[3], 350.0)
        self.assertEqual(signal.iloc[3].tolist(), [3000, 3000, 3000, 3000])
