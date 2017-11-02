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

from trappy.utils import listify

from millhouse import MissingTraceEventsError
from millhouse.analyzer_module import requires_events, AnalyzerModule

def integrate_square_wave(series):
    values = series.values[:-1]
    return float((values * np.diff(series.index)).sum())

class FrequencyAnalyzerModule(AnalyzerModule):
    required_events = ['cpu_frequency']

    def __init__(self, *args, **kwargs):
        super(FrequencyAnalyzerModule, self).__init__(*args, **kwargs)

        self.clusters = None # TODO
        self.clusters_freq_coherent = None
        self.sanitize_trace_events()

    def sanitize_trace_events(self):
        """
        Verify that all platform reported clusters are frequency coherent (i.e.
        frequency scaling is performed at a cluster level).
        """
        if 'cpu_frequency_devlib' in self.available_events:
            self._inject_devlib_events()

        # Frequency Coherency Check
        if self.clusters:
            df = self.analyzer.get_trace_event('cpu_frequency')
            for _, cpus in clusters.iteritems():
                cluster_df = df[df.cpu.isin(cpus)]
                for chunk in self._chunker(cluster_df, len(cpus)):
                    f = chunk.iloc[0].frequency
                    if any(chunk.frequency != f):
                        self.freq_coherency = False

    def _chunker(self, seq, size):
        """
        Given a data frame or a series, generate a sequence of chunks of the
        given size.

        :param seq: data to be split into chunks
        :type seq: :mod:`pandas.Series` or :mod:`pandas.DataFrame`

        :param size: size of each chunk
        :type size: int
        """
        return (seq.iloc[pos:pos + size] for pos in range(0, len(seq), size))

    def _inject_devlib_events(self):
        devlib_freq = self.analyzer.get_trace_event('cpu_frequency_devlib')
        devlib_freq.rename(columns={'cpu_id':'cpu'}, inplace=True)
        devlib_freq.rename(columns={'state':'frequency'}, inplace=True)

        df = self.analyzer.get_trace_event('cpu_frequency')

        # devlib always introduces fake cpu_frequency events, in case the
        # OS has not generated cpu_frequency envets there are the only
        # frequency events to report
        if len(df) == 0:
            # Register devlib injected events as 'cpu_frequency' events
            setattr(self.ftrace.cpu_frequency, 'data_frame', devlib_freq)
            df = devlib_freq
            self.available_events.append('cpu_frequency')

        # make sure fake cpu_frequency events are never interleaved with
        # OS generated events
        else:
            if len(devlib_freq) > 0:

                # Frequencies injection is done in a per-cluster based.
                # This is based on the assumption that clusters are
                # frequency choerent.
                # For each cluster we inject devlib events only if
                # these events does not overlaps with os-generated ones.

                # Inject "initial" devlib frequencies
                os_df = df
                dl_df = devlib_freq.iloc[:self.platform['cpus_count']]
                for _,c in self.platform['clusters'].iteritems():
                    dl_freqs = dl_df[dl_df.cpu.isin(c)]
                    os_freqs = os_df[os_df.cpu.isin(c)]
                    # All devlib events "before" os-generated events
                    if os_freqs.empty or \
                    os_freqs.index.min() > dl_freqs.index.max():
                        self._log.debug("Insert devlib freqs for %s", c)
                        df = pd.concat([dl_freqs, df])

                # Inject "final" devlib frequencies
                os_df = df
                dl_df = devlib_freq.iloc[self.platform['cpus_count']:]
                for _,c in self.platform['clusters'].iteritems():
                    dl_freqs = dl_df[dl_df.cpu.isin(c)]
                    os_freqs = os_df[os_df.cpu.isin(c)]
                    # All devlib events "after" os-generated events
                    if os_freqs.empty or \
                    os_freqs.index.max() < dl_freqs.index.min():
                        df = pd.concat([df, dl_freqs])

                df.sort_index(inplace=True)

            setattr(self.ftrace.cpu_frequency, 'data_frame', df)

    @requires_events()
    def _dfg_signal_cpu_frequency(self):
        """TODO doc"""
        df = (self.ftrace.cpu_frequency.data_frame
              .pivot(columns='cpu')['frequency'].ffill())
        return self._add_cpu_columns(df)
