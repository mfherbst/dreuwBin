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

from queuing_system.queuing_system_data import queuing_system_data, node_type
from argparse import ArgumentParser
import shared_utils_lib as utils
import re

class qsys_line:
    """
    Class to parse or build a QSYS line originating
    from an input file of another program
    """

    def __parse_to_key_value(line):
        # Normalise:
        line=re.sub("\W*=\W*","=", line)

        # Split at spaces:
        whitespace = line.strip().split()

        # Slit at equals
        kv_raw = [ a.split("=") for a in whitespace if "=" in a ]

        # Make key-value pairs:
        return { v[0].strip() : v[1].strip() for v in kv_raw if len(v) == 2 }

    def __init__(self,data):
        """Initialise with the data object to place the results"""
        if not isinstance(data,queuing_system_data):
            raise TypeError("data should be of type queuing_system_data")

        self.__data = data

    def parse_file(self, f, comment_chars=["#"], keywords=["QSYS"]):
        """File to parse and place the values in the data object,
           which was provided upon construction.
           Only values which are Null will not be set.

           All characters in a line before comment_char + keyword or
           comment_char + " " + keyword are ignored.

           string    The string to parse. Should not contain a newline char
           comment_chars    Comment characters to look for.
           keywords         Keywords to look for, which start a QSYS line.
        """
        for line in f:
            self.parse_line(line,comment_chars=comment_chars, keywords=keywords)

    def parse_line(self,string,comment_chars=["#"], keywords=["QSYS"]):
        """Parse the values contained in the given line of text
           and place the values into the data object, which was provided
           upon construction.
           Only values which are Null will not be set.

           All characters before comment_char + keyword or comment_char + " "
           + keyword are ignored.

           string    The string to parse. Should not contain a newline char
           comment_chars    Comment characters to look for.
           keywords         Keywords to look for, which start a QSYS line.
        """
        # Build the startstrings like "#QSYS", "# QSYS"
        startstrings = [ v for c in comment_chars for k in keywords for v in (c+k,c+' '+k) ]

        # Find a keyword in the line:
        start=-1
        for startstr in startstrings:
            start=string.find(startstr)
            if start >= 0:
                start = start + len(startstr)
                break
        if start == -1: return

        data=self.__data
        vals = qsys_line.__parse_to_key_value(string[start:])
        for k in vals:
            verror_string = ("Could not parse value \""+vals[k]
                + "\" of QSYS directive " + k 
                +". Check that you supplied something sensible.")
            ignore_string = ("Warning: Ignoring "+available_directives[k]
                + " (== " + vals[k] + ") "
                + "specified in input file "
                + "via \"QSYS "+k+"=\", "
                + "since already provided (probably via the commandline).")

            if not k in available_directives:
                print("Warning: Ignoring unknown QSYS directive " + k
                        + "( == " + vals[k] + ").")
                continue
            elif k == "wt":
                if data.walltime is None:
                    try:
                        data.walltime = \
                            utils.interpret_string_as_time_interval(vals[k])
                    except ArgumentParser:
                        raise ValueError(verror_string)
                else:
                    print(ignore_string)
            elif k == "np":
                if data.no_nodes() == 0:
                    try:
                        node = node_type()
                        node.no_procs = int(vals[k])
                        data.add_node_type(node)
                    except ValueError:
                        raise ValueError(verror_string)
                else:
                    print(ignore_string)
            elif k == "mem":
                if data.physical_memory is None:
                    try:
                        data.physical_memory = \
                            utils.interpret_string_as_file_size(vals[k])
                    except ArgumentParser:
                        raise ValueError(verror_string)
                else:
                    print(ignore_string)
            elif k == "vmem":
                if data.virtual_memory is None:
                    try:
                        data.virtual_memory = \
                            utils.interpret_string_as_file_size(vals[k])
                    except ArgumentParser:
                        raise ValueError(verror_string)
                else:
                    print(ignore_string)

"""
The dict mapping from a QSYS directive
to a short description what it does.
"""
available_directives = {
        "wt": "job walltime",
        "np": "number of processors",
        "mem": "physical memory",
        "vmem": "virtual memory",
        }

def print_available_directives(indention=4*" ", comment_chars=["#"], keywords=["QSYS"]):
    maxdir = max( len(k) for k in available_directives )
    maxlal = max( len(available_directives[k]) for k in available_directives )

    fmt = indention + "{0:4s} {1:<" + str(maxdir) + "s} = <value>     {2:" + \
            str(maxlal)+"s}\n"

    ret=""
    for k in available_directives:
        for c in comment_chars:
            for kw in keywords:
                ret += fmt.format(c + kw, k, available_directives[k])
    return ret
