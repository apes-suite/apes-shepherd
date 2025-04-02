#!/usr/bin/env python3
###############################################################################
# AUTHOR: KANNAN MASILAMANI
###############################################################################
#IMPORTANT NOTE: DO NOT MODIFY THIS FILE.
#JUST USE IT AS TEMPLATE TO CREATE YOUR OWN PYTHON SCRIPT
# This python script generates several jobscripts and lua files based on input
# parameters given in the file params.py. This can be used to-
# 1. Generate lua scripts for various parameters (for parameter study)
#    in the param file
# 2. Generate job scripts for various parameters (eg. for performance study)
# 3. Automate any sequencial and non-sequencial jobs
# Apart from generating two above mentioned files (lua files and jobscripts),
# option can also be specified to
# run the lua files locally or also submit all the generated jobscripts.
# Find more details in the README file
##############################################################################

##############################################################################

def main():
    """ Main execution of the shepherd script. """
    ##----------  IMPORT LIBRARIES  ------------------------------------------
    # load shepherd library files
    from shepherd.lib.auxiliary import say_hello, load_inputfile, exit_shepherd, init_logging
    
    ## initialize logging_level and logging_file
    init_logging()
    
    ## shepherd log header
    say_hello()
    
    ## load input file
    params = load_inputfile()

    import shepherd.executor

    shepherd.executor.process_input()

    ## finished shepherd successfully
    exit_shepherd(0)
