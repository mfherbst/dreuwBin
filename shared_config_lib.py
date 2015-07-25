# vi: set et ts=4 sw=4 sts=4:

# Python module to deal with config files
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
# file COPYING or at <http://www.gnu.org/licenses/>.

import os
import sys
import re

def default_configdir():
    """
    Return default config dir path
    """
    return os.path.expanduser("~/.dreuwBin")

def default_configfile(fileroot=None,extension="cfg"):
    """
    Return default config file

    Alternatively the extension and the fileroot (basename without
    extension) can be modified by the parameters
    """

    if fileroot is None:
        fileroot = os.path.basename(sys.argv[0])
        (fileroot,dummy) = os.path.splitext(fileroot)

    if not isinstance(fileroot,str):
        raise TypeError("fileroot needs to be a string")
    
    if not isinstance(extension,str):
        raise TypeError("extension needs to be a string")

    return default_configdir() + "/" + fileroot + "." + extension

class config_entry:
    def __init__(self,value=None,comment=None):
        self.value = value
        self.comment = comment

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self,val):
        self.__value=val

    @property
    def comment(self):
        return self.__comment

    @comment.setter
    def comment(self,val):
        if val is None:
            self.__comment = None
        elif isinstance(val,str):
            self.__comment = val
        else:
            raise TypeError("comment has to be a string")

class InvalidConfigFileException(Exception):
    """
    Exception thrown when parsing the config file
    leads to problems
    """
    def __init__(self,message,linenr,path):
        super(InvalidConfigFileException, self).__init__(message)
        self.__linenr = linenr
        self.__path = path

    @property
    def linenr(self):
        return self.__linenr

    @property
    def path(self):
        return self.__path

#TODO add class that reads and writes the config in proper json format

