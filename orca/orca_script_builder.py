# vi: set et ts=4 sw=4 sts=4:

# Python module to build a orca jobscripts
# Copyright (C) 2017 Michael F. Herbst, Manuel Hodecker, Marvin Hoffmann
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

from queuing_system import jobscript_builder as jsb
from queuing_system import queuing_system_data as qd
from queuing_system import queuing_system_environment as qe
import os.path
import shared_utils_lib as utils

#########################################################
#-- Settings --#
################

orca_basedir = "/opt/software/Orca"

# Map orca version to the mpi module
# which needs to be loaded for orca to run
orca_to_openmpi_map = {
    #"4.0.0" : "openmpi/gcc/2.0.2", #TODO Check when there
    "4.0.0" : "openmpi/gcc/1.8.2", #TODO Check when there
    "3.0.3" : "openmpi/gcc/1.8.2",
}

#########################################################
#--  Orca  --#
##############

class orca_args():
    def __init__(self):
        self.infile=None #str, path to the Orca input file
        self.outfile=None #str or None, Orca output filename
        self.orca_executable=None #str, full path to orca executable
        self.modules=[] # List of modules to load

class orca_payload(jsb.hook_base):
    def __init__(self,args):
        if not isinstance(args,orca_args):
            raise TypeError("args should be of type " + str(type(orca_args)))
        self.__orca_args = args

    def generate(self,data,params,calc_env):
        """
        Generate shell script code from the queuing_system_data,
        the queuing_system_params and the calculation_environment
        provided
        """
        if not isinstance(data,qd.queuing_system_data):
            raise TypeError("data not of type qd.queuing_system_data")

        if not isinstance(params,qe.queuing_system_environment):
            raise TypeError("params not of type qe.queuing_system_environment")

        if not isinstance(calc_env,jsb.calculation_environment):
            raise TypeError("calc_env not of type calculation_environment")

        orca_args = self.__orca_args

        # Build orca commandline
        cmdline=orca_args.orca_executable
        cmdline += ' "' + orca_args.infile + '"'
        cmdline += " > " + orca_args.outfile

        # Directory in which orca is contained
        orcadir = os.path.abspath(
                os.path.dirname(orca_args.orca_executable))

        # Set environment
        string = 'export PATH="'+orcadir+':$PATH"\n'
        for mod in orca_args.modules:
            string += "module load " + mod + "\n"
        string += "\n"

        # Run orca
        string += cmdline + '\n'
        string += calc_env.return_value + '=$?\n'
        string += "\n"

        string += "# check if job terminated successfully\n" \
                + 'if ! grep -q "****ORCA TERMINATED NORMALLY****" "' \
                + orca_args.outfile + '"; then\n' \
                + '    ' + calc_env.return_value +'=1\n' \
                + 'fi\n'

        return string

