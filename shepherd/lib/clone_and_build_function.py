from shepherd.lib.build_steering import *
import shutil
import zlib
import traceback
import logging

def base36encode(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, int):
        raise TypeError('number must be an integer')

    base36 = ''
    sign = ''

    if number < 0:
        sign = '-'
        number = -number

    if 0 <= number < len(alphabet):
        return sign + alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return sign + base36



def clone_build(solver, revision='', variant='build', confopts = '',
        solver_dir=None, git_clone_source='', clone_build_out='',
        clone_build_err='', exe_cache='shepherd_executables'):

    ''' Return path to executable, and create it if needed.
    (str, str, str, str, str, str, str, str) -> (str)
    This function returns the path of the executable identified by:
    solver   -- the name of the solver executable
    revision -- mercurial revision of the source code to use for the
              executable. The revision can be defined in terms of git
              revsets (will just be passed on to git checkout -f)
              Note: an empty revision will update to the latest revision
                    on the current branch, to keep the current version
                    use revision = '.'
              default: ''
    variant  -- the waf variant to build, default: 'build'
    confopts -- options to pass on to waf configure, default: ''

    The executable will be put into the 'shepherd_executables' directory in
    the current working directory, which is created if it does not exist yet.
    If an executable with the same identification already exists, that one is
    used without rebuilding the executable.
    To allow a concise distinguishing by the configuration options, the
    zlib.adler32 checksum of the confoptions argument will be used in the
    executable name. To easily look up the meaning of these hashes, a file
    with the actual options and the name with the actual hash is written
    alongside with the executable.
    In total the executable name will follow this pattern:

    <exe_cache>/<solver>/<revision>/<variant>-<confopts>

    Further options:
    solver_dir      -- directory with the checked out repository of the solver
                     default: None (which would mean the current directory)
    git_clone_source -- URL to clone and pull updates from, if this is empty
                     no attempts to pull or clone are made.
    clone_build_out -- File to write the output to.
    clone_build_err -- File to write the errors to.
    exe_cache -- directory to store executables in

    The returned value is the absolute path to the executable that matches
    the desired id.
    '''
    import sys
    import tempfile

    if clone_build_out == '':
        logfile = tempfile.TemporaryFile(mode="w")
    else:
        logfile = open(clone_build_out, 'a')

    if clone_build_err == '':
        errfile = tempfile.TemporaryFile(mode="w")
    else:
        errfile = open(clone_build_err, 'a')


    logfile.write("######################################################\n")
    logfile.write("####################  NEW JOB  #######################\n")
    logfile.write("######################################################\n")


    if git_clone_source != '':
        # If a clone source is provided, attempt to get the latest changes from
        # it.
        if not solver_dir or os.path.exists(solver_dir):
            runcmd(['git', 'pull', '--recurse-submodules'], cwd=solver_dir)
        else:
            logging.info("Cloning {0} from {1}\n".format(solver, git_clone_source))
            runcmd(['git', 'clone', '--recurse-submodules', git_clone_source, solver_dir])

    if os.path.exists(solver_dir or '.'):
        gitupC = [arg for arg in 'git checkout --recurse-submodules -f'.split() + [revision] if arg]
        runcmd(gitupC, cwd=solver_dir)
        gitproc = subprocess.Popen(
                ['git', 'rev-parse', '--short=12', 'HEAD'],
                cwd=solver_dir,
                stdout=subprocess.PIPE)
        gitout, giterr = gitproc.communicate()
        rev = gitout.decode('ascii').strip()
    else:
        rev = revision

    if not os.path.isdir(exe_cache):
        os.mkdir(exe_cache)

    opthash = base36encode(zlib.adler32(confopts.encode('utf-8')))
    solver_cache = os.path.join(exe_cache, solver)
    if not os.path.isdir(solver_cache):
        os.mkdir(solver_cache)
    dir_of_exec = os.path.join(solver_cache, rev)
    path_to_exec = os.path.join(
            dir_of_exec,
            "{0}-{1}".format(variant, opthash) )
    logfile.write("Looking for executable {0} ...\n".format(path_to_exec))

    if os.path.exists(path_to_exec):
        logfile.write("Executable exists!")
        logfile.write("{0} {1} {2} {3}\n".format(solver, rev, variant, confopts))
        logging.info("{0} {1} {2} {3}\n".format(solver, rev, variant, confopts))

        try:
            logfile.flush()
        except Exception:
            logging.exception('Flushing file failed')
            pass

    else:
        ## executable does not exist, try to build it

        logfile.write("Executable {0} not found.\n".format(path_to_exec))
        try:
            logfile.flush()
        except Exception:
            logging.exception('Flushing file failed')
            pass

        ## configure and build the solver
        logfile.write("#####################  HG BUILD  #####################\n")

        try:
            logging.info("\nCompiling {0} {1} {2} {3}...\n".format(solver, rev, variant, confopts))
            build_waf(variant, confopts, solver_dir, logfile, errfile)

            if variant == 'build':
                built_exec = os.path.join(solver_dir or '', 'build', solver)
            else:
                built_exec = os.path.join(
                        solver_dir or '',
                        'build',
                        variant,
                        solver)

            if not os.path.isdir(dir_of_exec):
                os.mkdir(dir_of_exec)

            shutil.copyfile(built_exec, path_to_exec)
            shutil.copymode(built_exec, path_to_exec)

            # Storing the used options, for simple later reference.
            with open(os.path.join(dir_of_exec,'opts'+opthash+'.txt'), 'w') \
                    as optfile:
                optfile.write(confopts+'\n')

        except Exception:
            # Failed builds will be handled below by checking, wether the
            # executable actually exists.
            logging.exception('Build failed')
            pass

    abs_to_exec = os.path.join(os.getcwd(), path_to_exec)

    ## finaly checks if the exec exist at the right place and executable
    if os.path.isfile(abs_to_exec) and os.access(abs_to_exec, os.X_OK):
        logging.info("####################################################\n")
        logging.info("       CLONE BUILD {0} revision: {1}".format(solver, rev))
        logging.info("                  SUCCESSFULLY\n")
        logging.info("####################################################\n\n")
        logfile.write("####################################################\n")
        logfile.write("       CLONE BUILD {0} revision: {1}".format(solver, rev))
        logfile.write("                  SUCCESSFULLY\n")
        logfile.write("####################################################\n\n")
    else:
        logging.info("Build FAILED\n")
        logging.info("####################################################\n\n")
        logfile.write("####################################################\n")
        logfile.write("EXECUTABLE NOT FOUND!\n")
        logfile.write("Please look at the clone_build errorlog\n")
        logfile.write("####################################################\n\n")
    try:
        logfile.flush()
    except Exception:
        logging.exception('Flushing file failed')
        pass

    return abs_to_exec
