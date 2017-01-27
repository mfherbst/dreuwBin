_this_path_on() {
	local cur=${COMP_WORDS[COMP_CWORD]}
	local prev=${COMP_WORDS[$((COMP_CWORD-1))]}
	COMPREPLY=()
	local flags="-h --help -p --prefix -s --strip"

	if [[ "$prev" == "-s" || "$prev" == "--strip" ]]; then
		# Complete directories
		COMPREPLY=( $( compgen -d -- "$cur" ) )
		return
	fi

	if [[ "$cur" == -* ]]; then
		COMPREPLY=( $( compgen -W "$flags" -- "$cur" ) )
		return
	fi

	_known_hosts_real -a "$cur"

	if [[ -z "$cur"  ]]; then
		COMPREPLY+=( $( compgen -W "$flags" -- "$cur" ) )
		return
	fi

	return
}
complete -F _this_path_on this_path_on
