# Library to allow easy writing and parsing of config files
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

###########################################################################
########################
#-- Global Variables --#
########################

# BASH_SOURCE is a bash array containing the full paths of all files in the
# call stack. We expect this library to be sourced directly from the main script
# In other words ${BASH_SOURCE[0]} is the path to this script and
# ${BASH_SOURCE[1]} is the path to the script sourcing this library
if [ -z "${BASH_SOURCE[1]}" ]; then
	echo "Cannot source this script directly." >&2
	echo "Can only be used as a library from a script." >&2
	[ "$0" == "bash" ] && return 1
	exit 1
fi

CONFDIR="$HOME/.dreuwBin"
CONFFILE="$CONFDIR/$(basename "${BASH_SOURCE[1]}" ".sh").cfg"

###########################################################################
#########################
#-- Config management --#
#########################
ConfigGet() {
	# get stream of the config file to stdout
	# comments are removed automatically
	# returns 1 if no file found.
	[ ! -f "$CONFFILE" ] && return 1
	< "$CONFFILE" sed -e "s/#.*$//g" -e "s/[[:space:]]*$//g" -e "s/^[[:space:]]*//g" -e "/^$/d"
}

ConfigParseStdin() {
	# parses STDIN into a string of bash commands that
	# sets variables specified on $@ to the values given
       	# on STDIN
	# $@: Allowed options
	# returns 0 if no errors occurred, else 1
	# prints a message to stderr if an option is encountered
       	# that is not allowed
	# 
	# Example: 
	# STDIN has the content
	# CURRENCY=dollar
	# BLUBBER="234"
	#
	# and we execute 
	#    RES=$(ConfigParseStdin CURRENCY BLUBB) && eval "$RES"
	# than after the execution the value of the variable BLUBB
	# is unchanged, whereas CURRENCY now contains the string
	# "dollar". An error is printed because BLUBBER is not an
	# allowed option.
	#
	# The syntax of options on STDIN is
	# <OPTIONNAME> = "<OPTIONVALUE>"
	# Note that both spaces and the " are optional and <OPTIONVALUE>
	# may not contain any of the three characters " = '

	if [ -z "$1" ]; then
		# no options at all
		local STDIN=$(cat)
		[[ -z "$STDIN" ]] && return 0
		echo "No options given, but content on stdin is provided"
		return 1
	fi

	awk -v "options=$*" "

		BEGIN {
			# split options string:
			maxind = split(options,ops)

			# build matchstring
			matchstring=\"^(\" ops[1]
			for (ind=2; ind <= maxind; ++ind) {
				matchstring=matchstring \"|\" ops[ind]
			}
			matchstring=matchstring \")[[:space:]]*=[[:space:]]*\\\"?[^\\\"'=]+\\\"?$\"

			FS=\"=\"
			res=0 #return value
		}	

		\$0 ~ matchstring {
			# remove tailling or leading \"
			sub(/^\"/,\"\",\$2)
			sub(/\"$/,\"\",\$2)

			print \$1 \"='\" \$2 \"'\" 
			next
		}

		{
			print \"Unknown option: \" \$1  > \"/dev/stderr\"
			res=1
			next
		}

		END {
			exit res
		}
	"
}

ConfigParseBlock() {
	# Uses ConfigParseStdin to parse the Block obtained via
	# ConfigGetBlock.
	# $1: Block name
	# $2 to $n: Allowed options
	# returns 1 if no config file was found
	# returns 2 if the block cannot be found
	# returns 8 if the block contained invalid options
	# prints a message to stderr in the latter case as well.

	local BLOCK
	local RET
	BLOCK=$(ConfigGetBlock "$1")
	RET=$?
	[[ $RET -ne 0 ]] && return $RET

	shift
	local PARSED
	if ! PARSED=$(echo -n "$BLOCK" | ConfigParseStdin "$@"); then
		return 8
	fi
	eval "$PARSED"
}

ConfigGetBlock() {
	# get stream of the block of the config file corresponding
	# to the configuration for the block named $1
	# returns 1 if no config file found.
	# returns 2 if the block cannot be found
	
	[ ! -f "$CONFFILE" ] && return 1
	[ -z "$1" ] && return 2

	local SECTION=$1
	ConfigGet | awk -v "section=$SECTION" '
		BEGIN { pr=0; foundit=0 }
	
		# NOTE: Space at beginning and end was removed in ConfigGet

		# Just a single line in this block
		$0 ~ "^" section "[[:space:]]*{.*}$" {
			gsub("^[[:space:]]*" section "[[:space:]]+{[[:space:]]*","")
			gsub("}$","")
			if ($0 != "") print
			foundit=1
			exit
		}

		# Beginning of a section
		$0 ~ "^" section "[[:space:]]*{" {
			gsub("^[[:space:]]*" section "[[:space:]]+{[[:space:]]*","")
			if ($0 != "") print
			pr=1
			foundit=1
			next
		}

		# End of the section
		pr == 1 && $0 ~ "}$" {
			gsub("}$","")
			if ($0 != "") print
			pr=0
			exit
		}

		# Between beginning and end
		pr == 1 && $0 != ""

		END {
			if (foundit == 1) {
				exit 0
			}
			exit 2
		}
	'
	return $?
}

ConfigPut() {
	#writes a stream to the config file
	[ ! -d "$CONFDIR" ] && mkdir "$CONFDIR"
	cat > "$CONFFILE"
}

ConfigPath() {
	#echos the path of the config.
	echo "$CONFFILE"
}
