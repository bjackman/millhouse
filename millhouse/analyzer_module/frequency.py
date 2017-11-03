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

from millhouse.exception import MissingTraceEventsError
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
            self.clusters_freq_coherent = True
            for _, cpus in clusters.iteritems():
                cluster_df = df[df.cpu.isin(cpus)]
                for chunk in self._chunker(cluster_df, len(cpus)):
                    f = chunk.iloc[0].frequency
                    if any(chunk.frequency != f):
                        self.clusters_freq_coherent = False


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

    def _dfg_stats_frequency_residency(self):
        return self._get_freq_residency(0)

    @requires_events(['cpu_idle', 'cpu_frequency'])
    def _get_freq_residency(self, cluster):
        """
        Get a DataFrame with per cluster frequency residency, i.e. amount of
        time spent at a given frequency in each cluster.

        :param cluster: this can be either a single CPU ID or a list of CPU IDs
            belonging to a cluster
        :type cluster: int or list(int)

        :returns: namedtuple(ResidencyTime) - tuple of total and active time
            dataframes
        """

        _cluster = listify(cluster)

        if len(_cluster) > 1 and not self.clusters_freq_coherent:
            raise ValueError('Cluster frequency is NOT coherent, '
                             'cannot compute residency!')

        freq_df = self.ftrace.cpu_frequency.data_frame
        cluster_freqs = freq_df[freq_df.cpu == _cluster[0]]

        # Compute TOTAL Time
        time_intervals = cluster_freqs.index[1:] - cluster_freqs.index[:-1]
        total_time = pd.DataFrame({
            'time': time_intervals,
            # TODO: LISA divides f by 1000.0, I dunno why
            'frequency': [f for f in cluster_freqs.iloc[:-1].frequency]
        })
        total_time = total_time.groupby(['frequency']).sum()

        print _cluster
        # Compute ACTIVE Time
        cluster_active = self.analyzer.idle.signal.cluster_active(_cluster)
        print cluster_active

        # In order to compute the active time spent at each frequency we
        # multiply 2 square waves:
        # - cluster_active, a square wave of the form:
        #     cluster_active[t] == 1 if at least one CPU is reported to be
        #                            non-idle by CPUFreq at time t
        #     cluster_active[t] == 0 otherwise
        # - freq_active, square wave of the form:
        #     freq_active[t] == 1 if at time t the frequency is f
        #     freq_active[t] == 0 otherwise
        available_freqs = sorted(cluster_freqs.frequency.unique())
        cluster_freqs = cluster_freqs.join(
            cluster_active, how='outer')
        cluster_freqs.fillna(method='ffill', inplace=True)
        nonidle_time = []
        for f in available_freqs:
            freq_active = cluster_freqs['frequency'] == f

            active_t = cluster_freqs.active * freq_active
            print active_t
            # Compute total time by integrating the square wave
            nonidle_time.append(integrate_square_wave(active_t))

        active_time = pd.DataFrame({'time': nonidle_time},
                                   # TODO: LISA divides f by 1000.0, I dunno why
                                   index=[f for f in available_freqs])
        active_time.index.name = 'frequency'

        return pd.concat([total_time, active_time], keys=['total', 'active'])
