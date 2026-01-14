"""
Solver Modules

This package contains solver implementations for different problem types
and optimization strategies (with/without machine learning).

Architecture:
- Base solver classes define common interfaces
- Problem-specific solvers (SCP, RW) implement the optimization logic
- ML-enhanced solvers integrate machine learning components
"""

from .scp_solver import SCPSolver
from .scp_ml_solver import SCPMLSolver
from .rw_solver import RWSolver
from .rw_ml_solver import RWMLSolver

__all__ = ['SCPSolver', 'SCPMLSolver', 'RWSolver', 'RWMLSolver']
