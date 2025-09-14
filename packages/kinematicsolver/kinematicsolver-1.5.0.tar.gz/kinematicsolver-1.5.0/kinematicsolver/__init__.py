# kinematicsolver/__init__.py

"""
KinematicSolver Package
A Python package to solve kinematics problems for uniform acceleration motion (UAM) and other types.
"""

# Package metadata
__version__ = "1.0.0"
__author__ = "Mahir Masudur Rahman"

# Import main solver functions/classes for easy access
from .kinematicsolvermethods import KinematicSolverUAM

# Optional: list what gets imported with `from kinematicsolver import *`
__all__ = ["KinematicSolverUAM"]