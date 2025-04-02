#!/usr/bin/env python
## \file auxiliary.py
## This file contains some auxilary functions for shepherd
import sys, os
import shutil
from subprocess import call
import logging, logging.handlers
import traceback
import datetime
from shepherd.lib.mail_function import prepare_mail, send_mail, txt_file_to_mail

def say_hello():
    logging.info("#####################################################")
    logging.info("#     _____ __               __                  __ #")
    logging.info("#    / ___// /_  ___  ____  / /_  ___  _________/ / #")
    logging.info("#    \__ \/ __ \/ _ \/ __ \/ __ \/ _ \/ ___/ __  /  #")
    logging.info("#   ___/ / / / /  __/ /_/ / / / /  __/ /  / /_/ /   #")
    logging.info("#  /____/_/ /_/\___/ .___/_/ /_/\___/_/   \__,_/    #")
    logging.info("#                 /_/                               #")
    logging.info("#####################################################")


def exit_shepherd(return_code):
    """ Clean termination of shepherd
    """

    if return_code==0:
        logging.info('Successfully finished Shepherd.')
        # Delete temporary files
        try:
            if os.path.isdir('__pycache__'):
                shutil.rmtree('__pycache__')
            if os.path.isfile('clone_build.log'):
                os.remove('clone_build.log')
            if os.path.isfile('clone_build.log'):
                os.remove('clone_build.log')
            if os.path.isfile('clone_build_error.log'):
                os.remove('clone_build_error.log')
            if os.path.isfile(shepherd_out):
                os.remove(shepherd_out)
        except:
            logging.warning('could not delete files')
            raise
    else:
        logging.error('Exiting Shepherd with error code %s', return_code)
    sys.exit(return_code)


def load_inputfile():
    """ Read parameters from input file or default file params.py as a
        Python module.
    """
    import importlib.util
    import sys

    if (len(sys.argv) > 1):
        ifile = sys.argv[1]
    else:
        ifile = 'params.py'

    if not os.path.isfile(ifile):
        logging.error('Input file %s is not found in current dir', ifile)
        exit_shepherd(1)

    logging.info('Reading input file: %s', ifile)
    global init_dir
    init_dir = os.getcwd()

    spec = importlib.util.spec_from_file_location('params',
                                                  os.path.abspath(ifile))
    module = importlib.util.module_from_spec(spec)
    sys.modules['params'] = module
    spec.loader.exec_module(module)
    return module


def log_uncaught_exceptions(ex_class, ex, tb):
    """ Reconfigure sys.excepthook in order to log any uncaught error to log
    file
    """

    try:
        from params import mail_address
    except:
        logging.error('ERROR: No mail_address provided. Please check your \
                params input file for Shepherd.')
    try:
        from params import clone_build_out
    except:
        clone_build_out = None
    try:
        from params import clone_build_err
    except:
        clone_build_err = None
    try:
        from params import prod_dir
    except:
        prod_dir = 'prod'
    try:
        from params import smtp_server
    except:
        smtp_server = {}

    work_dir = str(os.getcwd()) + '/'
    logging.critical(''.join(traceback.format_tb(tb)))
    logging.critical('{0}: {1}'.format(ex_class, ex))
    text = 'This mail was automatically created due to an error during \
            Shepherd run. There is the logging output provided as \
            attachment for debugging processes.'
    subject='Unexpected error during Shepherd run'
    try:
        to = mail_address
    except:
        print('No mail_address provided.')
    try:
        message = prepare_mail(to,subject, text)
    except:
        print('Could not configure mail settings.')

    try:
        txt_file_to_mail(message, init_dir, shepherd_out)
    except:
        print('ERROR: Could not attach '+shepherd_out+' to mail.')
    try:
        txt_file_to_mail(message, init_dir, clone_build_out)
    except:
        print('ERROR: Could not attach '+clone_build_out+' to mail.')
    try:
        txt_file_to_mail(message, init_dir, clone_build_err)
    except:
        print('ERROR: Could not attach '+clone_build_err+' to mail.')
    try:
        send_mail(to,message,**smtp_server)
    except:
        print('Could not send mail due to some unknown error.')
    ### moves the shepherd.log to the right place
    try:
        call(
                ['mv ' +os.path.join(init_dir, shepherd_out)+' '+os.path.join(init_dir,prod_dir)],
                shell=True)
    except:
        logging.exception('Moving failed')
        pass
    try:
        call(
                ['mv ' + os.path.join(init_dir, clone_build_out)
                       + ' ' +os.path.join(init_dir, prod_dir)],
                shell=True)
    except:
        logging.exception('Moving failed')
        pass
    try:
        call(
                ['mv ' + os.path.join(init_dir, clone_build_err)
                       + ' ' +os.path.join(init_dir, prod_dir)],
                shell=True)
    except:
        logging.exception('Moving failed')
        pass
    exit_shepherd(3)


def init_logging():
    """ Initialize logging
    If loglevel is not defined in shepherd input file, set default
    loglevel = 'INFO'
    """
    try:
        from params import loglevel, mail_address, clone_build_out, \
                clone_build_err, prod_dir
    except:
        loglevel = "INFO"
        # tries to set a filename for the a shepherd logfile if "shepherd_out"
        # is defined in the params.py

    global shepherd_out
    weekday = datetime.datetime.now().strftime("%A")
    shepherd_out = str(weekday) + '.log'

    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)

    logging.basicConfig(
            format="%(levelname)s : %(message)s",
            level=numeric_level,
            filename=shepherd_out,
            filemode="a")

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(console)


    print('Using loglevel="'+loglevel+'"')

    # reconfigure sys.excepthook in order to log any uncaught error to log file
    sys.excepthook = log_uncaught_exceptions
