_qchem_send_job() {
	local cur
	cur=${COMP_WORDS[COMP_CWORD]}

	COMPREPLY=()

	local JOBSCRIPTOPT='-h --help --qsys-args --workdir --scratchdir --mail --wt --mem --vmem --np --name --priority --queue --merge_stdout_stderr --send_email_end --send_email_begin --send_email_error -q -d -m'
	local QCHEMOPT='--out --save --savedir --np-to-qchem --nt-to-qchem --version --perf'
	local CLISCRIPTOPT='--cfg --send'

	if [[ "$cur" == -* ]]; then
		COMPREPLY=( $( compgen -W "$JOBSCRIPTOPT $QCHEMOPT $CLISCRIPTOPT " -- "$cur" ) )
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

complete -o filenames -F _qchem_send_job qchem_send_job
