#!/usr/bin/python
## \file recursive.py
## Contains recursive function to run shepherd jobs
import logging
from itertools import *

def runRecursiveJobs(allJobs, ijob_cur, curDir, prod_dir, count):
    """ Run over each job to generate files and execute them. Do recursive
    calls if job depends on other jobs.
    """

    if ijob_cur < len(allJobs):
        # current job
        job = allJobs[ijob_cur]
        # run current job only if it is not defined as last job
        if not job.runLast:
            # if job has dependency then set curDir path to depend job path
            # else set curDir to prod_dir
            if job.depend != None:
                #print job.depend
                # dependent job ID
                depID = max(job.dependID)
                #print depID
                #print 'count 1', count
                curDir = allJobs[depID].dirpath[count[depID]]
                #exit_shepherd(1)
            else:
                curDir = prod_dir

            logging.debug('current dir: ' + curDir)
            # run job for each parameter combination
            for iparam in product(*job.params_vals):
                #print 'params ',iparam
                logging.debug('Running job id: {!s}, label: {}'.format(
                    ijob_cur,
                    job.label))
                logging.debug('current count {!s}'.format(count))
                # execute current job
                success = job.run(
                        iparam=iparam,
                        icnt=count[ijob_cur],
                        curDir=curDir,
                        allJobs=allJobs,
                        count=count)
                # run next job
                runRecursiveJobs(allJobs, ijob_cur + 1, curDir, prod_dir, count)
                # update job count
                count[ijob_cur] = count[ijob_cur] + 1
        else:
            logging.debug(
                    'Postpone job label: "{}" due to run_last=True'.format(
                        job.label))
    else:
        logging.debug('Final job is reached')
        return
