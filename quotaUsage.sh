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
# file COPYING or at <http://www.gnu.org/licenses/>.

HOST="ccserv1"

if [ "$HOSTNAME" != "$HOST" ];then
	QUOTA="ssh $HOST quota"
else
	QUOTA="quota"
fi

$QUOTA | awk 'NR == 3 {
	printf("quota usage:  %6.2f%%    (%2iG of %2iG used)\n", $2/$3*100,$2/1000/1000,$3/1000/1000)
	}'
