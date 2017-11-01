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

import numpy as np
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
        self.has_events = 'cpu_idle' in self.analyzer.available_events

    # TODO should it be analyzer.idle.signal.cpu_idle_state?
    # Current is        analyzer.idle.get_cpu_idle_state_signal
    # TODO Make this aututomatically return a column for all CPUs if we know
    #      what the CPUs were
    @requires_events()
    def get_cpu_idle_state_signal(self):
        """TODO doc"""
        df = self.ftrace.cpu_idle.data_frame
        df = df.pivot(columns='cpu_id')['state'].ffill()

        # TODO make this common
        for cpu in self.cpus:
            if cpu not in df.columns:
                df[cpu] = np.nan
        df = df.sort_index(axis=1) # Sort column labels

        return df

    @requires_events()
    def get_cpu_wakeup_events(self):
        """TODO doc"""
        sr = pd.Series()
        state_df = self.get_cpu_idle_state_signal()
        for cpu in self.cpus:
            cpu_sr = drop_dupes(state_df[cpu].dropna())
            cpu_sr = cpu_sr[cpu_sr == -1].replace(-1, cpu)
            sr = sr.append(cpu_sr)
            print
            print cpu
            print cpu_sr
            print sr
            print
        return pd.DataFrame({'cpu': sr}).sort_index()

