# vi: set et ts=4 sw=4 sts=4:

# Python class to interact with a PBS queuing system
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

from queuing_system.queuing_system_base import queuing_system_base
from queuing_system import queuing_system_data as qd
from queuing_system import queuing_system_environment as qe
import platform
import re
import argparse

class pbs_time:
    def __init__(self,time):
        """
        initialise a pbs_time object either from the number of seconds
        or a pbs time string of the form

        [[hours:]minutes:]seconds[.milliseconds]

        where the milliseconds are ignored
        """

        if isinstance(time,int):
            # number of seconds
            self.__seconds = time
            return

        if isinstance(time,str):
            (timestr, ret, tail) = time.rpartition(".")
            if (timestr == ""):
                #no partitioning was possible
                timestr=tail

            li=timestr.split(":")

            try:
                self.__seconds = int(li[-1])
                if (len(li) > 1):
                    self.__seconds += 60*int(li[-2])

                if (len(li) > 2):
                    self.__seconds += 3600*int(li[-3])
            except ValueError:
                raise ValueError("Invalid time string: " + time)
            return

        raise TypeError("Cannot parse type " + type(time))

    @property
    def seconds(self):
        """return number of seconds represented by this object"""
        return self.__seconds

class pbs_size:
    def __init__(self,size,wordsize=None):
        """
        initialise a pbs_size object either from the number of bytes
        or a pbs size string of the form

        integer[suffix]

        where suffix is one of

        b or  w    bytes or words.
        kb or kw    Kilo (1024) bytes or words.
        mb or mw    Mega (1,048,576) bytes or words.
        gb or gw    Giga (1,073,741,824) bytes or words.

        If words are used and wordsize is None, the executing systems
        wordsize is used for the conversion.

        wordsize is either none or the number of bits in a word.
        (even though only multiples of 8 will be accepted)
        """

        # set wordsize (or autodetermine from os)
        self.wordsize = wordsize

        if isinstance(size,int):
            # number of seconds
            self.__bytes = size
            return

        if isinstance(size,str):
            # extract integer:
            match = re.match("^[0-9]*",size)
            if len(match.group()) < 1:
                raise ValueError("Invalid size string: " + size)

            self.__bytes = int(match.group())

            # now find multiplication factor
            unit = size[match.end():]
            fac=1
            if unit == "b":
                fac=1
            elif unit == "w":
                fac=self.wordsize
            elif unit == "kb":
                fac=1024
            elif unit == "kw":
                fac=1024*self.wordsize
            elif unit == "mb":
                fac=1048576
            elif unit == "mw":
                fac=1048576*self.wordsize
            elif unit == "gb":
                fac=1073741824
            elif unit == "gw":
                fac=1073741824*self.wordsize
            else:
                raise ValueError("Unknown size unit: " + size)

            self.__bytes *= fac
            return

        raise TypeError("Cannot parse type " + type(time))

    @property
    def bytes(self):
        """return number of seconds represented by this object"""
        return self.__bytes

    @property
    def wordsize(self):
        """
        return the size of a word in bytes. Exactly the value
        used for all conversions in the class
        """
        return self.__wordsize

    @wordsize.setter
    def wordsize(self,value):
        """
        Set the wordsize used for internal conversions in the class
        If set to None use the value for this system
        """
        if value == None:
            (wordsize, dummy) = platform.architecture()
            wordsize = wordsize.replace("bit","")
            try:
                self.__wordsize=int(wordsize)/8 # word size in bytes
            except ValueError:
                raise OSError("Could not parse word size")
        elif not isinstance(value,int):
            raise ValueError("Expected an integer value as the wordsize")
            self.__wordsize = value

    @property
    def words(self):
        """return number of words represented by this object"""
        return self.__bytes // self.wordsize


