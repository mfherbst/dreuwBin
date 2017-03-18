. ${DREUWBIN_BASH_COMPLETION_DIR}/general_send_job.bash

_orca_send_job() {
	local QCHEMOPT='--out --version'
	_sendscript_completion "$QCHEMOPT"
}

complete -o filenames -F _orca_send_job orca_send_job
