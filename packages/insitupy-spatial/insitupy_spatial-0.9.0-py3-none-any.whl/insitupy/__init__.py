__author__ = "Johannes Wirth"
__email__ = "j.wirth@tum.de"
__version__ = "0.9.0"

# check if napari is available
try:
    import napari
    WITH_NAPARI = True
except ImportError:
    WITH_NAPARI = False

from . import _core, dataclasses, datasets, experiment
from . import images as im
from . import io
from . import plotting as pl
from . import preprocessing as pp
from . import tools as tl
from . import utils
from ._constants import CACHE
from ._core.data import InSituData
from .experiment.data import InSituExperiment

__all__ = [
    "InSituData",
    "InSituExperiment",
    "CustomPalettes",
    "AnnotationsData",
    "BoundariesData",
    "CellData",
    "ImageData",
    "MultiCellData",
    "RegionsData",
    "read_xenium",
    "differential_gene_expression",
    "calc_distance_of_cells_from",
    "register_images",
    "im",
    "io",
    "pl",
    "pp",
    "tl",
    "utils"
]