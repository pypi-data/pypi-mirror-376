3D Density Reconstruction from 2D Column Density
=================================================

This project provides Python functions to reconstruct a 3D density distribution from a 2D column density map using a multi-scale decomposition approach based on constrained diffusion. This method is particularly useful in astrophysics for analyzing gas and dust distributions.

Features
--------

- **compute_mean_density_width(column_density, dx)**: Derives the mean density and characteristic widths from a column density map.
- **density_reconstruction_3d(data_in, dx)**: The main function to perform the full 3D density reconstruction from a 2D column density map.

Installation
------------

To use this code, you need to install the following Python packages:

- numpy
- scipy
- matplotlib
- astropy
- constrained-diffusion (This is the cdd module used for the core decomposition.)

You can install these using pip:

.. code-block:: bash

    pip install numpy scipy matplotlib astropy
    pip install constrained-diffusion

If constrained-diffusion is a custom package, clone and install it from its repository:

.. code-block:: bash

    git clone https://github.com/gxli/Volume-Density-Mapper
    cd Volume-Density-Mapper
    pip install .


or 
    
.. code-block:: bash

    pip install -i https://test.pypi.org/simple/ volume-density-mapper==0.1.0


or 
    
.. code-block:: bash

    pip install volume-density-mapper==0.1.0



Example Usage
-------------

This example demonstrates how to:

- Estimate characteristic widths and mean density using compute_mean_density_width.
- Construct a 3D density cube using density_reconstruction_3d.

.. code-block:: python

    #!/usr/bin/env python
    # coding: utf-8

    import matplotlib.pyplot as plt
    import numpy as np
    from astropy.io import fits
    from volume_density_mapper import *

    # --- Load Data and Define Constants ---
    nh = fits.getdata('IC348_nh.fits')
    header = fits.getheader('IC348_nh.fits')
    mh2 = 1.34 * 3.34e-24  # Mass of H2 molecule in g
    pc = 3.08e18           # Parsec in cm
    dx = header['CDELT2'] / 180 * np.pi * 270 * pc  # Pixel size in cm

    # --- Compute Mean Density and Width ---
    input_map = nh * mh2
    density, width = compute_mean_density_width(input_map, dx)

    # --- Reconstruct 3D Density Structure ---
    data3d = density_reconstruction_3d(input_map, dx)

    print(np.shape(data3d))



Example
-------

.. code-block:: python


    import matplotlib.pyplot as plt
    import matplotlib as mpl
    from matplotlib import cm
    import numpy as np
    from astropy.io import fits
    from astropy import constants as cons
    from volume_density_mapper import *



    nh = fits.getdata('IC348_nh.fits')
    header = fits.getheader('IC348_nh.fits')
    mh2 = 1.34*3.34e-24
    pc = 3.08e18

    plt.figure(dpi = 100)
    plt.imshow(np.log10(nh * mh2), origin = 'lower')


.. image:: example/example_files/0.jpg
    :alt: Alternative text for the image
    :width: 600px
    :height: 400px
    :scale: 50%
    :align: center


.. code-block:: python

    plt.colorbar(label=r'Log(surface density ($\rm g cm^{-2}$))')



    # charactersitic scale (width) measurements
    input_map = nh.copy() * mh2
    dx = header['CDELT2']/180*np.pi*270 * pc
    #pixel size, the same unit with that of output
    density, width = compute_mean_density_width(input_map, dx)

    plt.figure(dpi = 100)
    plt.imshow(np.log10(density), origin = 'lower')
    plt.colorbar(label = r'log(Volume Density (r$g\;cm^{-3}$))')


    plt.figure(dpi = 100)
    plt.imshow(np.log10(width), origin = 'lower',cmap = 'magma')
    plt.colorbar(label = r'log(width (cm))')

    plt.show()

.. image:: example/example_files/1.jpg
    :alt: Alternative text for the image
    :width: 600px
    :height: 400px
    :scale: 50%
    :align: center

.. image:: example/example_files/2.jpg
    :alt: Alternative text for the image
    :width: 600px
    :height: 400px
    :scale: 50%
    :align: center




.. code-block:: python

    # restructure the density structure in 3D space

    data_in = nh * mh2 # convert to cgs unit 
    dx = header['CDELT2']/180*np.pi*270 * pc #pixel size, unit as cm (cgs unit)
    data3d = density_reconstruction_3d(data_in, dx)

    print(np.shape(data3d))

License
-------

This project is open-source and available under the MIT License.