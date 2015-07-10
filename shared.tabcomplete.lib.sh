# Library to allow easy implementation of tab completion on readline
# based input
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
#--   Global Stuff   --#
########################

# set this to allow @( ) and ?( ) patterns in case ... and other pathname expansions
shopt -qs extglob

# switch to vi or emacs line editing mode
# (needed to allow the binding of \t to "tabcomplete" and hence tab completion)
if set -o | awk '$1 == "emacs" { if ($2 =="off") exit 0; exit 1}'; then
	#no emacs editing mode, hence
	set -o vi
else
	set +o vi
fi

###########################################################################
###############################
#--  First word completion  --#
###############################

# GLOBAL variable containing the last execution time of tabcomplete
# where only a partial completion of the command was achieved
__TAB_PARTIAL_LASTEXEC=0
declare -a TAB_FIRST_WORDS
tabcomplete_first_word() {
	# try to complete the READLINE_LINE
	# needs the possible matches in the global array TAB_FIRST_WORDS
	
	# discard tab if no input on line
	[ -z "$READLINE_LINE" ] && return

	# return if no words to match
	[ -z "${TAB_FIRST_WORDS[*]}" ] && return

	# remove leading whitespace:
	local NORMALISED="${READLINE_LINE##*( )}" #requires extglob again

	# if NORMALISED contains a space, we are already past the name of the 
	# qchem scrept
	# => quit
	[[ $NORMALISED == *" "*  ]] && return

	# try to match command. If no match -> return
	local MATCHES
	MATCHES=$(echo "${TAB_FIRST_WORDS[@]}" | tr ' ' '\n'  | grep "^$NORMALISED") || return

	# find longest substring in matches:
	local LONGCOMMON
	# In the awk script we go through all matches and determine
	# the longest common sequence of characters at the start of
	# all matches
	LONGCOMMON=`echo "$MATCHES" | awk '
		function commonstart(a,b) {
			# function to determine the longest sequence of characters
			# that starts both strings

			#determine minimum length of both strings
			len=length(a)
			if (length(b) < len) {
				len=length(b)
			}

			#determine longest common start:
			for(i = 1; i <= len; ++i) {
				if ( substr(a,i,1) != substr(b,i,1) ) {
					return substr(a,0,i-1)
				}
			}
			return substr(a,0,len)
		}
	
		BEGIN {comm="" };
		NR == 1 { comm=$0; next };
		NR > 1 { comm=commonstart(comm,$0); };
		END { print comm }
		'
	`
	
	if [[ $(echo -n "$MATCHES" | grep -c '^') == 1 ]]; then
		#single match: Tab complete
		READLINE_LINE="$MATCHES "
		READLINE_POINT=$(( ${#MATCHES} + 1))
		return
	fi

	# fill up to common chars:
	READLINE_LINE="$LONGCOMMON"
	READLINE_POINT=${#MATCHES}

	# pressed tab twice within 3 seconds
	if (( $(date +%s) - __TAB_PARTIAL_LASTEXEC < 4  )); then
		#print list of matching commands
		echo -n "$MATCHES" | tr '\n' '   '
		echo
	fi
	__TAB_PARTIAL_LASTEXEC=$(date +%s)
	return
}
