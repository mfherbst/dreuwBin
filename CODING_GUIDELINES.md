# Coding guidelines for dreuwBin
1. Scripts should be general. They should work for all users of 
   the Dreuw group. So no configuration of any kind in the script
   itself. Use an external config file for that purpose.

2. Code should be clear and sound with enough comments such that
   it is easy to understand what is going on.

3. Config files should be expected in the folder ``$HOME/.dreuwBin`` 
   -- ideally in a file that has a name similar to the name of 
   the script itself (ie. if the script is ``blubber.sh``, the config 
   is ``blubber.cfg``).

4. Input provided via (config-)files or commandline flags should be 
   checked for basic sanity before use, ie. does the file exist,
   is the number in the right range, ...

5. If the action of the script is non-obvious, then a ``-h`` flag
   should be provided that spits out a (hopefully) complete
   documentation of the available flags and features.

   *NOTE:* Any script taking a single commandline argument or one
   which has more than a few lines of code should be 
   considered to be "non-obvious".

6. If the script fails it should exit with a return code != 0
   (eg. call ``exit 1``). All error output should be written to 
   stderr, whilst normal output goes to stdout.

7. Temporary files and folders should be cleaned up properly 
   before exiting (regardless if the script execution fails
   or is successful)

8. If in doubt ask the user or abort. Avoid Philippians or 
   Danielisms. ;)
