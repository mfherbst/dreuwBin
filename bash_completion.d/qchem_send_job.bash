. ${DREUWBIN_BASH_COMPLETION_DIR}/general_send_job.bash

_qchem_send_job() {
	local QCHEMOPT='--out --save --savedir --np-to-qchem --nt-to-qchem --version --perf'
	_sendscript_completion "$QCHEMOPT"
}

complete -o filenames -F _qchem_send_job qchem_send_job