class pbs(queuing_system_base):
    """class to manage the queue of a pbs queuing system"""
    # PBS documentation manpages:
    #    pbs_resources_linux
    #    qsub

    def name(self):
        return "PBS"


    def __parse_lstring_into(self, lstring, data):
        """Parse a single string following an -l and set the
           appropriate values in the data object.
        """

        if "," in lstring:
            for lstr in lstring.split(","):
                self.__parse_lstring_into(lstring, data)

        # Get key and value
        if "=" not in lstring:
            key = lstring
            value = ""
        else:
            key, value = lstring.split("=", maxsplit=1)

        if key in ["walltime", "mem", "vmem", "nodes"] and not value:
            raise ValueError("The PBS resources walltime, mem, vmem, nodes need an "
                             "argument following them after an '='.")

        if key == "walltime":
            data.walltime = pbs_time(value).seconds
        elif key == "mem":
            data.physical_memory = pbs_size(value).bytes
        elif key == "vmem":
            data.virtual_memory = pbs_size(value).bytes
        elif key == "nodes":
            raise NotImplementedError("Parsing nodes on the commandline not "
                                      "yet implemented.")
        else:
            data.extra_resources[key] = value

    def parse_commandline_args(self, cmdline):
        """
        Parse a commandline string and return a queuing_system_data object

        No check towards consistency like is_ready_for_submission is made
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("-l", default=[], action="append")

        args, rest = parser.parse_known_args(cmdline.split())

        if len(rest) > 0:
            raise NotImplementedError("TODO: Not yet implemented parsing these "
                                      "arguments: " + " ".join(rest))
        data = qd.queuing_system_data()

        # Deal with -l flag:
        if args.l:
            for lstring in args.l:
                self.__parse_lstring_into(lstring, data)
        return data


        #TODO
        # use pbs_size and pbs_time above
        # throw UnknownDataFieldException
        raise NotImplementedError("TODO: Not yet implemented")

    def build_commandline_args(self,data):
        """
        Build a commandline string from the data object and return it

        No check towards consistency like is_ready_for_submission is made
        """
        if not isinstance(data,qd.queuing_system_data):
            raise TypeError("data is not of type queuing_system_data")

        ret = self.why_not_ready_for_submission(data)
        if ret != "":
            raise ValueError("data is not ready for submission: " + ret)

        ret=str()

        #TODO do in a similar fashion to build_script_header
        raise NotImplementedError("TODO: Not yet implemented")


    def parse_script_header(self,f):
        """
        Read a file object and extract queuing_system_data from the header
        for the queuing system

        No check towards consistency like is_ready_for_submission is made
        """
        #TODO
        # note pbs ignores all #PBS directives after the first non-comment or whitespace line!
        # use pbs_size and pbs_time above
        # throw UnknownDataFieldException
        raise NotImplementedError("TODO: Not yet implemented")

    def build_script_header(self,data):
        """
        Build a script header for a queuing system script from the data object
        and return the resulting strint (does not contain any shebang or so, just
        the plain queuing system directives)
        """
        if not isinstance(data,qd.queuing_system_data):
            raise TypeError("data is not of type queuing_system_data")
    
        ret = self.why_not_ready_for_submission(data)
        if ret != "":
            raise ValueError("data is not ready for submission: " + ret)
        
        ret=str()
        # append the job name
        if (data.job_name is not None):
            ret += ("#PBS -N " + data.job_name + "\n")

        # combine stderr and stdout?
        if data.merge_stdout_stderr is not None and data.merge_stdout_stderr:
            ret += ("#PBS -j oe\n")

        # walltime
        if data.walltime is not None:
            ret += ("#PBS -l walltime="+str(data.walltime)+"\n")
    
        # queue@server to run the job at
        if data.queue_name is not None:
            ret += ("#PBS -q " + data.queue_name + "\n")
    
        # amount of physical memory  (workspace size)
        if data.physical_memory is not None:
            ret += ("#PBS -l mem=" + str(data.physical_memory) + "b\n")

        # amount of virtual memory (including swap)
        if data.virtual_memory is not None:
            ret += ("#PBS -l vmem=" + str(data.virtual_memory) + "b\n")

        # Extra resources (as key-value pairs)
        for k, v in data.extra_resources.items():
            if len(v) > 0:
                val = "=" + str(v)
            else:
                val = ""
            ret += ("#PBS -l " + k + val + "\n")

        # when and whom to send emails
        if data.email is not None:
            # we have an email address, hence send mail
            # in cases where this is requested
            ret += ("#PBS -M " + data.email + "\n")

            if data.send_email_on.error is not None \
                    or data.send_email_on.begin is not None \
                    or data.send_email_on.end is not None:
                ret += "#PBS -m "
                if data.send_email_on.error:
                    ret += "a"
                if data.send_email_on.begin:
                    ret += "b"
                if data.send_email_on.end:
                    ret += "e"
                ret += "\n"
        else:
            # no email set, supress sending any email
            ret += "#PBS -m n\n"

        # priority of  job
        if data.priority is not None:
            ret += ("#PBS -p " + str(data.priority) + "\n")

        # nodes speciffication
        ret += "#PBS -l nodes="
        first=True
        for node_type in data.nodes:
            if (first):
                first=False
            else:
                ret += "+"

            ret += str(node_type.count)

            if node_type.name is not None:
                ret += (":" + node_type.name)

            if node_type.no_procs is not None:
                ret += (":ppn=" + str(node_type.no_procs))

            for extra_feature in node_type.extra_features:
                ret += (":" + extra_feature)

        return ret

    def submit_command(self):
        """return the command for the queuing system with which new jobs can be started"""
        return "qsub"

    def abort_command(self):
        """return the command for the queuing system with which jobs can be aborted"""
        return "qdel"

    def why_not_ready_for_submission(self,data):
        """
        return "" if all fine, else return message with the error
        """
        if not isinstance(data,qd.queuing_system_data):
            return "data is not of type queuing_system_data"

        if (data.no_nodes()==0):
            return "No nodes found in nodes list"

        # priority of  job
        if data.priority is not None:
            if not (-1024 <= data.priority <= 1023):
                return "data.priority has the wrong range (expected between -1024 and 1023)"

        return ""

    def get_environment(self):
        """
        return a queuing_system_environment object with the values set appropriately for 
        this queuing_system
        """
        env = qe.queuing_system_environment()
        env.submit_host="PBS_O_HOST"
        env.submit_server="PBS_SERVER"
        env.submit_queue="PBS_O_QUEUE"
        env.submit_workdir="PBS_O_WORKDIR"
        env.jobid="PBS_JOBID"
        env.jobname="PBS_JOBNAME"
        env.queue="PBS_QUEUE"
        env.path="PBS_O_PATH"
        env.home="PBS_O_HOME"
        env.nodes="(< $PBS_NODEFILE)"

        return env

if __name__ == "__main__":
    ################
    #-- pbs_time --#
    ################
    t = pbs_time(15)
    if t.seconds != 15:
        raise SystemExit("pbs_time from integer failed")

    t = pbs_time("1:23:45")
    if t.seconds != 3600+23*60+45:
        raise SystemExit("pbs_time from string failed")

    try:
        t = pbs_time("a:12:56")
        raise SystemExit("pbs_time from invalid string succeeded")
    except ValueError:
        pass


    ################
    #-- pbs_size --#
    ################
    s = pbs_size(16)
    if s.bytes != 16 or s.words != 2:
        raise SystemExit("pbs_size from integer failed")

    s = pbs_size("12kb")
    if s.bytes != 12*1024:
        raise SystemExit("pbs_size from byte string failed")

    s = pbs_size("12gw")
    if s.bytes != 12*1024*1024*1024*8:
        raise SystemExit("pbs_size from word string failed")


    ###########
    #-- pbs --#
    ###########
    pbs = pbs()

    data = qd.queuing_system_data()
    data.email = "tester@test.test"
    data.merge_stdout_stderr = True
    data.physical_memory = 3000
   
    if pbs.is_ready_for_submission(data):
        raise SystemExit("ready for submission returned true where false")

    try:
        pbs.build_script_header(data)
        raise SystemExit("Allowed to build script header from object which is not ready")
    except ValueError:
        pass

    node = qd.node_type()
    node.count = 4
    node.no_procs = 2
    node.name = "blue"
    data.nodes.append(node)

    node = qd.node_type()
    node.count = 2
    node.no_procs = 3
    node.name = "red"
    data.nodes.append(node)

    node = qd.node_type()
    node.count = 12
    data.nodes.append(node)

    strcmp="#PBS -j oe\n#PBS -l mem=3000b\n#PBS -M tester@test.test\n#PBS -l nodes=4:blue:ppn=2+2:red:ppn=3+12:ppn=1"

    if (pbs.build_script_header(data) != strcmp):
        raise SystemExit("build_script_header failed")

    print("Unit Test passed")
   
