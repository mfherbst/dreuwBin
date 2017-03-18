# vi: set et ts=4 sw=4 sts=4:

# Module to hold all data relevant for a queuing system
# Copyright (C) 2017 Michael F. Herbst
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

from argparse import ArgumentParser
import shared_utils_lib as utils
import re

class qsys_line:
    """
    Class to parse or build a QSYS line originating
    from an input file of another program
    """
    def __parse_to_key_value(self,line):
        # Normalise:
        line=re.sub("\W*=\W*","=", line)

        # Split at spaces:
        whitespace = line.strip().split()

        # Slit at equals
        kv_raw = [ a.split("=") for a in whitespace if "=" in a ]

        # Make key-value pairs:
        return { v[0].strip() : v[1].strip() for v in kv_raw if len(v) == 2 }

    def __init__(self,line):
        """Initialise with the line to parse"""
        self.__vals = self.__parse_to_key_value(line)

    def __print_ignore(self,directive):
        print("Warning: Ignoring "+qsys_line.available_directives[directive]
                + " (== " + self.__vals[directive] + ") "
                + "specified in input file "
                + "via \"QSYS "+directive+"=\", "
                + "since already given on commandline or in input file.")

    def parse_into(self,data):
        """Place the values in this data object"""
        for k in self.__vals:
            verror_string = ("Could not parse value \""+self.__vals[k]
                + "\" of QSYS directive " + k 
                +". Check that you supplied something sensible.")

            if not k in qsys_line.available_directives:
                continue
            elif k == "wt":
                if data.walltime is None:
                    try:
                        data.walltime = \
                            utils.interpret_string_as_time_interval(self.__vals[k])
                    except ArgumentParser:
                        raise ValueError(verror_string)
                else:
                    self.__print_ignore(k)
            elif k == "np":
                if data.no_nodes() == 0:
                    try:
                        node = node_type()
                        node.no_procs = int(self.__vals[k])
                        data.add_node_type(node)
                    except ValueError:
                        raise ValueError(verror_string)
                else:
                    self.__print_ignore(k)
            else:
                raise ValueError("Unknown QSYS directive: \""+k+"\"")

    """
    The dict mapping from a QSYS directive
    to a short description what it does.
    """
    available_directives = {
            "wt": "job walltime",
            "np": "number of processors",
            }
