#!/bin/bash

# Script to print your current usage of the quota in a handy way
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

HOST="ccserv1"

check_ssh_config() {
	if [ -f "$HOME/.ssh/config" ] && ! < $HOME/.ssh/config grep -q "Host $HOST"; then
		cat <<-EOF
			This script can only work properly if there exists a 
			      Host $HOST
			         Hostname $HOST.domain
			         Port <Portnumber>
			section in the $HOME/.ssh/config file. 
			Please add this section
		EOF
		exit 1
	fi
} && check_ssh_config


if [ "$HOSTNAME" != "$HOST" ];then
	QUOTA="ssh $HOST quota"
else
	QUOTA="quota"
fi

$QUOTA | awk 'NR == 3 {
	printf("quota usage:  %6.2f%%    (%4.1fG of %4.1fG used)\n", $2/$3*100,$2/1000/1000,$3/1000/1000)
	}'
