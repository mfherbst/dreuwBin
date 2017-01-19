#!/usr/bin/python

from optparse import OptionParser, SUPPRESS_HELP
import subprocess
import os
import sys


allowedHosts = range(1, 16)


class Error(Exception):
	"""is the base class of visible errors from this script."""
	pass


class HostsError(Error):
	"""is raised when encountering unexpected nodes etc."""
	pass


class ExecutionError(Error):
	"""is raised when trying to delete scratch files on non-knecht hosts."""
	pass

def getUserScratchDirs():
	dirs = []
	dirs.append(os.path.join("/scratch", os.getenv("USER")))
	dirs.append(os.path.join("/lscratch", os.getenv("USER")))
	dirs.append("/scratch")
	dirs.append("/lscratch")
	return dirs


def absPathOfThisScript():
	return os.path.abspath(sys.argv[0])


def parseHostsString(string):
	hosts = []
	tokens = string.split(",")
	for t in tokens:
		if "-" in t:
			fromTo = t.split("-")
			if not len(fromTo) == 2:
				raise HostsError("Bad format in hosts token '{:s}'.\n".format(
					t))
			try:
				hosts.extend(range(int(fromTo[0]), int(fromTo[1])+1))
			except ValueError:
				raise HostsError("Can't parse hosts token '{:s}'.\n".format(
					t))
		else:
			try:
				hosts.append(int(t))
			except ValueError:
				raise HostsError(
					"Don't know what to do with hosts token '{:s}'.\n".format(t))
	for h in hosts:
		if not h in allowedHosts:
			raise HostsError("No such host: {:d}.\n".format(h))
	hostnames = ["Knecht{:0>2d}".format(i) for i in sorted(list(set(hosts)))]
	return hostnames


def parseCommandline():
	parser = OptionParser(usage="%prog [options] [<hostname> [<hostname> ...]]"
		"\n\nlogs in to specified hosts and deletes files or directories located"
		"\nin the user scratch directories"
		"\n{:s} and {:s}."
		"\nHostnames given as command line arguments supersede hosts specified"
		"\nusing the --knechte option.".format(", ".join(getUserScratchDirs()[:-1]),
		getUserScratchDirs()[-1]))
	parser.add_option("--dry-run", help="Do not actually delete scratch files.",
		action="store_true", default=False, dest="dryRun")
	parser.add_option("-f", "--force", help="Don't ask before deleting"
		"\nfiles/dirs.  Don't use this option if you have running jobs or want to keep"
		"\nparticular scratch files.", dest="force", action="store_true",
		default=False)
	parser.add_option("-k", "--knechte", help="Only delete files on specified"
		"\nnodes.  Pass a comma-separated list of numbers.  Ranges using '-' are also"
		"\nallowed.  Example:  KNECHT_LIST=1,3-5,7,9 will cause this script to delete"
		"\nscratch files on knecht01, knecht03, knecht04, knecht05, knecht07 and"
		"\nknecht09.  The default is to delete files on all nodes, i. e. knecht01"
		"\nthrough knecht15.", action="store", default="1-15", type="str",
		dest="hostsString", metavar="KNECHT_LIST")
	# hidden option for execution on nodes
	parser.add_option("--delete-scratch-files-here", help=SUPPRESS_HELP,
		default=False, action="store_true", dest="doDelete")
	opts, args = parser.parse_args()
	if len(args) > 0:
		opts.hosts = sorted(list(set(args)))
	else:
		opts.hosts = parseHostsString(opts.hostsString)
	return opts


def getHostname():
	try:
		return open("/etc/hostname").read().strip()
	except IOError:
		p = subprocess.Popen(["/usr/bin/hostname",], stdout=subprocess.PIPE)
		return p.communicate()[0]


def deleteFileOrDir(fileOrDir, opts):
	if os.path.isdir(fileOrDir):
		tokenType = "directory"
	elif os.path.isfile(fileOrDir):
		tokenType = "file"
	else:
		return
	if not opts.force:
		sys.stdout.write("\t{:s}: Delete '{:s}'? (y/N) > ".format(
			getHostname(), fileOrDir))
		sys.stdout.flush()
		ret = raw_input("")
		if not ret.strip().lower().startswith("y"):
			return
	# now delete file or dir <fileOrDir>
	cmd = ["rm", "-rf", fileOrDir]
	sys.stdout.write("\tDeleting '{:s}'.\n".format(fileOrDir))
	sys.stdout.flush()
	if not opts.dryRun:
		p = subprocess.Popen(cmd)
		p.wait()


def isOwnedByMe(path):
	return os.getuid() == os.stat(path).st_uid


def collectScratchFilesAndDirs():
	userScratchDirs = getUserScratchDirs()
	filesAndDirs = []
	for s in userScratchDirs:
		try:
			os.stat(s)
			if not os.path.isdir(s):
				continue
		except OSError:
			continue
		filesAndDirs.extend([os.path.join(s, i) for i in os.listdir(s)
			if isOwnedByMe(os.path.join(s, i)) and not os.path.join(s, i) in userScratchDirs])
	return filesAndDirs


def deleteScratchFilesAndDirs(opts):
	hostname = getHostname()
	if not "knecht" in hostname.lower():
		raise ExecutionError("Expected to run on a knecht."
			"  Found to be executed on host '{:s}' instead.\n".format(
			hostname))
	for fileOrDir in collectScratchFilesAndDirs():
		deleteFileOrDir(fileOrDir, opts)


def processHost(hostname, opts):
	sys.stdout.write("Processing host: {:s}\n".format(hostname))
	sys.stdout.flush()
	cmd = [
		"/usr/bin/ssh",
		hostname,
		absPathOfThisScript(),
		"--delete-scratch-files-here"
	]
	if opts.force:
		cmd.append("--force")
	if opts.dryRun:
		cmd.append("--dry-run")
	p = subprocess.Popen(cmd)
	p.wait()


def processHosts(opts):
	for h in opts.hosts:
		processHost(h, opts)


def main():
	opts = parseCommandline()
	if opts.doDelete:
		deleteScratchFilesAndDirs(opts)
		sys.exit(0)
	else:
		processHosts(opts)


if __name__ == "__main__":
	main()

