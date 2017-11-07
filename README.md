Millhouse: Canned ftrace analyses based on TRAPpy
---------

This library provides a layer on top of the kernel trace-parsing library
TRAPpy. While TRAPpy is intended mainly for converting trace objects into Pandas
DataFrames, this library provides ready-made manipulations which can more
readily be translated into actionable metrics.

This library can be installed via `pip`:

```
git clone git@github.com:bjackman/millhouse.git
pip install millhouse          # Installs dependencies automatically
```

More information and user documentation are available in the HTML documentation,
which can be built like so:

```
pip install sphinx-doc
git clone git@github.com:bjackman/millhouse.git
cd millhouse/doc/
make html
```

Development notes
-------------

The analyses are grouped into 'modules' (for example cpufreq and cpuidle) and
further by the type of the DataFrame they return (for example signal and event -
see the documentation for more info on this). Each module is implemented as a
subclass of `millhouse.AnalyzerModule`, and getters are added by implementing
methods with names of the form:

`<ModuleClass>_dfg_<kind>_<name>`

Which are converted into TraceAnalyzerAttributes of the form:

`TraceAnalyzer.<ModuleClass.name>.<kind>.name`

For example:

`IdleAnalyzerModule._dfg_signal_cpu_idle_state`

is exposed to the user as

`TraceAnalyzer.idle.signal.cpu_idle_state`.

Due to this name wrangling, these DataFrame accessors must be documented in the
.rst files under doc/, rather than directly via their Python docstrings.


Contributing
------------

GitHub pull requests are welcome. Please remember to add tests and documentation
(which may need to be added under the doc/ directory, not just in the Python
source). Please ensure you have the permission of your employer to contribute to
this Apache-licensed project.
