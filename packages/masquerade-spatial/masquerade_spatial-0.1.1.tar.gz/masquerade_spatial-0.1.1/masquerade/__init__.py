"""
Masquerade: A Python package for spatial image analysis and mask generation.

This package provides tools for processing spatial imaging data, generating masks
from spatial coordinates, and working with multi-channel TIFF files commonly used
in spatial biology and microscopy applications.
"""

__version__ = "0.1.1"
__author__ = "Eduardo Esteva"
__email__ = "Eduardo.Esteva@nyulangone.org"
__description__ = "Spatial image analysis and mask generation for microscopy data"

from .masquerade import Masquerade

__all__ = ["Masquerade"]
