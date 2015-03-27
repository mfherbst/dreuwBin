#!/bin/bash

HOST="ccserv1"

if [ "$HOSTNAME" != "$HOST" ];then
	QUOTA="ssh $HOST quota"
else
	QUOTA="quota"
fi

$QUOTA | awk 'NR == 3 {
	printf("quota usage:  %6.2f%%    (%2iG of %2iG used)\n", $2/$3*100,$2/1000/1000,$3/1000/1000)
	}'
