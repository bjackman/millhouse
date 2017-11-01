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

from wrapt import decorator

def requires_events(events=None):
    @decorator
    def wrapper(wrapped, instance, args, kwargs):
        """TODO doc"""
        # TODO add testcase with an assertRaises
        _events = events or instance.required_events

        missing_events = set(_events) - set(instance.analyzer.available_events)
        if missing_events:
            raise MissingTraceEventsError(missing_events)

        return wrapped(*args, **kwargs)
    return wrapper

class AnalyzerModule(object):
    """TODO doc"""
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.ftrace = self.analyzer.ftrace
        self.cpus = analyzer.cpus

    def _add_cpu_columns(self, df):
        for cpu in self.cpus:
            if cpu not in df.columns:
                df[cpu] = np.nan
        return df.sort_index(axis=1) # Sort column labels