class orca_script_builder(jsb.jobscript_builder):
    """
    Class to build a job script for Orca
    """

    def __init__(self,qsys):
        super().__init__(qsys)
        self.__files_copy_in=None  # files that should be copied into the workdir
        self.__files_copy_work_out=None  # files that should be copied out of the workdir on successful execution
        self.__files_copy_error_out=None # files that should be copied out of the workdir on 
        self.__orca_args=None
        self.program_name = "ORCA"

    @property
    def orca_args(self):
        return self.__orca_args

    @orca_args.setter
    def orca_args(self,val):
        if not isinstance(val,orca_args):
            raise TypeError("val should be of type " + str(type(orca_args)))
        self.__orca_args = val

    def add_entries_to_argparse(self,argparse):
        """
        Adds required entries to an argparse Object supplied
        """
        super().add_entries_to_argparse(argparse)

        argparse.add_argument("infile",metavar="infile.inp", type=str, help="The path to the ORCA input file")
        argparse.add_argument("--out",metavar="file",default=None,type=str, help="ORCA output filename (Default: infile + \".out\")")
        argparse.add_argument("--version", default=None, type=str, help="Version string identifying the ORCA version to be used.")

        epilog="The script tries to complete parameters and information which are not \n" \
                + "explicitly provided on the commandline using the infile.in input \n" \
                + "file. This includes: \n" \
                + "   - jobname (Name of the file), \n" \
                + "   - output file name, \n" \
                + "   - number of processors (using %pal and alike) \n" \
                + "   - physical and virtual memory (using %maxcore and alike) \n" \
                + "\nFurthermore QSYS directives are available in the orca input file\n" \
                + "to further set the following properties:\n"

        for k in qd.qsys_line.available_directives:
            epilog += "   !QSYS " + k + "= <value>     set " \
                    + qd.qsys_line.available_directives[k] + " to <value>\n"

        if argparse.epilog is None:
            argparse.epilog = epilog
        else:
            argparse.epilog += ("\n" + epilog)

    def _orca_work_files(self):
        """
        Returns a list of possible files which are generated
        by this orca job.
        """
        # The ret list should be filled with files to be copied.
        # Note that existance is checked automatically, i.e.
        # if a file is listed here, but is not created by orca
        # or does not exist after the run, no error is produced.
        ret=[]

        # Determine the base names of the files generated by orca
        (base, ext) = os.path.splitext(self.__orca_args.infile)
        prefixes = [ os.path.basename(f) for f in (base, self.__orca_args.infile) ]

        # Add output file
        if self.__orca_args.outfile is not None:
            ret.append(self.__orca_args.outfile)
        
        # Copy gbw and property files
        # Note: Orca does not always split the extension, so we
        # will attempt to copy both versions
        postfixes = [ ".prop", ".gbw", "_property.txt" ]
        ret.extend([
            p+e for p in prefixes for e in postfixes
        ])

        # TODO Think about more files to copy back!
        return ret

    def _parse_infile(self,infile):
        """
        Update the inner data using the infile provided. If the values conflict, the
        values are left unchanged.
        """
        pass

    def examine_args(self,args):
        """
        Update the inner data using the argparse data
        i.e. if there are conflicting values, the commandline takes
        preference

        If we find a flag to parse extra commandline args (-q, --qsys-args)
        invoke parsing of those arguments as well. Note that these explicitly
        provided arguments overwrite everything else on the commandline
        """
        super().examine_args(args)

        # check parsed data for consistency
        if not os.path.isfile(args.infile):
            raise SystemExit("File not found: " + args.infile)

        # set internal values:
        self.__orca_args = orca_args()
        self.__orca_args.infile = args.infile

        # Determine version and executable
        orcafile=None
        version = args.version
        if version is None:
            version = utils.determine_most_recent_version(orca_basedir)
        orcafile=orca_basedir + "/" + version + "/orca"

        # Check executable exists:
        if not os.path.isfile(orcafile) or not os.access(orcafile,os.X_OK):
            raise SystemExit("ORCA executable \"" + orcafile 
                    + "\" could not be found on the system. "
                    +"Check that you supplied an ORCA version which is actually installed.")
        self.__orca_args.orca_executable = orcafile 

        # Set openmpi module to use:
        try:
            self.__orca_args.modules.append(orca_to_openmpi_map[version])
        except KeyError:
            raise SystemExit("Could not determine openmpi version to use for ORCA version \"" + version + "\". " +
                    "Please append the proper value in " + os.path.abspath(__file__) +  ".")

        # split .in extension from filename
        filename, extension =  os.path.splitext(self.__orca_args.infile)
        if not extension in [ ".in", ".inp" ]:
            filename = self.__orca_args.infile

        # set outfile if not provided:
        if args.out is None:
            self.__orca_args.outfile= filename + ".out"
        else:
            self._orca_args.outfile=args.out

        # set jobname if not yet set:
        if self.queuing_system_data.job_name is None:
            self.queuing_system_data.job_name = filename

        # files to copy in
        self.__files_copy_in =[]
        self.__files_copy_in.append(self.__orca_args.infile)

        # parse infile 
        self._parse_infile(self.__orca_args.infile)

        # File to copy out from working directory of node
        # on succesful execution.
        self.__files_copy_work_out=self._orca_work_files()

        # Files to copy out from working directory of node
        # if an error occurrs
        self.__files_copy_error_out=[ self.__orca_args.outfile ]

    def build_script(self):
        if self.__orca_args.orca_executable is None:
            raise jsb.DataNotReady("No path to an ORCA executable.")

        if self.__orca_args.outfile is None:
            raise jsb.DataNotReady("No outputfile provided")

        self.add_payload_hook(jsb.copy_in_hook(self.__files_copy_in),-1000)
        self.add_payload_hook(orca_payload(self.__orca_args))

        # Hook to copy files workdir of node -> submitdir
        self.add_payload_hook(jsb.copy_out_hook(self.__files_copy_work_out, fromdir="WORK"),900)

        self.add_error_hook(jsb.copy_out_hook(self.__files_copy_error_out),-1000)
        return super().build_script()

