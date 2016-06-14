#!/bin/bash
#
# sets the PATH variable properly to make all scripts accessible.
# Copyright (C) 2015 Michael F. Herbst
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# A copy of the GNU General Public License can be found in the 
# file LICENCE or at <http://www.gnu.org/licenses/>.

#DIR where this file is saved:
_dreuwBin_DIR=`dirname ${BASH_SOURCE[0]}`

for extra in . queuing_system qchem; do
	export PATH="$PATH:$_dreuwBin_DIR/$extra"
done

for extra in .; do
	export PYTHONPATH="$PYTHONPATH:$_dreuwBin_DIR/$extra"
done

unset _dreuwBin_DIR
