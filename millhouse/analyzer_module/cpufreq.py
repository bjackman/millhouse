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

class CpufreqAnalyzerModule(AnalyzerModule):
    required_events = ['cpu_frequency']

    def __init__(self, *args, **kwargs):
        super(CpufreqAnalyzerModule, self).__init__(*args, **kwargs)

        self.freq_domains = self.analyzer.cpufreq_domains
        self.frequencies_coherent = None
        self.sanitize_trace_events()

    def sanitize_trace_events(self):
        """
        Verify that all reported frequency domains are frequency coherent
        """
        if 'cpu_frequency_devlib' in self.available_events:
            self._inject_devlib_events()

        # Frequency Coherency Check
        if self.freq_domains:
            df = self.analyzer.get_trace_event('cpu_frequency')
            self.frequencies_coherent = True
            for cpus in self.freq_domains:
                domain_df = df[df.cpu.isin(cpus)]
                for chunk in self._chunker(domain_df, len(cpus)):
                    f = chunk.iloc[0].frequency
                    if any(chunk.frequency != f):
                        self.frequencies_coherent = False


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
        # TODO: We can only do this if we know the frequency domains.
        if not self.freq_domains:
            return None

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

                # Frequencies injection is done on a per-domain basis.
                # This is based on the assumption that domains are
                # frequency choerent.
                # For each domain we inject devlib events only if
                # these events do not overlaps with OS-generated ones.

                # Inject "initial" devlib frequencies
                os_df = df
                dl_df = devlib_freq.iloc[:len(self.cpus)]
                for c in self.freq_domains:
                    dl_freqs = dl_df[dl_df.cpu.isin(c)]
                    os_freqs = os_df[os_df.cpu.isin(c)]
                    # All devlib events "before" os-generated events
                    if os_freqs.empty or \
                    os_freqs.index.min() > dl_freqs.index.max():
                        df = pd.concat([dl_freqs, df])

                # Inject "final" devlib frequencies
                os_df = df
                dl_df = devlib_freq.iloc[len(self.cpus):]
                for c in self.freq_domains:
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
        df = self._do_pivot(self.ftrace.cpu_frequency.data_frame,
                            'cpu')['frequency'].ffill()

        return self._add_cpu_columns(self._extrude_signal(df))

    def _dfg_stats_frequency_residency(self):
        # If we don't have frequency domain data, just treat each CPU
        # individually.
        domains = self.freq_domains or [[c] for c in self.cpus]
        return pd.concat(
            [self._get_freq_residency(d) for d in domains],
            keys=[d[0] for d in domains], axis=1)

    @requires_events(['cpu_idle', 'cpu_frequency'])
    def _get_freq_residency(self, core_group):
        """
        Get a DataFrame with per core-group frequency residency, i.e. amount of
        time spent at a given frequency in each group.

        :param core_group: this can be either a single CPU ID or a list of CPU IDs
            belonging to a group
        :type group: int or list(int)

        :returns: namedtuple(ResidencyTime) - tuple of total and active time
            dataframes
        """

        _group = listify(core_group)

        if len(_group) > 1 and not self.frequencies_coherent:
            raise ValueError('Frequency is NOT domain-coherent, '
                             'cannot compute residency!')

        freq_df = self.ftrace.cpu_frequency.data_frame
        group_freqs = freq_df[freq_df.cpu == _group[0]]

        group_active = self.analyzer.idle.signal.cluster_active(_group)

        # In order to compute the active time spent at each frequency we
        # multiply 2 square waves:
        #
        # - cluster_active, a square wave of the form:
        #     cluster_active[t] == 1 if at least one CPU is reported to be
        #                            non-idle by CPUFreq at time t
        #     cluster_active[t] == 0 otherwise
        # - freq_active, square wave of the form:
        #     freq_active[t] == 1 if at time t the frequency is f
        #     freq_active[t] == 0 otherwise
        #
        # For the total time, we just treat the active signal as always-1

        available_freqs = sorted(group_freqs.frequency.unique())
        group_freqs = group_freqs.join(
            group_active, how='outer')
        group_freqs.fillna(method='ffill', inplace=True)
        total_time = []
        nonidle_time = []
        for f in available_freqs:
            freq_active = group_freqs['frequency'] == f
            active_t = group_freqs.active * freq_active

            # Compute total time by integrating the square wave
            nonidle_time.append(integrate_square_wave(active_t))
            total_time.append(integrate_square_wave(freq_active))

        df = pd.DataFrame({'total': total_time, 'active': nonidle_time},
                          index=[f for f in available_freqs])
        df.index.name = 'frequency'
        return df
