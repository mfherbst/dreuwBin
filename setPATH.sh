#!/bin/bash
#sets the PATH variable properly to make all scripts accessible.

#DIR where this file is saved:
_dreuwBin_DIR=`dirname ${BASH_SOURCE[0]}`

for extra in . queuing_system qchem; do
	export PATH="$PATH:$_dreuwBin_DIR/$extra"
done

for extra in .; do
	export PYTHONPATH="$PYTHONPATH:$_dreuwBin_DIR/$extra"
done

unset _dreuwBin_DIR
