import tacotiff
from osgeo import gdal

from tacomaker import datamodel
from tacomaker.create import create

if gdal.__version__ < "3.11":
    raise ImportError(
        f"GDAL version 3.11 or higher is required. Current version: {gdal.__version__}"
    )

__all__ = [
    "datamodel",
    "create",
    "edit",
]

__version__ = "0.1.0"
