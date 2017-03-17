# vi: set et ts=4 sw=4 sts=4:

# Python module of some helpful utils
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


def interpret_string_as_bool(string):
    import argparse
    """
    interpret the string as a bool
    if this is not possible, throw an argparse.ArgumentTypeError
    """
    s = string.lower()
    if s == "true": 
        return True
    if s == "1":
        return True
    if s == "false":
        return False
    if s == "0":
        return False
    raise argparse.ArgumentTypeError(string + "is not a valid boolean value, expected: true|false|0|1")

def interpret_string_as_file_size(string):
    import argparse
    import re
    """
    interpret a string of the form 

    integer[suffix]

    where suffix is case insensitive and one of

    b               bytes
    kib, kb, k      Kilo (1024) bytes
    mib, mb, m      Mega (1,048,576) bytes
    gib, gb, g      Giga (1,073,741,824) bytes
    tib, tb, t      Tera (1024)^4 bytes

    and return number of bytes
    """
    if not isinstance(string,str):
        raise TypeError("Cannot parse type " + type(string))

    # extract integer:
    match = re.match("^[0-9.]*",string)
    if len(match.group()) < 1:
        raise argparse.ArgumentTypeError(string + " is not a valid size value: Expected integer before size suffix")

    nbytes = float(match.group())

    # now find multiplication factor
    unit = string[match.end():].lower()
    if len(unit) == 0:
        return int(nbytes)

    unit = unit.lower()

    if unit == "b":
        nbytes = nbytes
    elif unit in [ "kb", "kib", "k" ]:
        nbytes = nbytes*1024
    elif unit in [ "mb", "mib", "m" ]:
        nbytes = nbytes*1024*1024
    elif unit in [ "gb", "gib", "g" ]:
        nbytes = nbytes*1024*1024*1024
    elif unit in [ "tb", "tib", "t" ]:
        nbytes = nbytes*1024*1024*1024*1024
    else:
        raise argparse.ArgumentTypeError("\"" +string + "\" is not a valid size value: Expected one of b,kb,kib, ... tb, tib as size suffix")
    return int(nbytes)


def interpret_string_as_time_interval(string):
    import argparse
    import re
    """
    interpret a string of the form 

    [[[days:]hours:]minutes:]seconds
    or
    integer[suffix]

    where suffix is case insensitive and one of

    s               seconds
    m               minutes
    h               hours
    d               days
    w               weeks
    y               years

    and return number of seconds
    """
    if not isinstance(string,str):
        raise TypeError("Cannot parse type " + type(string))

    # first see which mode we operate in:
    if string.count(":") == 0:
        # extract integer:
        match = re.match("^[0-9]*",string)
        if len(match.group()) < 1:
            raise argparse.ArgumentTypeError(string + " is not a valid time value: Expected integer before time suffix")

        n = int(match.group())

        # now find multiplication factor
        unit = string[match.end():]
        if len(unit) == 0:
            return n
        unit = unit.lower()

        if unit == "s":
            return n
        elif unit == "m":
            return n*60
        elif unit == "h":
            return n*60*60
        elif unit == "d":
            return n*60*60*24
        elif unit == "w":
            return n*60*60*24*7
        elif unit == "y":
            return n*60*60*24*365
        else:
            raise argparse.ArgumentTypeError(string + " is not a valid time value: Expected one of s,m,h,d,w,y as time suffix")
    else:
            li=string.split(":")

            #[[[days:]hours:]minutes:]seconds

            n = int(li[-1])
            if len(li) > 1:
                n += 60*int(li[-2])
            if len(li) > 2:
                n += 60*60*int(li[-3])
            if len(li) > 3:
                n += 24*60*60*int(li[-4])
            return n
