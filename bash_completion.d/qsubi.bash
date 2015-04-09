_qsubi() {
	local cur
	local prev
	prev=${COMP_WORDS[$((COMP_CWORD-1))]}
	cur=${COMP_WORDS[COMP_CWORD]}

	#if prev is option that reqires an arg: return
	[[ "$prev" == @(--np|--wt|--mem) ]] && return 

	#generate reply using options	
	COMPREPLY=( $( compgen -W '-h --help --np --wt --mem' -- "$cur" ) )

	unset cur prev
}

complete -F _qsubi qsubi
