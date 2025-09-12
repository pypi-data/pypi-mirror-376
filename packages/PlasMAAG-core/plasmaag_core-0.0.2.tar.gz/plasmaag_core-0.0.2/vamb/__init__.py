"""Vamb - Variational Autoencoders for Metagenomic Binning
Documentation: https://github.com/RasmussenLab/vamb/
"""

# TODO: Pyhmmer is compiled with -funsafe-math-optimizations, which toggles some
# flag in the CPU controlling float subnormal behaviour.
# This causes a warning in NumPy.
# This is not an issue in Vamb (I think), so we silence the warning here as a
# temporary fix.
# See https://github.com/althonos/pyhmmer/issues/71
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="numpy")

from . import vambtools
from . import parsebam
from . import parsecontigs
from . import parsemarkers
from . import taxonomy
from . import cluster
# from . import cluster_contr_vamb
from . import encode
from . import aamb_encode
from . import semisupervised_encode
from . import hloss_misc
from . import taxvamb_encode
from . import reclustering

from importlib.metadata import version as get_version
from . import encode_n2v_asimetric
from . import git_commit
from loguru import logger

__version_str__ = get_version("PlasMAAG")
logger.remove()

__all__ = [
    "vambtools",
    "parsebam",
    "parsecontigs",
    "parsemarkers",
    "taxonomy",
    "cluster",
    "cluster_contr_vamb"
    "encode",
    "aamb_encode",
    "semisupervised_encode",
    "taxvamb_encode",
    "hloss_misc",
    "reclustering",
    "encode_n2v_asimetric",
    "git_commit"
]
