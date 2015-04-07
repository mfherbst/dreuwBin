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
	#returns 1 if root reached.

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
