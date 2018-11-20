#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup.py

# Copyright (c) 2018, Richard Gerum, Achim Schilling, Hinrich Rahlfs, Matthias Streb
#
# This file is part of ASR-Setup.
#
# ASR-Setup is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ASR-Setup is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ASR-Setup. If not, see <http://www.gnu.org/licenses/>

from setuptools import setup


setup(name='open_gpias',
      version="0.9.0",
      description='Open GPIAS to measure startle responses',
      url='https://bitbucket.org/randrian/asr_setup',
      license="GPLv3",
      author='Hinrich Rahlfs, Matthias Streb, Achim Schilling, Richard Gerum',
      author_email='richard.gerum@fau.de',
      packages=['open_gpias'],
      entry_points={
              'console_scripts': ['open_gpias=open_gpias.mainWindow:main'],
              'gui_scripts': ['open_gpias_gui=open_gpias.mainWindow:main'],
          },
      #setup_requires=['numpy'],
      install_requires=['sounddevice',
                        'scipy',
                        'matplotlib',
                        'qtpy',
                        'PyDAQmx',
                        'pandas'],
      include_package_data=True)
