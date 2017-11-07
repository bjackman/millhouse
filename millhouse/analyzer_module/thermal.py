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

from millhouse.analyzer_module import requires_events, AnalyzerModule

class ThermalAnalyzerModule(AnalyzerModule):
    required_events = ['thermal_temperature']

    @requires_events()
    def _dfg_signal_temperature(self):
        df = self.ftrace.thermal_temperature.data_frame
        df = self._extrude_signal(df)
        return self._do_pivot(df, 'thermal_zone')['temp']

