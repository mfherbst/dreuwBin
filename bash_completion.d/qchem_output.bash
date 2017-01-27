_qchem_output() {
	local cur
	cur=${COMP_WORDS[COMP_CWORD]}

	COMPREPLY=()

	local HELPOPT="--help -h"
	local ACTIONS="--opt_geo --summary --std_orientation_xyz --extract_input_molecule"
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
