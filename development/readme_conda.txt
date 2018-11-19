Updating a version
==================

Raise version number in
    
    - setup.py
    - meta.yaml
    - docs/conf.py
    - clickpoints/__init__.py

Upload to PiPy
==============

ensure that twine is installed

    pip install twine

build the package and upload it

    python setup.py sdist
    twine upload dist/clickpoints-VERSION.tar.gz

Upload to Conda
===============
install anaconda-client and conda-build

    conda install anaconda-client conda-build -y
   
update those two packages

    conda update -n root conda-build
    conda update -n root anaconda-client
    
specify the login

    anaconda login --username rgerum --password *********
    
set autoupload to "yes"

    conda config --set anaconda_upload yes
    
build the package

    conda-build . -c conda-forge -c dlidstrom
