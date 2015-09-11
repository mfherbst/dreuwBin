_qchem_output() {
	local cur
	local prev
	cur=${COMP_WORDS[COMP_CWORD]}

	COMPREPLY=()

	local HELPOPT="--help -h"
	local ACTIONS="--extract_opt_geo --summary"
	if [[ "$cur" == -* ]]; then
		COMPREPLY=( $( compgen -W "$HELPOPT $ACTIONS " -- "$cur" ) )
		return 0
	fi

	local OLDIFS="$IFS"
	IFS="
	"

	#create reply based on all files or folders:
	COMPREPLY=( $(compgen -f -- "$cur") )

	IFS="$OLDIFS"
	unset cur OLDIFS
}

complete -o filenames -F _qchem_output qchem_output
