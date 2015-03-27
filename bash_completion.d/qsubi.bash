_qsubi() {
	local cur
	prev=${COMP_WORDS[$((COMP_CWORD-1))]}
	cur=${COMP_WORDS[COMP_CWORD]}

	#if prev is option that reqires an arg: return
	[[ "$prev" == @(--np|--wt|--mem) ]] && return 

	#generate reply using options	
	COMPREPLY=( $( compgen -W '-h --help --np --wt --mem' -- "$cur" ) )
}

complete -F _qsubi qsubi
