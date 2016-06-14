# vi: set et ts=4 sw=4 sts=4:

# Python module to hold the shell environment relevant to writing
# job scripts
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

class queuing_system_environment:
    def __init__(self):
        self.submit_host=None #str; shell environment var giving the host where job has been submitted.
        self.submit_server=None #str; shell environment var giving the server to which job has been submitted
        self.submit_queue=None #str; shell environment var giving the queue to which job was submitted
        self.submit_workdir=None #str; shell environment var giving the working dir of the submission command
        self.jobid=None #str; shell environment var giving the jobid
        self.jobname=None #str; shell environment var giving the jobname
        self.queue=None #str; shell environment var giving the queue where job is executed
        self.path=None #str; shell environment var giving the content of the original PATH variable
        self.home=None #str; shell environment var giving the content of the original HOME variable
        self.nodes=None #str; shell environment var giving the nodes on which this job is executed
#TODO properties


