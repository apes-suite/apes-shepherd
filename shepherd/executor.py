import sys
import os
import shutil
import logging
from itertools import *

# import shepherd input file
from params import *
from shepherd.lib.auxiliary import shepherd_out
# import shepherd job definition from shepherd lib
# import this file after load_inputfile since this module
# depends on params_tmp
from shepherd.lib.shepherd_job import spd_job
from shepherd.lib.mail_function import *
from shepherd.lib.validation import *
from shepherd.lib.create_tag import *
from shepherd.lib.md5 import *
from shepherd.lib.performance import perfDB

def process_input():
    # turn performance on/off
    if not 'grep_performance' in locals():
        grep_performance = True
    
    if not 'run_label' in locals():
        run_label = ''
    
    if not 'loris_clone_url' in locals():
        loris_clone_url = None
    
    if not 'create_tag_on' in locals():
        create_tag_on = False
    
    ### changed for RECHECK 2 ######
    ### mail_dict is not only for mail data. It includes all necessary data for
    ### the new shepherd with the feature of recheck
    mail_dict = {
            'mail':             [],
            'attachment':       [],
            'log_path':         [],
            'ref_path':         [],
            'out_path':         [],
            'case_name':        [],
            'validation':       [],
            'category':         [],
            'val_loadtxt_args': [],
            'solver':           [],
            'compiler':         [],
            'machine':          [],
            'timing':           [],
            'user':             [],
            'changeset':        [],
            'performance':      [],
            'performance_diff': [],
            'position':         [],
            'date':             [],
            'result':           [],
            'md5':              [],
            'success':          [],
            'performance_flag': False,
            'loris_clone_url':  None,
            'grep_performance': grep_performance }
    
    ## Add some necessary data to the mail_dict
    if grep_performance:
        # If we are to record the performance store where the repository is
        # to be found.
        mail_dict['loris_clone_url'] = loris_clone_url
    else:
        # There is no performance to record, no need to store a repository address.
        mail_dict['loris_clone_url'] = None
    
    # saves machinename to seperate the performance database
    mail_dict['machine'] = subprocess.check_output(['uname', '-n']).decode('utf-8')
    # saves the name of the user to check later if shepherd has to create a tag
    mail_dict['user'] = subprocess.check_output('whoami').decode('utf-8')
    # saves the date value from the params.py
    try:
        mail_dict['date'] = date
    except:
        mail_dict['date'] = 'UNKNOWN'
    
    ##########################
    
    # Get the production directory
    try:
        prod_dir
    except NameError:
        prod_dir = 'prod'
    
    try:
        #call(['mkdir','-p',prod_dir])
        if not os.path.exists(prod_dir):
            os.makedirs(prod_dir)
    except:
        logging.error( 'could not create production directory: '+ prod_dir)
        if os.path.isdir(prod_dir):
            logging.warning('but it already exists, so no problem.')
        else:
            exit_shepherd(2)
    
    # production directory absolute path
    prod_dir=os.getcwd()+'/'+prod_dir
    # set current dir to production directory path
    curDir = prod_dir
    
    # list of all jobs defined in input file as shepherd_job class format
    allJobs = []
    
    # Initialize the performance database
    performance_archive = perfDB(repository_address = mail_dict['loris_clone_url'])
    
    # loop over all jobs and load parameters defined for that job
    
    for ijob in range(len(shepherd_jobs)):
        #print job[ijob]['executable']
        logging.info('Reading job: '+str(ijob+1))
        # load parameter defined for this job and
        job = spd_job(shepherd_jobs[ijob])
        # for non defined parameter set default value
        job.setDependencies(allJobs, currentIndex =ijob)
        # add the new job to the list of all jobs
        allJobs.append(job)
    
    ## run over each jobs to generate files and execute them
    ## do recursive call if job depend on another job
    def runRecursiveJobs(allJobs, ijob_cur, curDir, count, perf_store, mail_dict):
        if ijob_cur < len(allJobs):
            job = allJobs[ijob_cur]
            if not job.runLast:
                if  job.depend != None and not job.runLast:
                    #print job.depend
                    depID = max(job.dependID)
                    #print depID
                    #print 'count 1', count
                    curDir = allJobs[depID].dirpath[count[depID]]
                    #exit_shepherd(1)
                else:
                    curDir = prod_dir
                #print curDir
                for iparam in product(*job.params_vals):
                    #print 'params ',iparam
                    logging.debug('Running job id: '+ str(ijob_cur) +', label: '+ job.label)
                    logging.debug('current count '+ str(count))
                    mail_dict = job.run(
                            iparam    = iparam,
                            icnt      = count[ijob_cur],
                            curDir    = curDir,
                            allJobs   = allJobs,
                            perf_store = perf_store,
                            count     = count,
                            mail_dict = mail_dict)
                    runRecursiveJobs(allJobs, ijob_cur+1, curDir, count, perf_store, mail_dict)
                    count[ijob_cur] = count[ijob_cur] + 1
            else:
                logging.debug('Postpone job with run_last=True')
        else:
            logging.debug('Final job is reached')
            return mail_dict
        return mail_dict
    nJobs = len(allJobs)
    count = [0]*nJobs
    logging.info( 'Initial count: '+ str(count))
    
    ## run all recursive jobs with dependency
    logging.info('Running recursive jobs...')
    mail_dict = runRecursiveJobs(
            allJobs,
            ijob_cur = 0,
            curDir = curDir,
            count = count,
            perf_store = performance_archive,
            mail_dict = mail_dict)
    logging.info( 'count after recursive calls: '+ str(count))
    
    ## run non dependent and run_last jobs
    ijob = 0
    for job in allJobs:
        if job.runLast:
            logging.debug('Running final job: '+job.label)
            if job.depend != None:
                ##get parent directory of depID directory
                ##create output file one level outside its dependent
                ##directory
                depID = min(job.dependID)
                logging.debug( 'min depID: ' + str(depID))
                if allJobs[depID].depend != None:
                    depOfDepID = min(allJobs[depID].dependID)
                    #print job.dependID
                    logging.debug( 'min dep of depID: ' + str(depOfDepID))
                    logging.debug( 'dep of dep label: ' + allJobs[depOfDepID].label)
                    logging.debug( 'dep of dep count: ' + str(count[depOfDepID]))
                    #if allJobs[depID].depend != None:
                    #  depID = min(allJobs[depID].dependID)
                    #  logging.debug( 'min depID of parent dir: '+str(depID))
                    #nVariant = int(count[depID]/allJobs[depID].params_nvariant)
                    nVariant = count[depOfDepID]
                    logging.info('Nr. dep of dep variants: ' + str(nVariant))
                    for idep in range(nVariant):
                        #curDir = os.path.dirname(allJobs[depID].dirpath[\
                        #            idep*allJobs[depID].params_nvariant])
                        curDir = allJobs[depOfDepID].dirpath[idep]
                        logging.debug('current dir: '+ curDir)
                        #exit_shepherd(1)
                        mail_dict = job.runForParams(
                                curDir = curDir,
                                ijob = ijob,
                                allJobs = allJobs,
                                count = count,
                                perf_store = performance_archive,
                                mail_dict = mail_dict)
                else:
                    # if dependent job has no dependency
                    curDir = prod_dir
                    logging.debug('current dir: '+ curDir)
                    mail_dict = job.runForParams(
                            curDir = curDir,
                            ijob = ijob,
                            allJobs = allJobs,
                            count = count,
                            perf_store = performance_archive,
                            mail_dict = mail_dict)
            else:
                # HK: The only difference here is, that we ignore the success return?
                # HK: Does not really make sense, is this a bug?
                curDir = prod_dir
                logging.debug('current dir: '+ curDir)
                mail_dict = job.runForParams(
                        curDir = curDir,
                        ijob = ijob,
                        allJobs = allJobs,
                        count = count,
                        perf_store = performance_archive,
                        mail_dict = mail_dict)
        ijob = ijob + 1
    
    logging.info('Final count : ' + str(count))
    
    ###### ADDED FOR RECHECK 2
    ### moves the shepherd.log to the right place
    try:
        subprocess.call(['mv ' + shepherd_out + ' ' + prod_dir + '/'], shell=True)
    except:
        logging.exception('Moving failed')
        pass
    
    try:
        subprocess.call(
                ['mv ' + clone_build_out + ' ' + clone_build_err + ' ' + prod_dir \
                        + '/'],
                shell=True)
    except:
        logging.exception('Moving failed')
        pass
    
    ### VALIDATION
    ## loops over all testcases and validates only if the validation is set to True
    ## for this testcase
    successful_run = True
    solver_ok = {}
    
    for testcase in range(len(mail_dict['validation'])):
        # if validation set to True at a testcase it runs the validate function
        if mail_dict['validation'][testcase]:
            if not mail_dict['solver'][testcase] in solver_ok:
                # If this solver appears for the first time, make sure it gets a
                # solver_ok entry:
                solver_ok[mail_dict['solver'][testcase]] = True
            success = False
            print('\nValidate: ', mail_dict['case_name'][testcase])
            print('Category: ', mail_dict['category'][testcase])
            # takes the outputfile and ref_file of the current testcase out of the dict
            # if md5 is true for the testcase it saves the md5_sum
    
            print('Out: ' + str(mail_dict['out_path'][testcase]))
            print('Ref: ' + str(mail_dict['ref_path'][testcase]))
    
            if mail_dict['md5'][testcase] \
                    and mail_dict['category'][testcase] == 'identity':
                testcase_output = filechecksum_for(mail_dict['out_path'][testcase])
                # checks if testcase reference is integer or a file/dir
                if isinstance(mail_dict['ref_path'][testcase],int):
                    testcase_ref = mail_dict['ref_path'][testcase]
                else:
                    testcase_ref = filechecksum_for(mail_dict['ref_path'][testcase])
            else:
                testcase_output = mail_dict['out_path'][testcase]
                testcase_ref = mail_dict['ref_path'][testcase]
            # takes the category of the curren testcase out of the dict
            testcase_category = mail_dict['category'][testcase]
            # takes the position of the testcase
            testcase_position = mail_dict['position'][testcase]
            # runs the validation function
            if testcase_output != None and testcase_ref != None:
                result,success = validate(
                        testcase_output,
                        testcase_ref,
                        testcase_category,
                        testcase_position,
                        mail_dict['val_loadtxt_args'][testcase])
            else:
                success = False
                if testcase_ref == None:
                    print('Can not find reference file')
                    result = 'NO_ref'
                else:
                    print('Can not find output file')
                    result = 'NO_out'
            # convert the result to a string
            result = str(result)
            # saves the result of the validation in the mail_dict
            mail_dict['result'].append(result)
            mail_dict['success'][testcase] = success
            logging.info('Success = ' + str(success))
            if not success:
                successful_run = False
                solver_ok[mail_dict['solver'][testcase]] = False
        else:
            mail_dict['result'].append('---')
    
    ### sends the mail if one job has set mail = True
    if 'mail_address' in globals() \
            and True in mail_dict['mail'] \
            and mail_address != None:
        mail_body = mail_body(mail_dict, run_label)
        if successful_run:
            okmsg = 'Successful'
        else:
            okmsg = 'FAILED'
    
        subject = okmsg + ' Shepherd run ' + run_label
        message = prepare_mail(mail_address, subject, mail_body)
        att_logs(message,mail_dict)
        send_mail(mail_address,message,**smtp_server)
    
    ### create working tag if every job is successful
      # create tag for each solver
    if create_tag_on == True:
        logging.warning('Creating tags is disabled for now due to changing to git repositories.')
    #    for solver in solver_ok:
    #        dir = solver
    #        logging.info(
    #                'Solver %s is ok. Trying to create working tag now.',
    #                solver )
    #
    #        if solver_ok[solver]:
    #            create_tag(solver)
    #        else:
    #            logging.warning(
    #                    'Could not create working tag because solver %s is not ok.',
    #                    solver)
    
    # Commit and push any recorded performance updates.
    performance_archive.commit('Shepherd update for {0}'.format(run_label))
