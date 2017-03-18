_sendscript_completion() {
	local cur
	cur=${COMP_WORDS[COMP_CWORD]}

	COMPREPLY=()
	local JOBSCRIPTOPT='-h --help --qsys-args --workdir --scratchdir --mail --wt --mem --vmem --np --name --priority --queue --merge_stdout_stderr --send_email_end --send_email_begin --send_email_error -q -d -m'
	local BUILDERMAINOPT='--cfg --send'

	COMPREPLY+=( $( compgen -W "${JOBSCRIPTOPT} ${BUILDERMAINOPT} $@ " -- "$cur" ) )

	local OLDIFS="$IFS"
	IFS="
	"
	#create reply based on all files or folders:
	COMPREPLY+=( $( compgen -f  -- "$cur" ) )

	IFS="$OLDIFS"
	unset cur OLDIFS
}

