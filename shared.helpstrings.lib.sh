# Library to allow the inline addition of help strings to bash functions
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

help_string() {
	#marker function that does absolutely nothing
	:
}

print_help_for_command() {
	# Print the help that has been inline set to a function using
	# the help_string marker function.
	#$1: function name

	local FCTNAME="$1"
	local DECLARE
	DECLARE=`declare -f -p $FCTNAME` || return 1
	echo "$DECLARE" | awk '
		BEGIN { pr=0 }
		/help_string/ && /";[[:space:]]*$/ {
			# a single line help. Just print it all.
			gsub(/^.*help_string[[:space:]]*"/,"")
			gsub(/";[[:space:]]*$/,"")
			print
			exit 0
		}

		/help_string/ {
			#beginning of the help: set flag to print other lines and remove unneccessary stuff.
			gsub(/^.*help_string[[:space:]]*"/,"")
			print
			pr=1
			next
		}
		
		/";[[:space:]]*$/ {
			#end of the help. Print last bit and exit
			gsub(/^[[:space:]]*/,"")
			gsub(/";[[:space:]]*$/,"")
			print
			pr=0
			exit 0
		}
		
		pr==1 {
			#line in between: Remove leading space
			gsub(/^[[:space:]]*/,"")
			print
			next
		}
	'
	return 0
}

