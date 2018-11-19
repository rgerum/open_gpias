Installation
============

Open GPIAS can be installed in different ways, you can choose the one which is the most comfortable for you and the
operating system you are using.

Windows Installer
~~~~~~~~~~~~~~~~~

If you have no Python installation and just want to get started, our installer is the best option for you. Just download
and execute the following installer:

`Download: Installer <https://bitbucket.org/randrian/open_gpias/downloads/Open_GPIAS_Setup.exe>`_

This will install the miniconda environment, if it is not already installed and download the open_gpias conda package.

.. note::
    Open GPIAS will be by default installed in a new conda environment called `_app_own_environment_open_gpias`.

Python Packages
~~~~~~~~~~~~~~~

If you are already familiar with python and have a python installation, you can choose one of the following ways:

- If you are in a conda env: ``conda install -c conda-forge -c dlidstrom -c rgerum open_gpias`` (recomended)
- Or with ``python setup.py install``

We recommend the conda installation, as this should always be the newest version of Open GPIAS.

Developer Version
~~~~~~~~~~~~~~~~~

If you want to have Open GPIAS installed from the repository and be able to update to the newest changesets, you can
follow this guide. First of all you need to have mercurial installed (`Mercurial <https://www.mercurial-scm.org/>`_).
Then you can open a command line in the folder where you want to install Open GPIAS and run the following command:

    ``hg clone https://bitbucket.org/randrian/open_gpias``

To install the package with all dependencies, execute:

    ``python install_requirements_with_conda.py``

in the downloaded repository directory.
