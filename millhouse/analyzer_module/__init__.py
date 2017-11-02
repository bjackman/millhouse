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

from millhouse import MissingTraceEventsError

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

class DfgRegister(object):
    # This class doesn't really do anything except act as an object to hang
    # attributes off, and also provides a more helpful error message for
    # AttributeErrors.
    def __init__(self, name):
        self.name = name
        self.getters = []

    def add_getter(self, name, val):
        self.getters.append(name)
        setattr(self, name, val)

    def __getattr__(self, name):
        try:
            return super(DfgRegister, self).__getattr__(name)
        except AttributeError:
            raise AttributeError(
                "{} doesn't have a DataFrame accessor named '{}' "
                "Available are: {}".format(self.name, name, self.getters))

class AnalyzerModule(object):
    """TODO doc"""
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.ftrace = self.analyzer.ftrace
        self.cpus = analyzer.cpus

        self.event = DfgRegister('{}.event'.format(self.__class__.__name__))
        self.signal = DfgRegister('{}.signal'.format(self.__class__.__name__))
        self.stats = DfgRegister('{}.stats'.format(self.__class__.__name__))

        # Set up registers to provide nice accessor code. E.g.
        # You can access `self._dfg_signal_cpu_idle_state` as
        # `self.signal.cpu_idle_state`
        for attr in dir(self):
            if not attr.startswith('_dfg_'):
                continue

            registers = {
                '_dfg_signal_': self.signal,
                '_dfg_event_': self.event,
                '_dfg_stats_': self.stats
            }
            for prefix, _register in registers.iteritems():
                if attr.startswith(prefix):
                    register = _register
                    break
            else:
                raise ValueError('Attribute {} of {} must start with one of {}'
                                 .format(attr, self.__class__, registers.keys()))

            name = attr[len(prefix):]
            register.add_getter(name, getattr(self, attr))

    def _add_cpu_columns(self, df):
        for cpu in self.cpus:
            if cpu not in df.columns:
                df[cpu] = np.nan
        return df.sort_index(axis=1) # Sort column labels

