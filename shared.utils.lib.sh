# Library of common and useful shell functions
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

waitpid() {
	#wait until pid finishes
	for pid in "$@"; do
		while kill -0 "$pid"; do
			sleep 0.5
		done
	done
}

find_up() {
	#find a file in this directory or any parent directory
	#$1: File to find
	#returns 1 if root reached and file not found.

	if [ -f "$1" ]; then
		echo "$1"
		return 0
	fi

	[ $PWD = "/" ] && return 1

	(
		cd ..
		P=`find_up "$1"` || return 1
		echo "../$P"
		return 0
	)
}

resolve_link() {
	#resolve a symbolic link recursively until full relative path to the file is found
	#return 1 if link is broken

	if [ ! -L "$1" ]; then
		#we resolved it:
		echo "$1"
		return 0
	fi
	
	local NEWLINK
	if ! NEWLINK=$(readlink "$1"); then
		return 1
	fi

	resolve_link "$NEWLINK"
}

is_email_valid() {
	#$1: An email address to check
	echo -n "$1" | grep -q -E "^[A-Za-z0-9._%+\-\!#$&'*/=?^\`{|}~]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,6}$"
}

remove_extension() {
	#$1 a path
	echo ${1%.*}
}
