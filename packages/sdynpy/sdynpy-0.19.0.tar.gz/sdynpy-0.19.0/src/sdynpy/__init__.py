"""SDynPy: A Structural Dynamics Library for Python

Copyright 2022 National Technology & Engineering Solutions of Sandia,
LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
Government retains certain rights in this software.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from .core import coordinate, colors, array, geometry, shape, data, system, matrix_mod
from .fileio import unv, uff, rattlesnake, vic, tshaker, pdf3D, escdf
from .fem.sdynpy_exodus import Exodus, ExodusInMemory, read_sierra_matlab_map_file, read_sierra_matlab_matrix_file
from .fem import sdynpy_beam as beam
from .fem import sdynpy_shaker as shaker
from .fem import sdynpy_dof as dof
from .signal_processing import (frf, cpsd, integration, correlation, complex,
                                rotation, generator, camera, harmonic,
                                geometry_fitting, srs, lrm, frf_inverse, buffer)
from .modal import (PolyPy, SMAC, PolyPy_GUI, SMAC_GUI, compute_residues,
                    compute_shapes, SignalProcessingGUI, ColoredCMIF,
                    read_modal_fit_data, ModalTest)
from . import doc

# Pull things in for easier access
SdynpyArray = array.SdynpyArray
coordinate_array = coordinate.coordinate_array
CoordinateArray = coordinate.CoordinateArray
coordinate_system_array = geometry.coordinate_system_array
CoordinateSystemArray = geometry.CoordinateSystemArray
node_array = geometry.node_array
NodeArray = geometry.NodeArray
traceline_array = geometry.traceline_array
TracelineArray = geometry.TracelineArray
element_array = geometry.element_array
ElementArray = geometry.ElementArray
Geometry = geometry.Geometry
shape_array = shape.shape_array
ShapeArray = shape.ShapeArray
data_array = data.data_array
NDDataArray = data.NDDataArray
time_history_array = data.time_history_array
TimeHistoryArray = data.TimeHistoryArray
transfer_function_array = data.transfer_function_array
TransferFunctionArray = data.TransferFunctionArray
coherence_array = data.coherence_array
CoherenceArray = data.CoherenceArray
multiple_coherence_array = data.multiple_coherence_array
MultipleCoherenceArray = data.MultipleCoherenceArray
power_spectral_density_array = data.power_spectral_density_array
PowerSpectralDensityArray = data.PowerSpectralDensityArray
spectrum_array = data.spectrum_array
SpectrumArray = data.SpectrumArray
GUIPlot = data.GUIPlot
CPSDPlot = data.CPSDPlot
id_map = geometry.id_map
System = system.System
matrix_plot = correlation.matrix_plot
Matrix = matrix_mod.Matrix
matrix = matrix_mod.matrix
