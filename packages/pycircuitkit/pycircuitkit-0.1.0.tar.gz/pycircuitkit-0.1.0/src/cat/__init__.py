"""Top-level package exports for CAT (PyCircuitKit).

Exposes frequently used types and helpers, plus package version.
"""

from importlib.metadata import PackageNotFoundError, version

# Package version
try:  # pragma: no cover - metadata resolution may vary in editable installs
    __version__ = version("pycircuitkit")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

# Top-level convenient API imports

# Core building blocks
# Analyses and utilities
from .analysis import (
    AC,
    DC,
    OP,
    TRAN,
    AnalysisResult,
    Dist,
    LogNormalPct,
    MonteCarloResult,
    NormalPct,
    ParamGrid,
    StepNativeResult,
    StepResult,
    SweepResult,
    TriangularPct,
    UniformAbs,
    UniformPct,
    WorstCaseResult,
    ac_gain_phase,
    bandwidth_3db,
    bode,
    crossover_freq_0db,
    gain_db_from_traces,
    gain_margin_db,
    monte_carlo,
    overshoot_pct,
    peak,
    phase_crossover_freq,
    phase_margin,
    run_ac,
    run_op,
    run_step_native,
    run_tran,
    settling_time,
    stack_runs_to_df,
    stack_step_to_df,
    step_grid,
    step_param,
    sweep_component,
    worst_case,
)

# Plotting
from .analysis.viz.plot import (
    plot_bode,
    plot_sweep_df,
    plot_traces,
)
from .core.circuit import Circuit
from .core.components import (
    CCCS,
    CCVS,
    IA,
    IP,
    IPWL,
    IPWL_T,
    ISIN,
    ISIN_T,
    VA,
    VCCS,
    VCVS,
    VP,
    VPWL,
    VPWL_T,
    VSIN,
    VSIN_T,
    C,
    Capacitor,
    Diode,
    F,
    G,
    H,
    I,
    Iac,
    Idc,
    Inductor,
    Ipulse,
    Ipwl,
    L,
    OpAmpIdeal,
    R,
    Resistor,
    V,
    Vdc,
    Vpulse,
    Vpwl,
)
from .core.net import GND, Net
from .utils.topologies import opamp_buffer, opamp_inverting

__all__ = [
    "__version__",
    # Core
    "Circuit",
    "Net",
    "GND",
    "Resistor",
    "Capacitor",
    "Vpulse",
    "Ipulse",
    "Vpwl",
    "Ipwl",
    "Inductor",
    "Vdc",
    "VA",
    "VP",
    "VSIN",
    "ISIN",
    "VPWL",
    "IPWL",
    "OpAmpIdeal",
    "OA",
    "Diode",
    "D",
    "VCVS",
    "VCCS",
    "CCCS",
    "CCVS",
    "E",
    "G",
    "F",
    "H",
    "R",
    "C",
    "V",
    "L",
    "Idc",
    "Iac",
    "I",
    "IA",
    "IP",
    # Analyses
    "OP",
    "TRAN",
    "AC",
    "DC",
    "AnalysisResult",
    # Sweeps/Steps
    "SweepResult",
    "sweep_component",
    "ParamGrid",
    "StepResult",
    "step_param",
    "step_grid",
    "stack_step_to_df",
    "stack_runs_to_df",
    # Metrics
    "peak",
    "settling_time",
    "overshoot_pct",
    "gain_db_from_traces",
    "bandwidth_3db",
    "ac_gain_phase",
    "crossover_freq_0db",
    "phase_margin",
    "phase_crossover_freq",
    "gain_margin_db",
    # Monte Carlo / Worst case
    "Dist",
    "NormalPct",
    "UniformPct",
    "LogNormalPct",
    "TriangularPct",
    "UniformAbs",
    "MonteCarloResult",
    "monte_carlo",
    "WorstCaseResult",
    "worst_case",
    "StepNativeResult",
    "run_step_native",
    # Plotting
    "plot_traces",
    "plot_bode",
    "plot_sweep_df",
    # High-level helpers
    "run_op",
    "run_tran",
    "run_ac",
    "bode",
]

# Typed source helpers (also export for convenience)
__all__ += [
    "VSIN_T",
    "ISIN_T",
    "VPWL_T",
    "IPWL_T",
]

# Topology helpers
__all__ += [
    "opamp_buffer",
    "opamp_inverting",
]
