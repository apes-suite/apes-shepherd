import subprocess
import os
import logging

def runcmd(*args, logfile = None, errfile = None, **kwargs):
    ''' Encapsulating subprocess.run, always capturing the output
        and writing it to the given files.
    '''

    ignorekeys = ('stdout', 'stderr', 'capture_output')
    filteredargs = {k:v for (k,v) in kwargs.items() if k not in ignorekeys}
    proc = subprocess.run(*args, capture_output=True, **kwargs)
    print(proc.stdout.decode('utf-8'))
    print(proc.stderr.decode('utf-8'))
    if logfile:
        logfile.write(proc.stdout.decode('utf-8'))
    if errfile:
        errfile.write(proc.stderr.decode('utf-8'))


def build_waf(variant='build', confopts='', solver_dir=None,
        logfile=None, error_file=None):
    ''' Build the variant of the project in solver_dir via waf.
    (str, str, str, str, str) -> None
    The project will be cleaned and configured with the current sources in
    the directory. Configuration options can be passed in via the confopts
    argument.
    '''

    if logfile:
        logfile.write("#####################  CONFIGURE  #####################\n")
        try:
            logfile.flush()
        except Exception:
            logging.exception('Flushing file failed')
            pass

    runcmd(["bin/waf", "cleanall"], logfile = logfile, errfile = error_file, cwd=solver_dir)
    runcmd(["bin/waf", "configure"] + confopts.split(),
           logfile = logfile, errfile = error_file, cwd=solver_dir)


    ## Build the project:
    if logfile:
        logfile.write("#####################  BUILD  #########################\n")
        try:
            logfile.flush()
        except Exception:
            logging.exception('Flushing file failed')
            pass

    runcmd(["bin/waf", variant], logfile = logfile, errfile = error_file, cwd=solver_dir)
