# dreuwBin

## Getting the repository

As usual just clone. The best place to stick the repository is your
home directory. In order to this just run:
```
cd $HOME
git clone https://github.com/mfherbst/dreuwBin.git
```
I will assume for this ``README.md``, that this is exactly what you have
done and give the instructions accordingly.

## Setup
- The recommended way to setup is using the **setup script** ``setPATH.sh``.
In order to do so, you should add the following line at the end of your
``$HOME/.bashrc``:
```
source $HOME/dreuwBin/setPATH.sh
```
Of course you can alternatively just copy or link individual files
to your ``$HOME/bin`` folder or similar instead.

- If you want to use **Tab completion** you should furthermore 
create the file ``$HOME/.bash_completion``, if it does not exist,
and add to it:
```
for dir in dreuwBin; do
	[[ -f $HOME/$dir/enable.bash_completion && -r $HOME/$dir/enable.bash_completion ]] \
	 && source $HOME/$dir/enable.bash_completion
done
```

## Contained scripts and their features

### ``qchem_send_job`` and ``orca_send_job``
- Facilitate sending jobs to a cluster for performing calculations.
- The scripts parse the calculation input file and automatically determine the
  required queuing system parameters for each individual job.
- An appropriate job script is produced, but may be reviewed by the user
  before sending it off to the job queue.
- The way the queuing system parameters are determined is very flexible and may be
  influenced by the user in the follwing ways:
  - Commandline flags
  - Native parameters in the calculation program's input file
    (e.g. ``threads`` or ``memtotal`` for Q-Chem or ``%pal`` sections for ORCA)
  - Special ``QSYS`` directives (e.g. for walltime and memory), which
    may be placed in the input file as well, but are transparent to the
    program eventually executed.
  - A global configuration file with defaults for walltime, ...

### ``send_command``
- Send a command or a script to a cluster
- Optionally supply further files to copy to the cluster in order to perform the job.
- For example
```
send_command --copy blubba "cat blubba"
```
  would first copy the file `blubba` to the compute cluster and then execute `cat blubba`,
  i.e. the job's output file would contain the content of `blubba`.

### ``qinvestigate``
- Interactive PBS queuing system analysis and diagnosis toolkit.

### ``this_path_on``
- Login to a different host, but preserving the working directory
- I.e. we login and automatically cd to the same directory as locally.

### ``look4bas``
- Lookup and download Gaussian basissets
- See [github.com/mfherbst/look4bas](https://github.com/mfherbst/look4bas) for detauls.

## Submitting scripts
The best way to do this is via **Pull Request** on github.
Note that the request will only be merged if your changes satisfy the
[coding guidelines](CodingGuidelines.md).

## Authors
- For a list of authors and their contributions see [AUTHORS.md](AUTHORS.md).
