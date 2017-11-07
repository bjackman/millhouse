.. Millhouse documentation master file, created by
   sphinx-quickstart on Tue Nov  7 13:41:31 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Millhouse: Canned ftrace analyses based on TRAPpy
=================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

This library provides a layer on top of the kernel trace-parsing library
TRAPpy. While TRAPpy is intended mainly for converting trace objects into Pandas
DataFrames, this library provides ready-made manipulations which can more
readily be translated into actionable metrics.

For example, TRAPpy directly exposes the information from ftrace's
"cpu_frequency" trace events as a Pandas DataFrame, like so:

   >>> import trappy
   >>> ftrace = trappy.FTrace('path/to/trace.dat')
   >>> ftrace.cpu_frequency.data_frame.head()
            __comm  __cpu  __line  __pid  cpu  frequency
    Time
    0.193239  sugov:0      0   15933   1247    0     533000
    0.193269  sugov:0      0   15941   1247    1     533000
    0.193269  sugov:0      0   15942   1247    2     533000
    0.193270  sugov:0      0   15943   1247    3     533000
    0.298908  sugov:4      4   20257   1252    4     903000

While this library provides a more convenient representation of the same data:

    >>> import millhouse
    >>> analyzer = millhouse.TraceAnalyzer(ftrace)
    >>> analyzer.cpufreq.signal.cpu_frequency()[[0, 1, 2, 3]].head()
    cpu              0         1         2         3
    Time
    0.193239  533000.0       NaN       NaN       NaN
    0.193269  533000.0  533000.0  533000.0       NaN
    0.193270  533000.0  533000.0  533000.0  533000.0
    0.298908  533000.0  533000.0  533000.0  533000.0
    0.298919  533000.0  533000.0  533000.0  533000.0

And also a ready-made helper for finding the residency of CPU frequencies for
given CPUs or groups of CPUs:

    >>> analyzer.cpufreq.stats.frequency_residency(0)
                active     total
    frequency
    533000     0.005428  0.361603
    999000     0.015519  0.526832
    1844000    0.037929  0.301168

The benefit of having this analysis in a library not only consolidates code
where analyses are non-trivial, but also consolidates the avoidance of common
pitfalls for analyses that do seem trivial.

This library also consolidates post-processing that needs to be done on the
trace in order to perform anlysis, but that requires semantic knowledge that
does not belong in TRAPpy. For instance, it is aware of the events injected by
the devlib library to ensure that CPU frequencies are always available in a
trace.

To use this library, you need to construct a TRAPpy ``FTrace`` object, use it to
construct a :class:`TraceAnalyzer`, and then simply call the provided DataFrame
accessors.

DataFrame accessors are doubly grouped - firstly by the area of kernel behaviour
to which they pertain (one such group is 'cpufreq'), and secondly by the kind of
data represented by the returned DataFrame. These kinds of data are:

- *signal*: In these DataFrames, a row represents a snapshot of a value (or, if
  the DataFrame has multiple columns, a cross-section of several
  values). :attr:`TraceAnalyzer.cpufreq.signal.cpu_frequency` is one such
  accessor: a row appears wherever the CPU frequency was set for one
  or more CPUs, and shows the frequency of each CPU from that point until the
  next event.

- *event*: In these DataFrames, a row represents an event that
  occurred. :attr:`TraceAnalyzer.idle.event.cpu_wakeup` is such an acessor: a
  row represents a moment where a CPU was woken - the 'cpu' column shows which
  CPU was woken in a given event.

- *stats*: These are higher-level analyses, and their format varies.

API documentation can be found below.

.. automodule:: millhouse.trace_analyzer
    :members:
    :undoc-members:

cpufreq analysis
-------------------------------------------

.. autoclass:: millhouse.analyzer_module.cpufreq.CpufreqAnalyzerModule

   .. method:: signal.cpu_frequency()

        Get a DataFrame showing the frequency of each CPU at each moment

        Columns are CPU IDs.

   .. method:: stats.frequency_residency(self, core_group)

        Get a DataFrame with per core-group frequency residency, i.e. amount of
        time spent at a given frequency in each group.

        Note that this currently only reports a value for frequencies that were
        observed in the trace.

        :param core_group: this can be either a single CPU ID or a list of CPU IDs
            belonging to a group
        :type group: int or list(int)

        :returns: namedtuple(ResidencyTime) - tuple of total and active time
            dataframes


cpuidle analysis
-------------------------------------------

.. autoclass:: millhouse.analyzer_module.cpuidle.IdleAnalyzerModule

   .. method:: signal.cpu_idle_state()

        Get a CPU signal showing the idle state of each CPU at each moment

   .. method:: signal.cpu_active()

        Get a CPU signal that shows whether a CPU was active (i.e. not idle)

   .. method:: signal.cluster_active(cluster)

        Get a signal for a reporting where any of a group of CPUs were active

        :param cluster: List of CPU IDs to get active signal for

   .. method:: event.cluster_active(cluster)

        Get a signal for a reporting where any of a group of CPUs were active

Internal Millhouse APIs
-----------------------

The following APIs are internal and unlikely needed for a user - they should
mainly be a reference for those who want to add functionality to the library.

.. automodule:: millhouse.analyzer_module
    :members:
    :undoc-members:
    :private-members:

.. automodule:: millhouse.utils
    :members:
    :undoc-members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
