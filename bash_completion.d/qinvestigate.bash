_qinvestigate() {
	local prev=${COMP_WORDS[$((COMP_CWORD-1))]}
	local cur=${COMP_WORDS[COMP_CWORD]}
	local commands='alias help joblist summary login top scratch delete'
	local options='-h --help --add-sshkey --no-add-sshkey'
	local aliases='' #TODO implement

	case "$prev" in
		"--")
			#only commands may follow
			COMPREPLY=( $( compgen -W "$commands" -- "$cur" ) )
			return
			;;
		"-"*|${COMP_WORDS[0]})
			#complete to everything
			COMPREPLY=( $( compgen -W "-- $commands $options $aliases" -- "$cur" ) )
			return 
			;;
		*)
			#already in command block => complete job ids or names
			COMPREPLY=( $( compgen -W "$(qstat -u $USER | awk -v "user=$USER" '$2 == user { printf "%s %s ", $1, $4 }')" -- "$cur") )
			return
			;;
	esac

   	unset prev cur commands options aliases
}
complete -F _qinvestigate qinvestigate
