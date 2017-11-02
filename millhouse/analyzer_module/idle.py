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

import pandas as pd

from millhouse import MissingTraceEventsError
from millhouse.analyzer_module import requires_events, AnalyzerModule

#
# TODO move the following into common module
#

def drop_consecutive_duplicates(df):
    """TODO doc"""
    return df[df.shift() != df]

drop_dupes = drop_consecutive_duplicates

class IdleAnalyzerModule(AnalyzerModule):
    required_events = ['cpu_idle']

    def __init__(self, *args, **kwargs):
        super(IdleAnalyzerModule, self).__init__(*args, **kwargs)

    # TODO should it be analyzer.idle.signal.cpu_idle_state?
    # Current is        analyzer.idle.get_cpu_idle_state_signal
    @requires_events()
    def _dfg_signal_cpu_idle_state(self):
        """TODO doc"""
        df = self.ftrace.cpu_idle.data_frame
        df = df.pivot(columns='cpu_id')['state'].ffill()

        return self._add_cpu_columns(df)

    @requires_events()
    def _dfg_event_cpu_wakeup(self):
        """TODO doc"""
        sr = pd.Series()
        state_df = self.signal.cpu_idle_state()
        for cpu in self.cpus:
            cpu_sr = drop_dupes(state_df[cpu].dropna())
            cpu_sr = cpu_sr[cpu_sr == -1].replace(-1, cpu)
            sr = sr.append(cpu_sr)
        return pd.DataFrame({'cpu': sr}).sort_index()

