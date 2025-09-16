Masquerade: Spatial Image Analysis and Mask Generation
======================================================

|PyPI version| |Python Support| |License: MIT| |Tests|

Masquerade is a Python package designed for spatial image analysis and
mask generation from microscopy data. It specializes in processing
multi-channel TIFF files and generating spatial masks based on
clustering data, making it particularly useful for spatial biology and
microscopy applications.

🚀 Features
-----------

- **Multi-channel TIFF processing**: Read and process complex
  multi-channel TIFF files with biomarker annotations
- **Spatial mask generation**: Create circular masks (filled or
  outlined) based on spatial coordinates
- **Intelligent compression**: Automatic compression with configurable
  quality settings to meet size targets
- **Flexible coordinate handling**: Automatic coordinate adjustment and
  boundary condition management
- **Cluster-based analysis**: Process spatial data organized by clusters
  with customizable parameters
- **Memory efficient**: Optimized for handling large microscopy datasets
- **Command-line interface**: Both modern and legacy CLI options for
  easy integration
- **OME-TIFF support**: Export results in OME-compatible BigTIFF format

📦 Installation
---------------

From PyPI (recommended)
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   pip install masquerade-spatial

From source
~~~~~~~~~~~

.. code:: bash

   git clone https://github.com/e-esteva/masquerade.git
   cd masquerade-spatial
   pip install -e ".[dev]"

Requirements
~~~~~~~~~~~~

- Python ≥ 3.8
- NumPy, SciPy, Pandas
- scikit-image, tifffile, imagecodecs
- matplotlib, tqdm

🏃‍♂️ Quick Start
--------------

Python API
~~~~~~~~~~

.. code:: python

   from masquerade import Masquerade

   # Initialize the processor
   processor = Masquerade()

   # Configure parameters
   processor.image_source = "path/to/your/image.tiff"
   processor.spatial_anno = "path/to/spatial_annotations.csv"
   processor.radius = 15
   processor.filled = True
   processor.target_size = 4  # Target 4GB output

   # Process the image and generate masks
   image, subset_x, subset_y, metadata = processor.PreProcessImage()
   channels = processor.get_circle_masks(image, metadata, subset_x, subset_y)

   # Add continuous channels from original image
   channels, names = processor.get_continuous_channels(
       channels, subset_x, subset_y
   )

   # Save results as OME-BigTIFF
   Masquerade.write_ome_bigTiff(
       channels, "output_masks.tiff", list(channels.keys())
   )

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   # Modern CLI with named arguments
   masquerade input.tiff coordinates.csv output.tiff \
     --radius 15 \
     --compress \
     --target-size 2.5 \
     --filled \
     --verbose

   # Legacy CLI (for backward compatibility)
   masquerade-legacy input.tiff coords.csv output.tiff markers.csv \
     True False 10 True 100 False 4.0

📊 Input Data Format
--------------------

Spatial Annotations CSV
~~~~~~~~~~~~~~~~~~~~~~~

Your spatial annotations file should contain these columns: - ``x``: X
coordinates (pixels) - ``y``: Y coordinates (pixels) - ``cluster``:
Cluster identifiers

.. code:: csv

   x,y,cluster
   100,150,1
   102,148,1
   200,300,2
   205,295,2
   310,450,3

Multi-channel TIFF Files
~~~~~~~~~~~~~~~~~~~~~~~~

- Compatible with standard microscopy formats
- XML metadata with biomarker information
- Supports qpTIFF and similar formats
- Handles large files efficiently

Optional: Marker Metadata CSV
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Specify which markers to include in processing:

.. code:: csv

   x
   CD3
   CD4
   CD8
   Ki67

⚙️ Configuration Parameters
---------------------------

+----------------------+----------+---------------+-----------------------+
| Parameter            | Type     | Default       | Description           |
+======================+==========+===============+=======================+
| ``image_source``     | str      | ’’            | Path to input TIFF    |
|                      |          |               | file                  |
+----------------------+----------+---------------+-----------------------+
| ``spatial_anno``     | str      | ’’            | Path to CSV file with |
|                      |          |               | spatial annotations   |
+----------------------+----------+---------------+-----------------------+
| ``relevant_markers`` | str      | None          | Path to CSV with      |
|                      |          |               | markers to include    |
+----------------------+----------+---------------+-----------------------+
| ``target_size``      | float    | 4.0           | Target output size in |
|                      |          |               | GB                    |
+----------------------+----------+---------------+-----------------------+
| ``radius``           | int      | 10            | Radius for circular   |
|                      |          |               | masks (pixels)        |
+----------------------+----------+---------------+-----------------------+
| ``filled``           | bool     | True          | Generate filled       |
|                      |          |               | circles (True) or     |
|                      |          |               | outlines (False)      |
+----------------------+----------+---------------+-----------------------+
| ``num_points``       | int      | 100           | Number of points for  |
|                      |          |               | circle outlines       |
+----------------------+----------+---------------+-----------------------+
| ``adjust_coords``    | bool     | True          | Adjust coordinates to |
|                      |          |               | image bounds          |
+----------------------+----------+---------------+-----------------------+
| ``compress``         | bool     | False         | Enable intelligent    |
|                      |          |               | compression           |
+----------------------+----------+---------------+-----------------------+
| ``filter_img``       | bool     | False         | Apply filtering       |
|                      |          |               | during compression    |
+----------------------+----------+---------------+-----------------------+

🔧 Advanced Usage
-----------------

Working with Specific Markers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   processor = Masquerade()
   processor.relevant_markers = "important_markers.csv"
   processor.image_source = "large_image.tiff"

   # Only processes markers listed in the CSV
   channels, names = processor.get_continuous_channels({})

