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

from millhouse.analyzer_module.idle import IdleAnalyzerModule
from millhouse.analyzer_module.frequency import FrequencyAnalyzerModule

class TraceAnalyzer(object):
    """TODO document"""
    def get_trace_event(self, event):
        """TODO doc"""
        # TODO raise proper error if event missing (and test it)
        return getattr(self.ftrace, event).data_frame

    def __init__(self, ftrace, topology=None):
        self.ftrace = ftrace
        self.topology = topology

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

        self.idle = IdleAnalyzerModule(self)
        self.frequency = FrequencyAnalyzerModule(self)
