import os
from shepherd.lib.validate_functions import *
import numpy as np
import logging

def validate(output, reference, category, position, loadtxt_args = {}):

    logging.info('Out: {}'.format(output))
    logging.info('Ref: {}'.format(reference))

    success = False

    ## forms the input variable to an array
    ## try to load the output
    if isinstance(output, str):
        if '.' in output:
            if os.path.exists(output):
                load_output = np.loadtxt(output, **loadtxt_args)
            else:
                logging.error('ERROR: Can not read the Outputfile')
                result = 'NO_out'
                return result, success
        else:
            load_output = np.array(output)
    else:
        load_output = np.array(output)

    if isinstance(reference, str):
        if '/' in reference:
            if os.path.exists(reference):
                load_reference = np.loadtxt(reference, **loadtxt_args)
            else:
                logging.error('ERROR: Can not read the ref file')
                result = 'NO_ref'
                return result, success
        else:
            load_reference = np.array(reference)
    else:
        load_reference = np.array(reference)


    load_output = np.ndarray.tolist(load_output)
    load_reference = np.ndarray.tolist(load_reference)
    if not position == None:
        new_load_output = []
        new_load_reference = []
        for i in position:
            new_load_output.append(load_output[i])
        load_output = new_load_output
        for i in position:
            new_load_reference.append(load_reference[i])
        load_reference = new_load_reference

    ##which category are given
    if category == 'identity':
        ##ckeck_identity
        result, success = check_identity(load_output, load_reference)
        return result, success

    elif category == 'difference':
        ##check difference
        result, success = check_difference(load_output, load_reference)
        return result, success

    else:

        logging.error('ERROR: Check the category of your shepherd_job')
        logging.error('Given category: {}'.format(category))
        result = 'NO_Cat'
        return result, success
