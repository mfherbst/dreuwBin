from queuing_system.pbs import pbs
from shared_utils_lib import which

def guess_queuing_system(fallback=pbs, silent=False):
    if (which("qsub") is not None):
        return pbs()
    else:
        fb=fallback()
        if not silent:
            print("Warning: Could not autodetermine the queing system on your machine. "
                +"Using fallback \"" + fb.name() + "\".")
        return fb