#TODO add superclass that only extracts the blocks and the content
# of them for further processing in derived classes
# like for example the following one
class keyword_config_parser:
    """
    Class parsing a config file that only consists of 
    blocks of the form KEYWORD=value
    """
    def __init__(self):
        self.__entries={None:{}}    # dictionary of dictionaries of entries
                                    # None represents the top level (and no block)

    def add_keyword(self,keyword,default=None,block=None,comment=None):
        """
        Add a new keyword with a possible default value (or None if not given)
        to the parser. Can also add a comment used when the default config file is 
        written
        """
        if block is not None and not isinstance(block,str):
            raise TypeError("block has to be a string or None")

        entry = config_entry(comment=comment)
        entry.value = default

        if self.__entries.get(block) is None:
            # first time reaching this block ==> add a dict:
            self.__entries[block] = {}
        
        (self.__entries[block])[keyword] = entry

    def __process_config_line(self,line,block):
        """
        Take the line, split it by the = and interpret results.
        Each line is required to contain a =
        Interpreted results are addet to the block given (or main
        if the block is None)
        """

        if block is not None and not isinstance(block,str):
            raise TypeError("block has to be a string or None")
        if not block in self.__entries:
            raise ValueError("Unknown block: " + block)

        if len(line) == 0:
            return

        match = re.match("^.*\s*=\s*",line)
        if match is None:
            raise ValueError("Line does not contain a =")

        # split the line
        s = line.split("=")
        if len(s) > 2:
            raise ValueError("Line contains more than one =")

        # remove whitespace:
        s[0] = s[0].strip()
        s[1] = s[1].strip()

        blockentries=self.__entries[block]
        blockstr=None
        if block is not None:
            blockstr=" in block " + str(block)
        else:
            blockstr=""

        if s[0] in blockentries:
            blockentries[s[0]].value = s[1]
        else:
            raise ValueError("Unknown keyword " + s[0] + blockstr +".")

    def parse(self,path):
        """
        Parse the config file and set the values in the dictionary
        If an unknown Keyword arises an InvalidConfigOptionException
        is raised.
        """
        
        block=None # the current block
        with open(path,"r") as f:
            for count, line in enumerate(f,1):
                # ignore comment lines:
                if line.startswith("#"): continue

                # remove whitespace:
                line = line.strip()

                # ignore zero lines:
                if len(line) == 0: continue

                try:
                    # if we contain both a { and a }, we have a one-line block
                    match = re.match("^[^=]*{.*}$",line)
                    if match is not None:
                        if block is not None:
                            raise InvalidConfigFileException(
                                    "Error occurred when parsing config file "
                                    + str(path) + " at line " + str(count)
                                    +": " +
                                    "Block "+block +" has not been closed"
                                    +" properly before next block started.",count,path)
                        first_backet=line.find("{")
                        innerblock=line[:first_backet].strip()
                        innerline=line[first_backet+1:match.endpos-1].strip()
                        self.__process_config_line(innerline,innerblock)
                        continue

                    # if we contain a { and no = beforehand, we start a block here
                    match = re.match("^[^=]*{.*",line)
                    if match is not None:
                        if block is not None:
                            raise InvalidConfigFileException(
                                    "Error occurred when parsing config file "
                                    + str(path) + " at line " + str(count)
                                    +": " +
                                    "Block "+block +" has not been closed"
                                    +" properly before next block started.",count,path)
                        first_backet=line.find("{")
                        block=line[:first_backet].strip()
                        innerline=line[first_backet+1:].strip()
                        if len(innerline) > 0:
                            self.__process_config_line(innerline,block)
                        continue

                    # if we contain a } in the end, this ends the block
                    match = re.match("^.*}$",line)
                    if match is not None:
                        if block is None:
                            raise InvalidConfigFileException(
                                    "Error occurred when parsing config file "
                                    + str(path) + " at line " + str(count)
                                    +": " +
                                    "Attempt to close a block where we are already"
                                    +" outside any block.",count,path)
                        last_backet=line.rfind("}")
                        innerline=line[:last_backet].strip()
                        if len(innerline) > 0:
                            self.__process_config_line(innerline,block)
                        block=None
                        continue

                    # within a block:
                    self.__process_config_line(line,block)
                except ValueError as v:
                    raise InvalidConfigFileException(
                        "Error occurred when parsing config file "
                        + str(path) + " at line " + str(count)
                        +": " + v.args[0],count,path)

            if block is not None:
                raise InvalidConfigFileException(
                        "Error occurred when parsing config file "
                        + str(path) + " at line " + str(count)
                        +": " +
                        "Some blocks in the config file " + str(path) + " were not closed properly",count,path)

    def get_blocks(self):
        """
        return the list of blocks as strings including a None
        object representing the top level entries
        """
        return self.__entries.keys()

    def get_block(self,block=None):
        """
        Return a python dictionary representing the block of entries
        if no block specified, returns the top level entries
        """
        if not block in self.__entries:
            raise ValueError("Unknown block: " + str(block))
        return self.__entries[block]

    def get_entry(self,keyword, block=None):
        """
        Return the entry corresponding to the keyword in the block.
        If the block is none, keyword is looked up in the top level entries
        """
        blockdict = self.get_block(block=block)
        if not keyword in blockdict:
            raise ValueError("Unknown keyword in block "+str(block)+": " + str(keyword))
        return self.get_block(block=block) [keyword]

    def get_value(self,keyword,block=None):
        """
        Return the value corresponding to the keyword in the block.
        If the block is none, keyword is looked up in the top level entries
        """
        return self.get_entry(keyword,block=block).value

    def json_string(self,compact=False):
        """
        Get a json string representing the current object's keywords and values

        If compact is true, a very long string is returned (without any line break)
        left for someone else to format.
        """
        nl="\n"
        indent_unit=3
        if compact:
            nl="  "
            indent_unit=0

        string="{"+nl
        indent=indent_unit

        for blocki, block in enumerate(self.__entries.keys()):
            havecomma=False #have a forced comma in the following loop
            if block is not None:
                string+= "".ljust(indent) + "\""+block+"\": {"+nl
                indent+=indent_unit
            else:
                if blocki < len(self.__entries)-1:
                    havecomma=True

            blockdict=self.get_block(block)
            for keywordi, keyword in enumerate(blockdict.keys()):
                string += "".ljust(indent) + "\""+keyword+"\": " + "\""+self.get_value(keyword,block=block) + "\""
                if keywordi < len(blockdict)-1 or havecomma:
                    string+=","
                string+=nl

            if block is not None:
                indent-=indent_unit
                string+= "".ljust(indent) + "}"
                if blocki < len(self.__entries)-1:
                    string+=","
                string += nl

        string+="}"
        return string

    def config_string(self,comments=True):
        """
        Print a config string representing the current object including
        comments (if comments==True). 
        """

        string=""
        indent_unit=3
        indent=0

        for blocki, block in enumerate(self.__entries.keys()):
            have_newline=False # have a forced extra newline in the loop
            if block is not None:
                string+= "".ljust(indent) + "\""+block+"\": {\n"
                indent+=indent_unit
            else:
                if blocki < len(self.__entries)-1:
                    have_newline=True

            blockdict=self.get_block(block)
            for keywordi, keyword in enumerate(blockdict.keys()):
                entry=self.get_entry(keyword,block=block)

                if comments and entry.comment is not None:
                    string += "".ljust(indent) + "# " + entry.comment + "\n"
                    string += "".ljust(indent) + keyword + " = " + entry.value + "\n"
                if keywordi < len(blockdict)-1 or have_newline:
                    string += "\n"

            if block is not None:
                indent-=indent_unit
                string += "}\n"
                if blocki < len(self.__entries)-1:
                    string += "\n"

        return string

    def __str__(self):
        return self.json_string(compact=True)

