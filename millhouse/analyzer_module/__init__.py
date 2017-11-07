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

from wrapt import decorator

from millhouse.exception import MissingTraceEventsError

def requires_events(events=None):
    """
    This decorator can be applied to a _dfg method to automatically raise a
    MissingTraceEventsError whenever it is called when the required events are
    missing.

    Note that this decorator has a parameter and so it must have "()" after its
    name (i.e. you need to write "@requires_events()" above the method name).

    :param events: The list of names of events required by the _dfg method. If
                   None, defaults to the value of the ``required_events``
                   attribute of the object to which the decorated method is
                   bound.
    """
    @decorator
    def wrapper(wrapped, instance, args, kwargs):
        # TODO add testcase with an assertRaises
        _events = events or instance.required_events

        missing_events = set(_events) - set(instance.available_events)
        if missing_events:
            raise MissingTraceEventsError(missing_events)

        return wrapped(*args, **kwargs)
    return wrapper

class _DfgRegister(object):
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
            return super(_DfgRegister, self).__getattr__(name)
        except AttributeError:
            raise AttributeError(
                "{} doesn't have a DataFrame accessor named '{}' "
                "Available are: {}".format(self.name, name, self.getters))

class AnalyzerModule(object):
    """
    An object encapsulating a group of analyses that can be done on a trace.

    :ivar analyzer: The `class`:TraceAnalyzer associated with this object
    :ivar ftrace: Alias for ``analyzer.ftrace``

    TODO .. continue documenting
    """

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.ftrace = self.analyzer.ftrace
        self.cpus = analyzer.cpus

        self.event = _DfgRegister('{}.event'.format(self.__class__.__name__))
        self.signal = _DfgRegister('{}.signal'.format(self.__class__.__name__))
        self.stats = _DfgRegister('{}.stats'.format(self.__class__.__name__))

        self.available_events = self.analyzer.available_events

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

        if self.ftrace.normalize_time:
            self.trace_end_time = 0 + self.ftrace.get_duration()
        else:
            self.__trace_end_time = self.ftrace.basetime + self.ftrace.get_duration()

    def _do_pivot(self, df, columns):
        """
        Perform a DataFrame pivot, dealing with duplicate indices as necessary

        If there are two rows in the DataFrame with the same index and the same
        value in the column indicated by 'columns', Pandas raises 'ValueError:
        Index contains duplicate entries, cannot reshape' due to the ambiguity
        as to which value to take. This solves the issue by taking the _latest_
        value (i.e. the one with the higher value in the __line column - this is
        implemented by assuming that __line always increases with iloc).

        See Pandas documentation for more detail.
        """
        return df.pivot_table(columns=columns, index='Time',
                              aggfunc=lambda x: x.iloc[-1])


    def _add_cpu_columns(self, df):
        for cpu in self.cpus:
            if cpu not in df.columns:
                df[cpu] = np.nan
        return df.sort_index(axis=1) # Sort column labels

    def _extrude_signal(self, df):
        """
        Duplicate the last event of a signal DataFrame at the end of the trace

        Where you have a DataFrame that represents a signal, and the last event
        is not at the end of the trace (e.g. because your CPU frequency did not
        change in the last 500ms of the trace), this can be used to 'extrude'
        that signal up to the end of the trace so that it can be usefully
        integrated.
        """
        return df.append(pd.Series(df.iloc[-1], name=self.__trace_end_time))
