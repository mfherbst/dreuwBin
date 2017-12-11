# vi: set et ts=4 sw=4 sts=4:

# Python module to help with the generation of queuing job scripts
# Copyright (C) 2015-17 Michael F. Herbst
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
from queuing_system import queuing_system_data as qd
from queuing_system import queuing_system_environment as qe
import shared_config_lib as conf
import os
import pwd
import queue
import argparse
import shared_utils_lib as utils
import objectmerge

######################################################################
#--  Main function of build scripts  --#
########################################

def builder_main(script_builder, qsys):
    """
    A generic main function which can be used to setup an actual script building
    the jobscripts.

    Just specify the script_builder, which should be derived off the
    jobscript_builder in this class and the queuing_system object
    to optionally submit the job later on.

    This is the function orca_send_job and qchem_send_job use to do
    their work.
    """

    # setup parser:
    parser = argparse.ArgumentParser(
            description='Script to send '+script_builder.program_name+' jobs',
            formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--cfg", metavar="configfile", default=None,type=str,help="Use this alternatve config file as sendscript config")
    parser.add_argument("--send",default=False, action='store_true', help="Send the job once the jobscript has been written.")
    parser.add_argument("--dumpcfg", default=False, action='store_true', 
            help="Dump a default config file under the path specified by --cfg if this file does not exist.")

    # setup script builder:
    script_builder.add_entries_to_argparse(parser)

    # parse args and config:
    args = parser.parse_args()

    try:
        if args.cfg is not None:
            script_builder.parse_config(cfg=args.cfg,autocreate=args.dumpcfg)
        else:
            script_builder.parse_config()
    except ParseConfigError as pe:
        raise SystemExit("When parsing the config: " + pe.args[0])

    script_builder.examine_args(args)

    # write script
    scriptname="jobscript.sh"
    if script_builder.queuing_system_data.job_name is not None:
        scriptname=script_builder.queuing_system_data.job_name + ".sh"

    try:
        with open(scriptname,"w") as f:
            f.write(script_builder.build_script())
    except DataNotReady as dnr:
        raise SystemExit("Missing data: " + dnr.args[0])

    if args.send:
        qsys.submit_script(scriptname)

######################################################################
#--  Helpful hooks  --#
#######################

class hook_base(metaclass=ABCMeta):
    @abstractmethod
    def generate(self,data,params,calc_env):
        """
        Generate shell script code from the queuing_system_data,
        the queuing_system_params and the calculation_environment
        provided
        """
        pass

class copy_from_to_hook(hook_base):
    """
    Hook to copy a list of files/dirs from one directory to another.
    All dirs are copied recursively, all links are dereferenced.

    The relative paths are mainained, ie blubber/blub is copied from
    A/blubber/blub to B/blubber/blub and the 
    target dir is created if neccessary
    """
    def __init__(self,fromdir,todir,files):
        super().__init__()
        self.__files = files
        self.__fromdir=fromdir
        self.__todir=todir

    def __generate_code_for_file(self,filename):
        return 'if [ -r "$' + self.__fromdir+ "/" + filename + '" ]; then \n' \
                + '    CPARGS="--dereference" \n' \
                + '    [ -d "$' + self.__fromdir+ "/" + filename + '" ] && CPARGS="--recursive"\n' \
                + '    DIR=$(dirname "' + filename + '")\n' \
                + '    mkdir -p "$'+self.__todir+'/$DIR"\n' \
                + '    cp $CPARGS "$'+ self.__fromdir+ "/" + filename + '" "$' +self.__todir+'/$DIR"\n' \
                + 'fi\n'

    def generate(self,data,params,calc_env):
        """
        Generate shell script code from the queuing_system_data,
        the queuing_system_params and the calculation_environment
        provided
        """
        string=""
        for filename in self.__files:
            string+=self.__generate_code_for_file(filename)
        return string

class copy_in_hook(hook_base):
    """
    Hook to copy a list of files/dirs to the server working directory
    from the submit workdir if the files exist
    All dirs are copied recursively. 

    The relative paths are mainained, ie blubber/blub is copied from
    SUBMIT_WORKDIR/blubber/blub to SERVER_WORKDIR/blubber/blub and the 
    target dir is created if neccessary
    """
    def __init__(self, files):
        super().__init__()
        self.__files = files

    def generate(self,data,params,calc_env):
        """
        Generate shell script code from the queuing_system_data,
        the queuing_system_params and the calculation_environment
        provided
        """
        #if not isinstance(data,qd.queuing_system_data):
        #    raise TypeError("data not of type qd.queuing_system_data")

        if not isinstance(params,qe.queuing_system_environment):
            raise TypeError("params not of type qe.queuing_system_environment")

        if not isinstance(calc_env,calculation_environment):
            raise TypeError("calc_env not of type calculation_environment")

        return copy_from_to_hook(params.submit_workdir,calc_env.node_work_dir,self.__files)\
                .generate(data,params,calc_env)

class copy_out_hook(hook_base):
    """
    Hook to copy a list of files/subdirs from one directory of the
    node to the submit workdir if the files exist
    All dirs are copied recursively. 

    By default files are copied from the node's working directory,
    i.e. SERVER_WORKDIR.

    The relative paths are mainained, for example if we copy
    from SERVER_WORKDIR, then the file called "blubber/blub" is copied from
    SERVER_WORKDIR/blubber/blub to SUBMIT_WORKDIR/blubber/blub and the
    target dir is created if neccessary.

    Valid values for fromdir are
        "WORK"      use the job's working directory SERVER_WORKDIR
        "SCRATCH"   use the job's scratch directory SERVER_SCRATCHDIR
    """
    def __init__(self, files, fromdir="WORK"):
        super().__init__()
        self.__files = files

        # If None, then read node_work_dir from environment
        self.__fromdir = fromdir

    def generate(self,data,params,calc_env):
        """
        Generate shell script code from the queuing_system_data,
        the queuing_system_params and the calculation_environment
        provided
        """
        #if not isinstance(data,qd.queuing_system_data):
        #    raise TypeError("data not of type qd.queuing_system_data")

        if not isinstance(params,qe.queuing_system_environment):
            raise TypeError("params not of type qe.queuing_system_environment")

        if not isinstance(calc_env,calculation_environment):
            raise TypeError("calc_env not of type calculation_environment")

        fromdir_actual = ""
        if self.__fromdir == "WORK":
            fromdir_actual = calc_env.node_work_dir
        elif self.__fromdir == "SCRATCH":
            fromdir_actual = calc_env.node_scratch_dir
        else:
            raise ValueError("The value passed to fromdir upon construction (==" \
                    + str(self.__fromdir) + ") of this class is not valid.")

        return copy_from_to_hook(fromdir_actual,params.submit_workdir,self.__files)\
                .generate(data,params,calc_env)

#######################################################################
#--  Helper classes  --#
########################

class ParseConfigError(Exception):
    """
    Excetpion thrown when parsing the config file leads to a problem
    """
    def __init__(self,message):
        super(ParseConfigError, self).__init__(message)

class DataNotReady(Exception):
    """
    Thrown if the internal data is not ready for the requested step
    """
    def __init__(self,message):
        super(DataNotReady, self).__init__(message)


class calculation_environment:
    def __init__(self):
        self.node_work_dir=None #str; shell variable containing the dir where calculations take place on the server
        self.node_scratch_dir=None #str; shell variable containing the dir where node-local scratch files may be placed
        self.return_value=None #str; shell variable containing the return value

#######################################################################
#--  Main class  --#
####################

class jobscript_builder:
    """
    Class to build a job script for a queuing system

    A typical workflow looks like this:
    j = jobscript_builder()
    j.add_entries_to_argparse(argparse)
    j.parse_config
    j.examine_args
    j.add_payload_hook(bla)
    j.add_error_hook(bla)
    j.build_script

    j.add_payload_hook(bla)
    j.add_error_hook(bla)
    j.build_script

    ...

    """
    def __init__(self,qsys):
        self.__qsys = qsys
        # Priority Queue
        # https://docs.python.org/3/library/queue.html#queue.PriorityQueue
        # The smaller the int, the higher the priority
        self.__payload_hooks = queue.PriorityQueue() # hooks that generate payload code
        self.__error_hooks = queue.PriorityQueue() # hooks that generate code executed when the job crashes
        self.__qsys_data = qd.queuing_system_data()
        self.__node_workdir_base = None # get from e.g. Config: The base directory to use for the calculations.
                                    # if not otherwise specified, add jobname to get work_dir
        self.__node_scratchdir_base = None # get from e.g. Config: Base dir to use for node-local scratch files
                                    # if not otherwise specified, add jobname to get node_scratch_dir
        self.__force_node_workdir = None # this workdir has been enforced on the server via a commandline flag
        self.__force_node_scratchdir = None # this scratchdir has been enforced via a commandline flag

    @property
    def qsys(self):
        """
        The queuing_system assumed for the job builder
        """
        return self.__qsys

    @property
    def queuing_system_data(self):
        """
        The queuing_system_data used to build the script
        """
        return self.__qsys_data

    @queuing_system_data.setter
    def queuing_system_data(self,val):
        if not isinstance(val,qd.queuing_system_data):
            raise TypeError("queuing_system_data object expected")
        self.__qsys_data = val

    @property
    def default_configfile(self):
        """
        Return the config file used by default for the read
        """
        return conf.default_configfile(fileroot="sendscripts")


    def add_payload_hook(self,hook,priority=0):
        """
        Add a hook for code generation for the next call of build_script, which 
        is triggered as a payload when the jobscript is executed

        Note that when this code is executed, the current working directory
        is the calc_env.work_dir.

        You may provide a priority as an int. Note that lower values
        mean higher priority

        Note: After the next call of build_script, these hooks are consumed and
        need to be added again if they should be used again.
        """
        if not isinstance(hook,hook_base):
            raise TypeError("The hook provided is not of type hook_base")

        self.__payload_hooks.put_nowait( (priority,hook) )

    def add_error_hook(self,hook,priority=0):
        """
        Add a hook for code generation for the next call of build_script, 
        which is triggered when the job aborts or exits prematurely

        Note that when this code is executed, the current working directory
        is the calc_env.work_dir.

        You may provide a priority as an int. Note that lower values
        mean higher priority

        Note: After the next call of build_script, these hooks are consumed and
        need to be added again if they should be used again.
        """
        if not isinstance(hook,hook_base):
            raise TypeError("The hook provided is not of type hook_base")

        self.__error_hooks.put_nowait( (priority,hook) )

    def clear_hooks(self):
        """
        Clear both the error and payload hooks
        """
        self.__error_hooks.clear()
        self.__payload_hooks.clear()

    def parse_config(self,cfg=None,autocreate=True):
        """
        Parse the config file and update the inner queuing_system_data
        i.e. if there are confilcting values, the config file takes
        preference

        On error throws a ParseConfigError
        """
        if cfg is None:
            cfg = self.default_configfile


        # setup config parser:
        k = conf.keyword_config_parser()

        username = pwd.getpwuid(os.getuid()).pw_name
        k.add_keyword("workdir_base",default="/scratch/"+username,comment="The base directory in which calculations are done")
        k.add_keyword("scratchdir_base",default="/lscratch/"+username,comment="The base directory in which data local to the node is stored")
        k.add_keyword("mail",default="",comment="Mail address to send mail to. If empty, no mail is sent.")
        k.add_keyword("jobname",default="",comment="The default jobname")
        k.add_keyword("queue",default="",comment="The default queue to use")
        k.add_keyword("merge_stdout_stderr", default="true",comment="Merge stdout and stderr streams, valid are \"true\" and \"false\"")
        k.add_keyword("send_email_end", default="true", comment="Send an email if the job ends, valid are \"true\" and \"false\"")
        k.add_keyword("send_email_begin", default="", comment="Send an email if the job begins, valid are \"true\" and \"false\"")
        k.add_keyword("send_email_error", default="true", comment="Send an email if the job has an error, valid are \"true\" and \"false\"")
        k.add_keyword("memory", default="", comment="Default physical memory in the format integer[suffix]")
        k.add_keyword("virtual_memory", default="", comment="Default virtual memory in the format integer[suffix] (Default: what was set for memory)")
        k.add_keyword("walltime", default="", comment="Default walltime in the format integer[suffix] or [[[days:]hours:]minutes:]seconds")

        # see if file exists and create if not
        if not os.path.isfile(cfg):

            if autocreate:
                dirname=os.path.dirname(cfg)
                if not os.path.exists(dirname):
                    os.makedirs(dirname)

                with open(cfg,"w") as f:
                    f.write(k.config_string())

                os.sys.stderr.write("Did not find config file, will create one for you")
                raise ParseConfigError("Created default config file under " + cfg)
            else:
                raise ParseConfigError("Config File not found:" + cfg)

        # parse the file:
        try:
            k.parse(cfg)
        except conf.InvalidConfigFileException as i:
            raise ParseConfigError("Error while parsing the config file: " + i.args[0])

        data = self.__qsys_data
        params = self.__qsys.get_environment()

        # parse it:
        if len(k.get_value("workdir_base")) > 0:
            self.__node_workdir_base = k.get_value("workdir_base")

        if len(k.get_value("scratchdir_base")) > 0:
            self.__node_scratchdir_base = k.get_value("scratchdir_base")

        if len(k.get_value("mail")) > 0:
            data.email = k.get_value("mail")

        if len(k.get_value("jobname")) > 0:
            data.job_name= k.get_value("jobname")

        if len(k.get_value("queue")) > 0:
            data.queue_name=k.get_value("queue")

        if len(k.get_value("merge_stdout_stderr")) > 0:
            try:
                data.merge_stdout_stderr = utils.interpret_string_as_bool(k.get_value("merge_stdout_stderr"))
            except argparse.ArgumentTypeError:
                raise ParseConfigError("Cannot interpret config value of merge_stdout_stderr: " + k.get_value("merge_stdout_stderr") + ". Should be true or false")

        if len(k.get_value("send_email_end")) > 0:
            try:
                data.send_email_on.end = utils.interpret_string_as_bool(k.get_value("send_email_end"))
            except argparse.ArgumentTypeError:
                raise ParseConfigError("Cannot interpret config value of send_email_end: " + k.get_value("send_email_end") + ". Should be true or false")

        if len(k.get_value("send_email_begin")) > 0:
            try:
                data.send_email_on.begin =utils.interpret_string_as_bool(k.get_value("send_email_begin"))
            except argparse.ArgumentTypeError:
                raise ParseConfigError("Cannot interpret config value of send_email_begin: " + k.get_value("send_email_begin") + ". Should be true or false")

        if len(k.get_value("send_email_error")) > 0:
            try:
                data.send_email_on.error = utils.interpret_string_as_bool(k.get_value("send_email_error"))
            except argparse.ArgumentTypeError:
                raise ParseConfigError("Cannot interpret config value of send_email_error: " + k.get_value("send_email_error") + ". Should be true or false")

        if len(k.get_value("memory")) > 0:
            try:
                val = utils.interpret_string_as_file_size(k.get_value("memory"))
                data.physical_memory = val
                data.virtual_memory = val
            except argparse.ArgumentTypeError:
                raise ParseConfigError("Cannot interpret config value of memory: " + k.get_value("memory") + ". Should be of the form integer[suffix] like 4gb")

        if len(k.get_value("virtual_memory")) > 0:
            try:
                data.virtual_memory = utils.interpret_string_as_file_size(k.get_value("virtual_memory"))
            except argparse.ArgumentTypeError:
                raise ParseConfigError("Cannot interpret config value of virtual_memory: " + k.get_value("virtual_memory") + ". Should be of the form integer[suffix] like 4gb")

        if len(k.get_value("walltime")) > 0:
            try:
                data.walltime = utils.interpret_string_as_time_interval(k.get_value("walltime"))
            except argparse.ArgumentTypeError:
                raise ParseConfigError("Cannot interpret config value of walltime: " + k.get_value("walltime") + ". Should be of the form integer[suffix] or [[[days:]hours:]minutes:]seconds")

    def add_entries_to_argparse(self,argparse):
        """
        Adds required entries to an argparse Object supplied
        """

        argparse.add_argument("--qsys-args", "-q", metavar="args", default=None, type=str,help="Extra options for the queuing system (e.g. \"-l mem=40 -l vmem=20\" or \"-l intel\")." )
        argparse.add_argument("--workdir", "-d", metavar="dir", default=None, type=str, help="Change job execution directory on the node")
        argparse.add_argument("--scratchdir", metavar="dir", default=None, type=str, help="Change the path of the node-local scratch directory")
        argparse.add_argument("--mail", "-m", metavar="user@host", default=None, type=str, help="EMail Address to which messages are sent")
        argparse.add_argument("--wt", metavar="time", default=None, type=utils.interpret_string_as_time_interval, help="Walltime; format: [[[days:]hours:]minutes:]seconds or integer[suffix]")
        argparse.add_argument("--mem",metavar="size", default=None, type=utils.interpret_string_as_file_size, help="Physical memory in the format integer[suffix]")
        argparse.add_argument("--vmem",metavar="size", default=None, type=utils.interpret_string_as_file_size, help="Virtual memory in the format integer[suffix] (Default: What was set for --mem)")
        argparse.add_argument("--np",metavar="#", default=None, type=int, help="Number of processors/threads")
        argparse.add_argument("--name",metavar="jobname", default=None,type=str,help="Name of the Job")
        argparse.add_argument("--priority",metavar="num", default=None,type=int,help="Priority of the Job")
        argparse.add_argument("--queue",metavar="queue[@host]", default=None,type=str,help="Select queue to use to run the job")
        argparse.add_argument("--merge_stdout_stderr", metavar="true|false", default=None,type=utils.interpret_string_as_bool,help="Merge stdout and stderr streams")
        argparse.add_argument("--send_email_end", metavar="true|false", default=None,type=utils.interpret_string_as_bool,help="Send an email if the job ends")
        argparse.add_argument("--send_email_begin", metavar="true|false", default=None,type=utils.interpret_string_as_bool,help="Send an email if the job begins")
        argparse.add_argument("--send_email_error", metavar="true|false", default=None,type=utils.interpret_string_as_bool,help="Send an email if the job has an error")

    def examine_args(self,args):
        """
        Update the inner queuing_system_data using the argparse data
        i.e. if there are conflicting values, the commandline takes
        preference

        If we find a flag to parse extra commandline args (-q, --qsys-args)
        invoke parsing of those arguments as well. Note that these explicitly
        provided arguments overwrite everything else on the commandline
        """
        data = self.queuing_system_data

        if args.name is not None:
            data.job_name = args.name

        if args.wt is not None:
            data.walltime = args.wt

        if args.mem is not None:
            data.physical_memory = args.mem
            data.virtual_memory = args.mem

        if args.vmem is not None:
            data.virtual_memory = args.vmem

        if args.np is not None:
            node = qd.node_type()
            node.no_procs = args.np
            data.add_node_type(node)

        if args.mail is not None:
            data.email = args.mail

        if args.priority is not None:
            data.priority = args.priority

        if args.workdir is not None:
            self.__force_node_workdir = args.workdir

        if args.scratchdir is not None:
            self.__force_node_scratchdir = args.scratchdir

        if args.queue is not None:
            data.queue_name = args.queue

        if args.merge_stdout_stderr is not None:
            data.merge_stdout_stderr = args.merge_stdout_stderr

        if args.send_email_end is not None:
            data.send_email_on.end = args.send_email_end

        if args.send_email_begin is not None:
            data.send_email_on.begin = args.send_email_begin

        if args.send_email_error is not None:
            data.send_email_on.error = args.send_email_error

        if args.qsys_args is not None:
            qsys = self.__qsys
            try:
                cmd_qd = qsys.parse_commandline_args(args.qsys_args)
            except ValueError as e:
                raise SystemExit("The explicitly provided --qsys-args are erroneous: " +
                                 str(e))

            om = objectmerge.objectmerge(data,allowUpdates=True,allowListExtend=False)
            try:
                om.merge_in(cmd_qd)
            except objectmerge.MergeException as e:
                raise SystemExit("The explicitly provided --qsys-args and the other arguments conflict: " + e.args[0])

    def build_script(self):
        """
        use self.qsys to build the script and return string of its content

        Raises DataNotReady exception if the internally represented data is not
        ready for the script to be written

        Note: This function empties both the list of error and the list of payload hooks, so 
        if two scripts should be built new hooks need to be added beforehand
        """
        qsys = self.__qsys
        data = self.__qsys_data
        params = qsys.get_environment()
        environ = calculation_environment()

        # If we still have no nodes to run on up to this
        # point we add one. A more sensible way to deal with
        # this would be to have a default in the config, but
        # in the current mechanism this cannot be overwritten
        # (since commandline arguments only add extra nodes but
        # allow not to amend the number of processors which are
        # used on a particular node.
        #
        # TODO Later one would probably have a two-stage parser
        #      one which builds up some intermediate structure
        #      describing what the user wants and only at the time
        #      of writing the script in this function this would
        #      be translated into an actual list of nodes and
        #      processors to use ... but I cannot be bothered to
        #      do this right now, so this is a quick fix for the
        #      warning that there is no node available.
        if data.no_nodes() == 0:
            print("Warning: Number of processors or nodes to use not specified anywhere. "
                    "Defaulting to 1 node and 1 processor.")
            node = qd.node_type()
            node.no_procs = 1
            data.add_node_type(node)

        # check if data is ready:
        if not qsys.is_ready_for_submission(data):
            raise DataNotReady(qsys.why_not_ready_for_submission(data))

        # Determine the shell string expression for the working directory
        # and the scratch directory.
        # The variables workdirexpr and scratchdirexpr do not neccessarily
        # contain an actual directory. They only need to contain a valid
        # bash shell expression, which when assigned to a variable yields
        # a correct directory.
        if self.__force_node_workdir:
            workdirexpr='"' + self.__force_node_workdir + '"'
        elif self.__node_workdir_base and data.job_name:
            workdirexpr = '"' + self.__node_workdir_base + '/' + data.job_name
            workdirexpr += '_$' + params.jobid + '"'
        else:
            raise DataNotReady("Could not determine working directory.\n"
                    "Either specify it on the commandline or provide a jobname and "
                    "add a workdir_base in the config file.")

        if self.__force_node_scratchdir:
            scratchdirexpr = '"' + self.__force_node_scratchdir + '"'
        elif self.__node_scratchdir_base and data.job_name:
            scratchdirexpr = '"' + self.__node_scratchdir_base + "/" + data.job_name
            scratchdirexpr += '_$' + params.jobid + '"'
        else:
            raise DataNotReady("Could not determine scratch directory.\n"
                "Either specify it on the commandline or provide a jobname and "
                "add a scratchdir_base in the config file.")


        if self.queuing_system_data.walltime is None:
            print("Warning: Walltime not set. Queuing systems default will be used.")
        if self.queuing_system_data.physical_memory is None:
            print("Warning: Physical memory not set. Queuing systems default will be used.")
        if self.queuing_system_data.virtual_memory is None:
            print("Warning: Virtual memory not set. Queuing systems default will be used.")

        # build shebang:
        string="#!/bin/bash\n#\n"

        # build header
        string += qsys.build_script_header(data)
        string += "\n"

        # separator
        separator = "#\n###################################\n#\n"
        string += separator

        # Copy global vars from python part
        string += 'SUBMIT_HOST=$' + params.submit_host + '\n'
        string += 'SUBMIT_SERVER=$' + params.submit_server+ '\n'
        string += 'SUBMIT_QUEUE=$' + params.submit_queue+ '\n'
        string += 'SUBMIT_WORKDIR=$' + params.submit_workdir+ '\n'
        string += 'JOBID=$' + params.jobid+ '\n'
        string += 'JOBNAME=$' + params.jobname+ '\n'
        string += 'QUEUE=$' + params.queue+ '\n'
        string += 'O_PATH=$' + params.path+ '\n'
        string += 'O_HOME=$' +params.home+ '\n'
        string += 'NODES=$' + params.nodes + '\n'
        string += 'NODES_UNIQUE=$(echo "$NODES" | sort -u)\n'

        # Setup return / node / scratch environment:
        environ.return_value = "RETURN_VALUE"
        environ.node_work_dir = "NODE_WORKDIR"
        environ.node_scratch_dir="NODE_SCRATCHDIR"
        string += 'RETURN_VALUE=0\n'
        string += 'NODE_WORKDIR=' + workdirexpr + '\n'
        string += 'NODE_SCRATCHDIR=' + scratchdirexpr + '\n'

        string += separator

        # functions:
        string += """ \
print_info() {
    echo ------------------------------------------------------
    echo "Job is running on nodes"
    echo "$NODES" | sed 's/^/    /g'
    echo ------------------------------------------------------
    echo qsys: job was submitted from $SUBMIT_HOST
    echo qsys: originating queue is $SUBMIT_QUEUE
    echo qsys: executing queue is $QUEUE
    echo qsys: original working directory is $SUBMIT_WORKDIR
    echo qsys: job identifier is $JOBID
    echo qsys: job name is $JOBNAME
    echo qsys: current home directory is $O_HOME
    echo qsys: PATH = $O_PATH
    echo ------------------------------------------------------
    echo
}

stage_in() {
    rm -f "$SUBMIT_WORKDIR/job_not_successful"

    echo "Calculation working directory: $NODE_WORKDIR"
    echo "            scratch directory: $NODE_SCRATCHDIR"

    # create workdir and cd to it.
    if ! mkdir -m700 -p $NODE_SCRATCHDIR $NODE_WORKDIR; then
        echo "Could not create scratch($NODE_SCRATCHDIR) or workdir($NODE_WORKDIR)" >&2
        exit 1
    fi
    cd $NODE_WORKDIR

    echo
    echo ------------------------------------------------------
    echo
}

stage_out() {
    if [ "$RETURN_VALUE" != "0" ]; then
        touch "$SUBMIT_WORKDIR/job_not_successful"
    fi

    echo
    echo ------------------------------------------------------
    echo

    echo "Final files in $SUBMIT_WORKDIR:"
    (
        cd $SUBMIT_WORKDIR
        ls -l | sed 's/^/    /g'
    )

    echo
    echo "More files can be found in $NODE_WORKDIR and $NODE_SCRATCHDIR on"
    echo "$NODES_UNIQUE" | sed 's/^/    /g'
    echo
    echo "Sizes of these files:"

    if echo "$NODE_SCRATCHDIR"/* | grep -q "$NODE_SCRATCHDIR/\*$"; then
        # no files in scratchdir:
        du -shc * | sed 's/^/    /g'
    else
        du -shc * "$NODE_SCRATCHDIR"/* | sed 's/^/    /g'
    fi

    echo
    echo "If you want to delete these, run:"
    for node in $NODES_UNIQUE; do
        echo "    ssh $node rm -r \\"$NODE_WORKDIR\\" \\"$NODE_SCRATCHDIR\\""
    done
}

handle_error() {
    # Make sure this function is only called once
    # and not once for each parallel process
    trap ':' 2 9 15

    echo
    echo "#######################################"
    echo "#-- Early termination signal caught --#"
    echo "#######################################"
    echo
    error_hooks
    stage_out
}

"""
        # add stuff from hooks:
        string+="payload_hooks() {\n:\n"

        while not self.__payload_hooks.empty():
            hook = self.__payload_hooks.get() [1]
            string += hook.generate(data,params,environ)
            string += "\n"
        string += "}\n\n"

        string+="error_hooks() {\n:\n"

        while not self.__error_hooks.empty():
            hook = self.__error_hooks.get() [1]
            string += hook.generate(data,params,environ)
            string += "\n"
        string += "}\n"

        string += separator

        string += """\
# Run the stuff:

print_info
stage_in

# If catch signals 2 9 15, run this function:
trap 'handle_error' 2 9 15

payload_hooks
stage_out
exit $RETURN_VALUE\

"""

        return string

if __name__ == "__main__":
    #TODO have a proper unit test
    import argparse
    parser = argparse.ArgumentParser(description='Testparser')

    from pbs import pbs
    qsys=pbs()
    j = jobscript_builder(qsys)

    j.add_entries_to_argparse(parser)

    # parse the config
    j.parse_config()
    print(j.queuing_system_data)


    argslist=["--priority","0","--wt", "4h", "--mem", "56mb", "--vmem", "120mb", "--np", "2", "--name", "blubber" ]
    args = parser.parse_args(argslist)
    j.examine_args(args)


    print(argslist)
    print(j.queuing_system_data)

    print( j.build_script() )

    print()
    print("---------")
    print()

    argslist=["--priority","0","--wt", "12:34:45", "--mem", "56mb", "--vmem", "120mb", "--np", "2", "--name", "blubber" ]
    args = parser.parse_args(argslist)
    j.examine_args(args)
    print(argslist)
    print(j.queuing_system_data)


    #print("Unit Test passed")
