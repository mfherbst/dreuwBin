# vi: set et ts=4 sw=4 sts=4:

# Abstract python class for queuing system interaction
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

from abc import ABCMeta, abstractmethod
from queuing_system.queuing_system_data import queuing_system_data
import subprocess

class UnknownDataFieldException(Exception):
    """
    Exception thrown when parsing commandline or header
    finds an unknown field
    """
    def __init__(self,message):
        super(UnknownDataField, self).__init__(message)

class queuing_system_base(metaclass=ABCMeta):
    @abstractmethod
    def name(self):
        """
        Return the name of the queing system.
        """
        pass

    @abstractmethod
    def parse_commandline_args(self,cmdline):
        """
        Parse a commandline string and return a queuing_system_data object
        representing that string
        """
        pass

    @abstractmethod
    def build_commandline_args(self,data):
        """
        Build a commandline string that could be handed to the submit_command 
        from the data object and return it
        """
        pass

    @abstractmethod
    def parse_script_header(self,f):
        """
        Read a file object and extract queuing_system_data from the header
        for the queuing system
        """
        pass

    @abstractmethod
    def build_script_header(self,data):
        """
        Build a script header for a queuing system script from the data object
        and return the resulting strint (does not contain any shebang or so, just
        the plain queuing system directives)
        """
        pass

    def submit_script(self,filename):
        subprocess.check_call([ self.submit_command(), filename ])


    @abstractmethod
    def submit_command(self):
        """return the command for the queuing system with which new jobs can be started"""
        pass

    @abstractmethod
    def abort_command(self):
        """return the command for the queuing system with which jobs can be aborted"""
        pass

    def is_ready_for_submission(self,data):
        """
        return True if the data is valid, ie contains all required flags for the job to be
        submitted via the submit_command
        """
        return (self.why_not_ready_for_submission(data) == "")

    @abstractmethod
    def why_not_ready_for_submission(self,data):
        """
        return the reason as a string if the data is not valid, return an empty string if
        everything is fine
        """

    @abstractmethod
    def get_environment(self):
        """
        return a queuing_system_environment object with the values set appropriately for 
        this queuing_system
        """
        pass
        
