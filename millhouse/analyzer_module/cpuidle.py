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

from millhouse.exception import MissingTraceEventsError
from millhouse.analyzer_module import requires_events, AnalyzerModule
from millhouse.utils import (drop_consecutive_duplicates as drop_dupes,
                             integrate_square_wave)

class IdleAnalyzerModule(AnalyzerModule):
    required_events = ['cpu_idle']

    def __init__(self, *args, **kwargs):
        super(IdleAnalyzerModule, self).__init__(*args, **kwargs)

    @requires_events()
    def _dfg_signal_cpu_idle_state(self):
        df = self._do_pivot(
            self.ftrace.cpu_idle.data_frame, 'cpu_id')['state'].ffill()

        return self._add_cpu_columns(self._extrude_signal(df))

    def _dfg_signal_cpu_active(self):
        df = self.signal.cpu_idle_state()
        df[~df.isnull()] = (df == -1)
        return df

    def _dfg_signal_cluster_active(self, cluster):
        df = self.signal.cpu_active()[cluster]

        # Cluster active is the OR between the actives on each CPU
        # belonging to that specific cluster
        df = df.sum(axis=1)
        df[~df.isnull()] = df.astype(bool)

        return pd.DataFrame({'active': df})

    @requires_events()
    def _dfg_event_cpu_wakeup(self):
        """
        Get a a DataFrame of events where a CPU was woken

        Has a single column "cpu", reporting which CPU was woken at the time
        reported in the index.
        """
        sr = pd.Series()
        state_df = self.signal.cpu_idle_state()
        for cpu in self.cpus:
            cpu_sr = drop_dupes(state_df[cpu].dropna())
            cpu_sr = cpu_sr[cpu_sr == -1].replace(-1, cpu)
            sr = sr.append(cpu_sr)
        return pd.DataFrame({'cpu': sr}).sort_index()

    def _dfg_stats_cpu_time(self):
        df = self._dfg_signal_cpu_active()
        return pd.DataFrame({'active_time': [integrate_square_wave(df[s].dropna())
                                             for s in df]})
