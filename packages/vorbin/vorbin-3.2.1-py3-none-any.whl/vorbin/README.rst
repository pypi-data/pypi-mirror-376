
⚠️ **DEPRECATION NOTICE**  

``VorBin`` is **deprecated** and superseded by `PowerBin <https://pypi.org/project/powerbin/>`_.  
Please migrate to ``PowerBin``, which addresses ``VorBin``'s limitations.

The VorBin Package
==================

**VorBin: Adaptive Voronoi Binning of Two Dimensional Data**

.. image:: https://users.physics.ox.ac.uk/~cappellari/images/vorbin-logo.svg
    :target: https://users.physics.ox.ac.uk/~cappellari/software
    :width: 100
.. image:: https://img.shields.io/pypi/v/vorbin.svg
        :target: https://pypi.org/project/vorbin/
.. image:: https://img.shields.io/badge/arXiv-astroph:0302262-orange.svg
    :target: https://arxiv.org/abs/astro-ph/0302262
.. image:: https://img.shields.io/badge/DOI-10.1046/...-green.svg
        :target: https://doi.org/10.1046/j.1365-8711.2003.06541.x

This ``VorBin`` package is a Python implementation of the two-dimensional adaptive
spatial binning method of `Cappellari & Copin (2003) <https://ui.adsabs.harvard.edu/abs/2003MNRAS.342..345C>`_. 
It uses Voronoi tessellations to bin data to a given minimum signal-to-noise ratio.

.. contents:: :depth: 2

Attribution
-----------

If you use this software for your research, please cite
`Cappellari & Copin (2003) <https://ui.adsabs.harvard.edu/abs/2003MNRAS.342..345C>`_
The BibTeX entry for the paper is::

    @ARTICLE{Cappellari2003,
        author = {{Cappellari}, M. and {Copin}, Y.},
        title = "{Adaptive spatial binning of integral-field spectroscopic
            data using Voronoi tessellations}",
        journal = {MNRAS},
        eprint = {astro-ph/0302262},
        year = 2003,
        volume = 342,
        pages = {345-354},
        doi = {10.1046/j.1365-8711.2003.06541.x}
    }

Installation
------------

install with::

    pip install vorbin

Without writing access to the global ``site-packages`` directory, use::

    pip install --user vorbin

Usage Example
-------------

To learn how to use the package ``VorBin`` run
``voronoi_2d_binning_example.py`` in the ``vorbin/examples`` directory, within
the main package installation folder inside ``site-packages``, and read the
detailed documentation in the docstring of the file ``voronoi_2d_binning.py``,
on `PyPi <https://pypi.org/project/vorbin/>`_.

Perform the following simple steps to bin your own 2D data with minimal Python
interaction:

1. Write your data vectors [X, Y, Signal, Noise] in the text file
   ``voronoi_2d_binning_example.txt``, following the example provided;

2. Change the line ``targetSN = 50.0`` in the procedure
   ``voronoi_2d_binning_example.py``, to specify the desired target S/N of your
   final bins;

3. Run the program ``voronoi_2d_binning_example`` and wait for the final plot
   to appear. The output is saved in the text file
   ``voronoi_2d_binning_output.txt``. The last column BIN_NUM in the file is
   *all* that is needed to actually bin the data;

4. Read the documentation at the beginning of the file
   ``voronoi_2d_binning.py`` to fully understand the meaning of the various
   optional output parameters.

###########################################################################
