import logging
import numpy as np
import math
###function to compare two arrays if they are identical and returns an array
### with "True" or "False" for each row

def check_identity(load_output, load_reference):
  
    print('Check Identity.... ')
    #check identity for each row of the output array and the reference array
    if np.array_equal(load_output,load_reference):
        identity = True
    else:
        identity = False
    print('Identity: ',identity)
    success = True
    return identity,success

### a function to calculate the difference between the output and the reference
### and returns the difference as %

def check_difference(load_output,load_reference):

    print('Check Difference... ')
    ### if the input has the right format it builds the L2_norm for each row 
    ### of the output_array and the reference_array
    print('build L2_norm...') 
    l2_output = np.linalg.norm(load_output)
    l2_reference = np.linalg.norm(load_reference)

    ### calculate the difference between the output and reference array
    diff = math.fabs((l2_reference - l2_output) / l2_reference)
    print('L2 output:', l2_output)
    print('L2 ref_file:', l2_reference)

    success = (diff < 0.00001)
    if math.isnan(diff):
        difference = 'NaN!'
    else:
        difference = '{0:.3%}'.format(diff)

    print('Deviation: ', difference)

    return difference,success
