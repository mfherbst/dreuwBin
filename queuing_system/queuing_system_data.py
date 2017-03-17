# vi: set et ts=4 sw=4 sts=4:

# Module to hold all data relevant for a queuing system
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

from collections.abc import Iterable
from argparse import ArgumentParser
import shared_utils_lib as utils
import re

class send_email_on:
    def __init__(self,begin=None,end=None,error=None):
        self.begin=begin #bool send mail after job begins
        self.end=end #bool send mail after job end
        self.error=error #bool send mail on job error

    @property
    def begin(self):
        """Send mail after job begins"""
        return self.__begin

    @begin.setter
    def begin(self, val):
        if (val is None):
            self.__begin = None
            return 

        print(type(val))
        if (type(val) != bool):
            raise TypeError("begin is a bool or None")
        self.__begin = val

    @property
    def end(self):
        """Send mail after job ends"""
        return self.__end

    @end.setter
    def end(self, val):
        if (val is None):
            self.__end = None
            return 

        if (type(val) != bool):
            raise TypeError("end is a bool or None")
        self.__end = val

    @property
    def error(self):
        """Send mail when job has an error"""
        return self.__error

    @error.setter
    def error(self, val):
        if (val is None):
            self.__error = None
            return 

        if (type(val) != bool):
            raise TypeError("error is a bool or None")
        self.__error = val

class node_type:
    #TODO add properties

    def __init__(self):
        self.name=None #str
        self.count=1 #int how many of this type do we want
        self.no_procs=1 #int: number of processors
        self.extra_features=list() #list of str

    def add_extra_features(self,features):
        if isinstance(features,str):
            self.extra_features.append(features)

        if isinstance(feature,Iterable):
            for feat in features:
                if not isinstance(features,str):
                    raise TypeError("features contains non-strings")

            for feat in features:
                self.extra_features.append(feat)

        raise ValueError("feature is not a string or a list of strings")


    #TODO have no setter for extra_features

class queuing_system_data:
    #TODO add properties
    def __init__(self):
        self.job_name=None #str
        self.merge_stdout_stderr=None #bool
        self.walltime=None #int: seconds
        self.queue_name=None #str: queue@server to run job at
        self.physical_memory=None #int: amount of physical memory in bytes (i.e. working set memory)
        self.virtual_memory=None #int: amount of virtual memory in bytes (i.e including swap and so on)
        self.nodes=[] #list of node_type
        self.email=None #str: user email address for mail
        self.send_email_on=send_email_on()
        self.priority=None #int: between -1024 and +1023

    def no_procs(self):
        """Return the total number of processors on all nodes"""
        cnt=0
        for node in self.nodes:
            cnt+=node.count*node.no_procs
        return cnt

    def no_nodes(self):
        """Return the total number of nodes"""
        cnt=0
        for node in self.nodes:
            cnt+=node.count
        return cnt

    def add_node_type(self,ntype):
        """Add a node type"""
        if not isinstance(ntype,node_type):
            raise TypeError("ntype is not of type node_type")
        self.nodes.append(ntype)

    def todict(self):
        return vars(self)

    def __str__(self):
       return str(self.todict())

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

