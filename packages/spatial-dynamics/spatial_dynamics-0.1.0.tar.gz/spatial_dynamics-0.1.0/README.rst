Spatial Dynamics
================

A Python package for spatial dynamics analysis of cell neighborhoods in
biological data.

Overview
--------

Spatial Dynamics provides tools to analyze spatial relationships between
different cell types using: - N-simplex neighborhood analysis for
multi-cell-type interactions - Pairwise log-odds calculations for cell
type co-occurrence - Kolmogorov-Smirnov effect size calculations for
statistical validation

Features
--------

- **Scalable Analysis**: Handles large datasets through intelligent data
  blocking
- **Statistical Validation**: Built-in Kolmogorov-Smirnov testing
  against random distributions
- **Flexible Distance Metrics**: Configurable minimum and maximum
  interaction distances
- **Multiple Output Formats**: Neighbor counts, probabilities, log-odds,
  and effect sizes

Installation
------------

.. code:: bash

   pip install spatial-dynamics

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   git clone https://github.com/e-esteva/spatial-dynamics.git
   cd spatial-dynamics
   pip install -e ".[dev]"

Quick Start
-----------

.. code:: python

   import pandas as pd
   from spatial_dynamics import n_wise_logOdds, pairwise_logOdds

   # Load your spatial data (must have 'x', 'y', and 'cluster' columns)
   spatial_data = pd.read_csv('your_spatial_data.csv')

   # Pairwise analysis
   log_odds_matrix = pairwise_logOdds(
       spatial_obj=spatial_data,
       out_dir='./results',
       label='sample1',
       resolution=0.3774,  # spatial resolution
       p1=3,              # minimum distance
       p2=30,             # maximum distance
       compute_effect_size=True
   )

   # N-simplex analysis for specific cell types
   target_celltypes = ['TypeA', 'TypeB', 'TypeC']
   neighbor_matrix, global_log_odds = n_wise_logOdds(
       spatial_obj=spatial_data,
       out_dir='./results',
       label='sample1_simplex',
       target_celltypes=target_celltypes,
       compute_effect_size=True
   )

Parameters
----------

Common Parameters
~~~~~~~~~~~~~~~~~

- ``spatial_obj``: DataFrame with columns [‘x’, ‘y’, ‘cluster’]
- ``out_dir``: Output directory for results
- ``label``: Label for output files
- ``resolution``: Spatial resolution (default: 0.3774)
- ``p1``: Minimum interaction distance (default: 3)
- ``p2``: Maximum interaction distance (default: 30)
- ``compute_effect_size``: Whether to compute Kolmogorov-Smirnov effect
  sizes (default: False)

N-simplex Specific Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``target_celltypes``: List of cell types to analyze (default: all
  types)

Output Files
------------

The package generates several CSV files:

1. ``*-logOdds_matrix.csv``: Log-odds ratios between cell types
2. ``*-probabilities_matrix.csv``: Interaction probabilities
3. ``*-KS-effect_sizes_matrix.csv``: Effect sizes (if
   ``compute_effect_size=True``)

Algorithm Details
-----------------

Data Blocking Strategy
~~~~~~~~~~~~~~~~~~~~~~

For large datasets (>10,000 or >1,000 cells when computing effect
sizes), the algorithm automatically partitions data into blocks to
manage memory usage while maintaining statistical accuracy.

Distance Calculations
~~~~~~~~~~~~~~~~~~~~~

Spatial relationships are calculated using Euclidean distance with
configurable minimum (p1) and maximum (p2) thresholds to define
neighborhood boundaries.

Statistical Validation
~~~~~~~~~~~~~~~~~~~~~~

When ``compute_effect_size=True``, the algorithm compares observed
distance distributions against random spatial arrangements using the
Kolmogorov-Smirnov test.

Requirements
------------

- Python ≥ 3.8
- NumPy ≥ 1.21.0
- Pandas ≥ 1.3.0
- SciPy ≥ 1.7.0

Contributing
------------

1. Fork the repository
2. Create a feature branch (``git checkout -b feature/amazing-feature``)
3. Commit your changes (``git commit -m 'Add amazing feature'``)
4. Push to the branch (``git push origin feature/amazing-feature``)
5. Open a Pull Request

License
-------

This project is licensed under the MIT License - see the
`LICENSE <LICENSE>`__ file for details.

Citation
--------

If you use this package in your research, please cite:

.. code:: bibtex

   @software{spatial_dynamics,
     title={Spatial Dynamics: A Python Package for Cell Neighborhood Analysis},
     author={Eduardo Esteva},
     url={https://github.com/e-esteva/spatial-dynamics},
     year={2024}
   }