Intelligent Compression
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   processor = Masquerade()
   processor.compress = True
   processor.target_size = 2.0  # Target 2GB
   processor.filter_img = True  # Apply smoothing

   # Automatically calculates compression factor
   # to meet target size while preserving quality
   image, x, y, metadata = processor.PreProcessImage()
   channels = processor.get_circle_masks(image, metadata, x, y)

   # Compression factor available after processing
   print(f"Applied compression factor: {processor.compression_factor}")

Batch Processing
~~~~~~~~~~~~~~~~

.. code:: python

   import glob
   from pathlib import Path

   def process_batch(input_dir, output_dir):
       processor = Masquerade()
       processor.radius = 12
       processor.filled = True
       
       for tiff_file in glob.glob(f"{input_dir}/*.tiff"):
           base_name = Path(tiff_file).stem
           coord_file = f"{input_dir}/{base_name}_coords.csv"
           output_file = f"{output_dir}/{base_name}_masks.tiff"
           
           if Path(coord_file).exists():
               processor.image_source = tiff_file
               processor.spatial_anno = coord_file
               
               # Process
               image, x, y, metadata = processor.PreProcessImage()
               channels = processor.get_circle_masks(image, metadata, x, y)
               
               # Save
               Masquerade.write_ome_bigTiff(
                   channels, output_file, list(channels.keys())
               )
               print(f"Processed: {base_name}")

   # Usage
   process_batch("./input_images", "./output_masks")

🧪 API Reference
----------------

Core Methods
~~~~~~~~~~~~

``PreProcessImage()``
^^^^^^^^^^^^^^^^^^^^^

Loads and preprocesses the input image and spatial data. - **Returns**:
``(image, subset_x, subset_y, metadata)`` - **Side effects**: Sets
``raw_size`` attribute

``get_circle_masks(image, metadata, set_subset_x, set_subset_y)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Generates circular masks based on spatial coordinates. - **Parameters**:
- ``image``: Input image array - ``metadata``: Spatial annotations
DataFrame - ``set_subset_x/y``: Coordinate boundaries - **Returns**:
Dictionary of mask channels

``get_continuous_channels(channels, set_subset_x=None, set_subset_y=None)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extracts continuous channel data from TIFF files. - **Returns**:
``(channels_dict, channel_names_list)``

``compress_marker_channels(channels, spatial_metadata)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Applies compression and filtering to marker channels. - **Returns**:
``(compressed_channels, channel_names)``

Utility Methods
~~~~~~~~~~~~~~~

``generate_circle(x_center, y_center, radius, num_points=100)`` (static)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Generate coordinates for circle outline.

``generate_filled_circle(cx, cy, r)`` (static)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Generate coordinates for filled circle.

``writeMaskTiff(channels, outPath)`` (static)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Save channels as standard TIFF with ImageJ metadata.

``write_ome_bigTiff(channels, out, channels_to_keep)`` (static)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Save channels as OME-compatible BigTIFF.

🧪 Testing
----------

.. code:: bash

   # Run all tests
   pytest tests/

   # Run with coverage
   pytest tests/ --cov=masquerade --cov-report=html

   # Run specific test categories
   pytest tests/ -k "not skip"  # Skip integration tests requiring files
   pytest tests/test_masquerade.py::TestMasquerade -v  # Basic tests only

🤝 Contributing
---------------

We welcome contributions! Please see our `Contributing
Guide <CONTRIBUTING.md>`__ for details.

Development Setup
~~~~~~~~~~~~~~~~~

.. code:: bash

   # Clone the repository
   git clone https://github.com/e-esteva/masquerade.git
   cd masquerade-spatial

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install in development mode
   pip install -e ".[dev]"

   # Run tests
   pytest

   # Run code formatting
   black masquerade/ tests/
   isort masquerade/ tests/

Code Quality
~~~~~~~~~~~~

- Code formatting with ``black``
- Import sorting with ``isort``
- Type checking with ``mypy``
- Testing with ``pytest``

📄 License
----------

This project is licensed under the MIT License - see the
`LICENSE <LICENSE>`__ file for details.

📚 Citation
-----------

If you use Masquerade in your research, please cite:

.. code:: bibtex

   @software{masquerade_spatial,
     title = {Masquerade: Spatial Image Analysis and Mask Generation},
     author = {Your Name},
     url = {https://github.com/e-esteva/masquerade},
     version = {0.1.0},
     year = {2025},
     doi = {10.5281/zenodo.XXXXXXX}
   }

🔗 Links
--------

- **Documentation**: https://masquerade.readthedocs.io/
- **PyPI Package**: https://pypi.org/project/masquerade/
- **Issue Tracker**: https://github.com/e-esteva/masquerade/issues
- **Discussions**: https://github.com/e-esteva/masquerade/discussions

📈 Changelog
------------

v0.1.0 (2025-12-13)
~~~~~~~~~~~~~~~~~~~

- 🎉 Initial release
- ✨ Core mask generation functionality
- ✨ Multi-channel TIFF processing
- ✨ Spatial coordinate handling
- ✨ Compression and filtering options
- ✨ Command-line interface
- ✨ OME-BigTIFF export support
- 📚 Comprehensive documentation and tests

--------------

.. |PyPI version| image:: https://badge.fury.io/py/masquerade-spatial.svg
   :target: https://badge.fury.io/py/masquerade-spatial
.. |Python Support| image:: https://img.shields.io/pypi/pyversions/masquerade-spatial.svg
   :target: https://pypi.org/project/masquerade-spatial/
.. |License: MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
.. |Tests| image:: https://github.com/yourusername/masquerade-spatial/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/yourusername/masquerade-spatial/actions
