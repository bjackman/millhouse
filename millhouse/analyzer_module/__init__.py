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
from wrapt import decorator

@decorator
def requires_events(wrapped, instance, args, kwargs):
    # TODO add testcase with an assertRaises
    """TODO doc"""
    events = instance.required_events

    missing_events = set(events) - set(instance.analyzer.available_events)
    if missing_events:
        raise MissingTraceEventsError(missing_events)
    return wrapped(*args, **kwargs)

class AnalyzerModule(object):
    """TODO doc"""
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.ftrace = self.analyzer.ftrace
        self.cpus = analyzer.cpus

