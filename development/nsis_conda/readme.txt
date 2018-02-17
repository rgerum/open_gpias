To build the installer, first install conda, if it is not already installed.
Then install the conda-execute package:

    conda install conda-execute --channel=conda-forge -y
    
and then execute the asr_setup_conda.nsi file:

    conda execute asr_setup_conda.nsi
