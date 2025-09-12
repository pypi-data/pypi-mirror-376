# ruff: noqa: F401
import logging
import warnings

from pandas.plotting import register_matplotlib_converters

import pastas.objective_functions as objfunc
import pastas.recharge as rch
import pastas.timeseries_utils as ts
from pastas import check, extensions, forecast, stats
from pastas.dataset import list_datasets, load_dataset
from pastas.decorators import set_use_numba
from pastas.model import Model
from pastas.noisemodels import ArmaModel, ArmaNoiseModel, ArNoiseModel, NoiseModel
from pastas.plotting import plots
from pastas.plotting.modelcompare import CompareModels
from pastas.plotting.plots import TrackSolve
from pastas.rcparams import rcParams
from pastas.rfunc import (
    DoubleExponential,
    Exponential,
    FourParam,
    Gamma,
    Hantush,
    HantushWellModel,
    Kraijenhoff,
    One,
    Polder,
    Spline,
)
from pastas.solver import EmceeSolve, LeastSquares, LmfitSolve
from pastas.stressmodels import (
    ChangeModel,
    Constant,
    LinearTrend,
    RechargeModel,
    StepModel,
    StressModel,
    TarsoModel,
    WellModel,
)
from pastas.timeseries import validate_oseries, validate_stress
from pastas.transform import ThresholdTransform
from pastas.utils import set_log_level
from pastas.version import __version__, show_versions


logger = logging.getLogger(__name__)

# Register matplotlib converters when using Pastas
# https://github.com/pastas/pastas/issues/92

register_matplotlib_converters()
