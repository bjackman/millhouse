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

from millhouse.analyzer_module import requires_events, AnalyzerModule

class ThermalAnalyzerModule(AnalyzerModule):
    required_events = ['thermal']

    @requires_events()
    def _dfg_signal_temperature(self):
        # Looking for a docstring? See the .rst file(s) in doc/ for all the _dfg
        # methods' documentation.

        df = self.ftrace.thermal.data_frame
        df = self._extrude_signal(df)
        return self._do_pivot(df, 'thermal_zone')['temp']

    def _dfg_stats_avg_temperature(self):
        df = self._dfg_signal_temperature().dropna()
        duration = df.index[-1] - df.index[0]

        zones = df.columns.tolist()
        avgs = []
        for zone in zones:
            if duration == 0:
                avgs.append(np.nan)
            else:
                avgs.append(np.trapz(df[zone], df.index) / duration)

        return pd.DataFrame({'avg_temperature': avgs}, index=zones)