if __name__ == "__main__":
    def __test(prestring,actual,expected):
        if (expected != actual):
            raise SystemExit(prestring+ ": " + str(actual) + " where " + str(expected) + " was expected.")

    # Testing keyword_config_parser

    testfile = "/tmp/config_lib_tester.cfg"

    with open(testfile,"w") as f:
        f.write("# Here begins a one-line block\n"
                + "block { value=42 }\n"
                + "\n"
                + "# And a two-line block\n"
                + "block2 { val=43 \n"
                + " other = a } \n"
                + "# And a three-line block\n"
                + "block 3 {\n"
                +"      val=44 \n"
                + "} \n"
                + "\n"
                + "# and some content in no block\n"
                + "a=4\n"
                + "b=abc\n")

    print("testfile:")
    with open(testfile,"r") as f:
        print(f.read())
    print("---\n")

    k = keyword_config_parser()
    k.add_keyword("a",default="4",comment="a value")
    k.add_keyword("b",default="aaaa",comment="b value")
    k.add_keyword("c",default="1",comment="c value")
    k.add_keyword("value",default="19",comment="value of block",block="block")
    k.add_keyword("other",default="c",comment="other of block2",block="block2")
    k.add_keyword("val",default="d",comment="val of block 3",block="block 3")

    if k.get_value("a") != "4" or k.get_value("b") != "aaaa" or k.get_value("c") != "1":
        raise SystemExit("Error setting default values on top level")
    if k.get_value("value",block="block") != "19" \
            or k.get_value("val",block="block 3") != "d" \
            or k.get_value("other",block="block2") != "c":
        raise SystemExit("Error setting default values on section level")

    try:
        ret = k.get_value("val",block="block2")
        raise SystemExit("Was able to obtain val of block2 without error")
    except ValueError:
        pass

    try:
        k.parse(testfile)
        raise SystemExit("Was able to parse invalid config file")
    except InvalidConfigFileException as i:
        if not i.linenr == 5:
            raise
        pass

    # add remaining keyword:
    k.add_keyword("val",default="0",comment="val of block2",block="block2")

    try:
        k.parse(testfile)
    except InvalidConfigFileException as i:
        raise

    __test("After reading the file",k.get_value("a"),"4")
    __test("After reading the file",k.get_value("b"),"abc")
    __test("After reading the file",k.get_value("c"),"1")
    __test("After reading the file",k.get_value("value",block="block"),"42")
    __test("After reading the file",k.get_value("val",block="block2"),"43")
    __test("After reading the file",k.get_value("other",block="block2"),"a")
    __test("After reading the file",k.get_value("val",block="block 3"),"44")
     

    #------------------------------------------------------------------------

    print("Unit Test passed")
