#    Copyright 2017 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from millhouse.analyzer_module.cpuidle import IdleAnalyzerModule
from millhouse.analyzer_module.cpufreq import CpufreqAnalyzerModule
from millhouse.analyzer_module.thermal import ThermalAnalyzerModule

class TraceAnalyzer(object):
    """
    The main entry-point class for using this library

    This class encapsulates the analysis of a single TRAPpy ``FTrace`` object.
    Analyses are grouped by area, for example DataFrame getters related to CPU
    frequency scaling are attached to the :attr:`cpufreq` attribute.

    Optionally, extra information that is known about the target can be provided
    as parameters, in which case they will be used to enrich the available
    analyses.

    :ivar cpufreq: :class:`CpuFreqAnalyzerModule` containing CPU frequency
                    analyses.
    :ivar cpuidle: :class:`IdleAnalyzerModule` containing CPU idle state analyses.
    :ivar thermal: :class:`ThermalAnalyzerModule` containing thermal analyses.

    :ivar available_events: List of trace events that are available

    :param ftrace: :class:`trappy.FTrace` object to base analysis on

    :param window: Tuple of ``(start_time, end_time)`` representing region of
            trace to analyze. This is distinct from TRAPpy's window: while
            TRAPpy simply ignores events that fall outside the window,
            ``TraceAnalyzer`` will still consider them in order to detect the
            value of signals at the beginning of the trace. For example, suppose
            the only cpu_frequency events occur at time ``1.0``, and window is
            ``(2.0, 3.0)``, ``TraceAnalyzer`` will use those cpu_frequency
            events to determine the CPU frequencies at time 2.0.

            Note that the values of this parameter must play nicely with
            TRAPpy's time normalization: if :attr:`ftrace` was constructed with
            ``normalize_time=False``, ``window=(0, 10)`` will probably not
            include any data (since the first event in the trace probably has a
            timestamp later than ``10.0``)

            Both elements are optional: ``None`` means use up to the
            beginning/end of the trace.

    :param topology: Optional :class:`trappy.stats.Topology` object describing
            the target the trace was collected from. Some analyses will be
            enriched if this is provided

    :param cpufreq_domains: Optional list of lists of CPU IDs whose CPU frequencies are
                            tied together.
    """
    def get_trace_event(self, event):
        """
        Helper to return a raw trace event as parsed by TRAPpy

        :param event: Name of the event - e.g. ``"cpu_frequency"``
        """
        # TODO raise proper error if event missing (and test it)
        return getattr(self.ftrace, event).data_frame

    def __init__(self, ftrace, window=(None, None), topology=None, cpufreq_domains=None):
        self.ftrace = ftrace
        self.topology = topology
        self.cpufreq_domains = cpufreq_domains

        # TODO: This is copied from LISA. This should really be solved in TRAPpy
        # and removed from both here and LISA.
        self.available_events = []
        for val in self.ftrace.get_filters(''):
            obj = getattr(self.ftrace, val)
            if len(obj.data_frame):
                self.available_events.append(val)

        if not self.available_events:
            raise ValueError('No events found in trace')

        # TODO: Have TRAPpy expose this 'publicly'
        # TODO: Test this works?
        max_cpu = max(self.get_trace_event(e)['__cpu'].max()
                      for e in self.available_events)
        self.cpus = range(max_cpu + 1)

        start, end = window
        if start is None:
            start = self.ftrace.basetime
        if end is None:
            end = self.ftrace.basetime + self.ftrace.get_duration()
        window = (start, end)

        self.cpuidle = IdleAnalyzerModule(self, window)
        self.cpufreq = CpufreqAnalyzerModule(self, window)
        self.thermal = ThermalAnalyzerModule(self, window)
