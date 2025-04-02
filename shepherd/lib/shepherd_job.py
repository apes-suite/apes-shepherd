#!/usr/bin/python
## Contains spd_job class with default

import logging
from params import *
from itertools import *
from pyratemp import *
from subprocess import call
import subprocess
import sys
import os
import re
import pprint

import datetime

from shepherd.lib.performance import *

COMP_PATTERN = re.compile('(?<=Compiled with ).*$')
REV_PATTERN = re.compile('(?<=Revision of the code in this executable: ).*$')
RT_PATTERN = re.compile('(?<=Done with Musubi in).*$')


def get_timing_file(config):
    import sys
    from subprocess import Popen, PIPE
    getTime = "dofile '"+config+"'; if (timing_file) then; print(timing_file); else; print('timing.res') end"
    time = Popen(["lua", "-e", getTime], stdout=PIPE)
    timing_file = time.communicate()[0]
    if sys.version_info[0] > 2:
        timing_file = timing_file.decode('ascii').strip()
    # The lua script itself may print stuff, only use the last line (printed
    # by lua after the execution of the config file) as filename.
    return timing_file.split('\n')[-1]


def get_param(params):
    """ Get parameters from python file
    """

    array2 = []
    array1 = []
    array = []
    par = []
    for count in range(len(params)):
        if isinstance(params[count][0], (tuple)):
            par.append(params[count][0])

            len_tuple = len(params[count])
            for ii in range(len_tuple - 1):
                array2.append([params[count][ii + 1]])
            array.append(array2)
            array2=[]

        else:
            par.append(params[count][0])
            for ii in range(len(params[count]) - 1):
                 #print params[count][ii+1]
                 array1.append(params[count][ii + 1])
            array.append(array1)
            array1 = []

    return array, par


class spd_job:
    """ Class to collect all possible parameters for each job
    """

    def __init__(self, job_dict):
        """Initializes a new instance of a shepherd job class.

        Initializes a new instance of the shepherd's job class with the data
        provided in the job_dict.

        job_dict -- Dictionary containing the information used to perform the job.
        """

        # get executable of the spd_job
        try:
            self.executable = job_dict['executable']
            if self.executable != None:
                if not os.path.isfile(self.executable):
                    logging.error(self.executable + ' file not found.')
                    raise FileNotFoundError(self.executable + ' file not found.')
        except:
            logging.error('executable is not provided')
            raise

        try:
            self.solver_name = job_dict['solver_name']
        except:
            self.solver_name = self.executable

        # create directory or not
        try:
            self.createDir = job_dict['create_dir']
        except:
            self.createDir = True

        # get template file
        try:
            self.template = job_dict['template']
            # if template exist
            if not os.path.isfile(self.template):
                logging.error(self.template+' file not found.')
                raise FileNotFoundError(self.template+' file not found.')

            logging.info('Generating outfile from template file: '+self.template)
            # extension of template file
            try:
                self.extension = job_dict['extension']
            except:
                logging.error('extension is not given')
                raise ValueError('extension is not given').with_traceback(sys.exc_info()[2])

            if self.extension == 'job':
               logging.error('Not implemented yet')
               raise NotImplementedError('Not implemented yet')

            # variable parameters set
            try:
                self.params = job_dict['params']
                self.params_vals, self.params_par = get_param(self.params)
                logging.debug('params_par: '+str(self.params_par))
                logging.debug('params_vals: '+str(self.params_vals))
                nvar = 0
                for iparam in product(*self.params_vals):
                    nvar = nvar + 1
                self.params_nvariant = nvar
                logging.debug('number of variants: '+str(self.params_nvariant))
            # set params_dict
            except:
                self.params = None
        except:
            self.params = None
            self.template = None
            logging.error('template file is not given')
            raise FileNotFoundError('template file not given').with_traceback(sys.exc_info()[2])

        if self.params == None:
            self.params_vals = []
            self.params = []
            self.params_par = []
            self.params_nvariant = 0
            #self.createDir = False

        # run_exectuable
        try:
            self.run_exec = job_dict['run_exec']
        except:
            self.run_exec = True

        # run command
        try:
            self.run_command = job_dict['run_command']
        except:
            self.run_command = ''

        # identify label for this job
        try:
            self.label = job_dict['label']
        except:
            self.label = None

        # additonal params
        try:
            self.addParams = job_dict['additional_params']
        except:
            self.addParams = None

        # prefix to directory
        try:
            self.prefix = job_dict['prefix']
        except:
            self.prefix = ''

        # create subdirectories
        try:
            self.createSubDir = job_dict['create_subdir']
        except:
            self.createSubDir = None

        # run exectuable
        try:
            self.runExec = job_dict['run_exec']
        except:
            self.runExec = False

        # run command
        try:
            self.runCmd = job_dict['run_command']
        except:
            self.runCmd = ''

        # runtime environment variable
        try:
            self.runEnv = job_dict['run_env']
        except:
            self.runEnv = None

        # run job at last
        try:
            self.runLast = job_dict['run_last']
        except:
            self.runLast = False

        # run options
        try:
            self.input_option = job_dict['input_option']
        except:
            self.input_option = None

        # abort shephered when run job fails
        try:
            self.abort_failure = job_dict['abort_failure']
        except:
            self.abort_failure = False

        # whether to create dependPath
        try:
            self.createDependPath = job_dict['create_depend_path']
        except:
            self.createDependPath = False

        # whether to create depend params
        try:
            self.createDependParams = job_dict['create_depend_params']
        except:
            self.createDependParams = False

        # adjust output file permissions, if a value is given
        try:
            self.chmod = job_dict['chmod']
        except:
            self.chmod = None

        try:
            self.depend = job_dict['depend']
            if not isinstance(self.depend,(list)):
                tmp = self.depend
                self.depend = [tmp]
        except:
            self.depend = None

        ###########  Recheck 2 parameter  #################
        # enable mail
        try:
            self.mail = job_dict['mail']
        except:
            self.mail = True

        # mail attachment?
        try:
            self.attachment = job_dict['attachment']
        except:
            self.attachment = False

        # name of ref_file
        try:
            self.ref = job_dict['val_ref_path']
        except:
            self.ref = None

        # outputfile
        try:
            self.val_out = job_dict['val_output_filename']
        except:
            self.val_out = None

        # job stdout to screen
        try:
            self.job_stdout = job_dict['job_stdout_to_screen']
        except:
            self.job_stdout = False

        # run validation?
        try:
            self.validation = job_dict['validation']
        except:
            self.validation = False

        # category of validation
        try:
            self.val_category = job_dict['val_method']
        except:
            self.val_category = 'difference'

        # position to validate
        try:
            self.position = job_dict['val_position']
        except:
            self.position = None

        # loadtxt arguments for validation
        try:
            self.val_loadtxt_args = job_dict['val_loadtxt_args']
        except:
            self.val_loadtxt_args = {}

        # validate md5?
        try:
            self.md5 = job_dict['val_md5']
        except:
            self.md5 = None

        ###########################
        # empty lists
        self.params_dict = []
        self.dirname = []
        self.dirpath = []
        self.filepath = []
        self.dependID = []
        self.count = 0

    def setDependencies(self, allJobs, currentIndex):
        """ Set job dependencies.

        Some jobs depend on other jobs. To run them ordered by their
        dependencies, it is needed to set the dependencies for all jobs.
        Therefore we check each job for it's dependecies and set their job IDs
        in dependID.

        allJobs -- The list of all defined jobs
        currentIndex -- The index of this job within the allJobs list.
        """
        #print currentIndex

        # Check whether this job depends on any other job at all
        if self.depend == None:
            return

        try:
            for idep in range(len(self.depend)):
                #print self.depend[idep], currentIndex
                for ijob in range(currentIndex):
                    #print currentIndex, ijob, allJobs[ijob].label
                    if allJobs[ijob].label == None:
                        logging.error('To use depend variant, specify label \
                                for each job to identify its dependency jobs')
                        raise NameError('See log file')
                    #print self.depend[idep], allJobs[ijob].label
                    if self.depend[idep] == allJobs[ijob].label:
                        self.dependID.append(ijob)
            logging.debug('dependent job ID | labels: ')
            for idep in range(len(self.depend)):
                logging.debug( '           {!s}     | {}'.format(
                    self.dependID[idep],
                    allJobs[self.dependID[idep]].label))
        except:
              raise ValueError('Error code 1').with_traceback(sys.exc_info()[2])


    def update_paramsDictWithDependJobs(self, allJobs, count, icnt, params_dict):
        ''' Update params_dict with depend file path and filename if
        create_depend_path = True and depend params if
        create_depend_params = True
        '''

        #print 'count prev', count
        for idep in range(len(self.depend)):
            depID = self.dependID[idep]
            # append dependent job dir path, file path and executable to
            # params_dict if create_depend_path is True
            if self.createDependPath:
                logging.debug(
                        'Finding relative path for dependent job: {!s}'.format(
                            depID))
                # if it is last job then take depend path from root job of its
                # dependencies
                if self.runLast:
                    minDepID = min(self.dependID)
                    if allJobs[minDepID].depend != None:
                        depOfDepID = min(allJobs[depID].dependID)
                        #min_nVariant = count[minDepID]/allJobs[minDepID].params_nvariant
                        depOfDep_nVariant = count[depOfDepID]
                    else:
                        depOfDep_nVariant = 1
                    #print ('min_nVariant ', depOfDep_nVariant)
                    #print count[depID]/min_nVariant
                    ## collect dirPath of depID with all parameter combination
                    ## created under this depID path
                    l_limit = int(icnt*count[depID]/depOfDep_nVariant)
                    u_limit = int((icnt+1)*count[depID]/depOfDep_nVariant)
                    depPath = allJobs[depID].dirpath[l_limit:u_limit]
                    depFile = allJobs[depID].filepath[l_limit:u_limit]
                else:
                    depPath = allJobs[depID].dirpath[count[depID]]
                    depFile = allJobs[depID].filepath[count[depID]]
                #print 'depID ', depID
                #print allJobs[depID].dirpath
                logging.debug('depend path: '+ str(depPath))
                logging.debug('depend file: '+ str(depFile))
                # append params_dict with dependent dir path, file path and
                # executable
                params_dict[self.depend[idep]+'_path'] = depPath
                params_dict[self.depend[idep]+'_file'] = depFile
                params_dict[self.depend[idep]+'_executable'] \
                  = allJobs[depID].executable
                  #os.path.relpath(depPath,self.dirpath[icnt])

            # if create depend params are set then append all dependent job
            # params to params_dict
            if self.createDependParams:
                logging.debug('creating params of dependent job: {}, \
                        label: {}'.format(depID,allJobs[depID].label ))
                depParams_par = []
                depParams_val = []
                # if run last update params_dict with all parameter combination
                # in dependent jobs resulting list of params
                # else access specifiy dependent job parameter combination
                # using count[depID]
                if self.runLast:
                    depParams_par = allJobs[depID].params_par
                    depParams_val = allJobs[depID].params_vals

                    if ( allJobs[depID].addParams != None ):
                      for ikey in allJobs[depID].addParams.keys():
                          depParams_par.append(ikey)
                          depParams_val.append(allJobs[depID].addParams[ikey])
                else:
                    depDict = allJobs[depID].params_dict[count[depID]]
                    for idict in depDict:
                        depParams_par.append(idict)
                        depParams_val.append(depDict[idict])

                logging.debug('depend pars: {!s}'.format(depParams_par))
                logging.debug('depend val: {!s}'.format(depParams_val))

                # update params_dict
                for ipar in range(len(depParams_par)):
                    params_dict[allJobs[depID].label+'_'+depParams_par[ipar]] \
                            = depParams_val[ipar]

        success = True
        return success

    def generate_file(self, iparam, icnt, curDir, allJobs, count):
        """ Generate input file from parameter dictionary for each variant and
        also from its dependent job parameter. Also create necccessary
        directories.
        """

        self.count = icnt
        #print 'iparam: ', iparam
        params_dict = dict()

        # add additional params first
        if self.addParams != None:
            params_dict.update(self.addParams)

        # director name or file name
        if self.prefix != '':
            dirname_loc = self.prefix + '_'
        else:
            dirname_loc = ''

        # update params_dict with given paramters only if template file
        # is given else just use given input file to run executable
        if self.params != None:
            # Loop over all the parameters and add it to the dictionary
            for ival in range(len(self.params_par)):
                if isinstance(self.params_par[ival], (tuple)):
                    for ii in range(len(self.params_par[ival])):
                        #print self.params_par[ival][ii], str(iparam[ival][0][ii])
                        params_dict[self.params_par[ival][ii]] \
                                = str(iparam[ival][0][ii])
                    dirname_loc = dirname_loc + self.params_par[ival][0]\
                                + str(iparam[ival][0][0]) + '_'
                else:
                    params_dict[self.params_par[ival]] = str(iparam[ival])
                    dirname_loc = dirname_loc + self.params_par[ival] \
                            + str(iparam[ival]) + '_'

            # truncate last underscore character
            dirname_loc = dirname_loc.replace(',', '_')
            dirname_loc = dirname_loc[:-1]

        # name of the input file
        templ_infile = self.template
        # name of the output file
        templ_outfile = self.template.split('.')[0].split('/')[-1]\
                     + '.' + self.extension
        # create dir paths only if set to True. Default is true
        if self.createDir:
            self.dirname.append(curDir + '/' + dirname_loc + '/')
            self.dirpath.append(os.path.abspath(self.dirname[icnt]))
            self.filepath.append(self.dirname[icnt]+templ_outfile)
        else:
            self.dirname.append(curDir + '/')
            self.dirpath.append(os.path.abspath(self.dirname[icnt]))
            if dirname_loc == '':
                self.filepath.append(self.dirname[icnt]+templ_outfile)
            else:
                self.filepath.append(self.dirname[icnt] + dirname_loc \
                        + '_' + templ_outfile)
        #self.relpath = os.path.relpath(self.executable, self.dirpath)
        logging.debug('Generated directory '+ self.dirname[icnt])
        #print self.dirpath[icnt]
        #print self.relpath
        if self.createDir and not os.path.exists(self.dirname[icnt]):
            logging.info('creating dir {}'.format(self.dirname[icnt]))
            os.makedirs(self.dirname[icnt])

        # check for dependent jobs and update dictionary
        # check if it requires params from dependent jobs
        if self.depend != None:
            try:
                success = self.update_paramsDictWithDependJobs(
                        allJobs,
                        count,
                        icnt,
                        params_dict)
            except:
                logging.error('Updating params dict with depend jobs')
                raise ValueError('Updating params dict with depend jobs')

        ## add executable path to params_dict
        params_dict['executable'] = self.executable

        ## add dir path to params_dict
        params_dict['path'] = self.dirpath[icnt]

        ## add file path to params_dict
        params_dict['file'] = self.filepath[icnt]

        # store params_dict in list
        self.params_dict.append(params_dict)
        logging.debug('params_dict: ')#+str(self.params_dict[icnt]))
        logging.debug(pprint.pformat(self.params_dict[icnt]))

        logging.debug('template infile {}'.format(templ_infile))
        logging.info('Generating output file {}'.format(self.filepath[icnt]))
        ## generate output file from template
        try:
            outfile = open(self.filepath[icnt], 'w')
            mytemplate = Template(filename=templ_infile, data=params_dict)
            outfile.write(mytemplate())
            outfile.close()
            # Check if the file permission have to be adjusted
            if self.chmod != None:
                # and adjust them, when requested
                os.chmod(self.filepath[icnt], self.chmod)
        except:
            logging.error('Generating outfile using pyratemplate')
            raise IOError('Generating outfile using pyratemplate').with_traceback(sys.exc_info()[2])

        ## create sub directories
        if self.createSubDir != None:
            for idir in range(len(self.createSubDir)):
                #print self.createSubDir[idir]
                subdir_name = self.dirname[icnt] + '/' + self.createSubDir[idir]
                if not os.path.exists(subdir_name):
                    os.makedirs(subdir_name)

        return dirname_loc

    def run(self, iparam, icnt, curDir, allJobs, count, perf_store, mail_dict):
        try:
            success = self.generate_file(iparam, icnt, curDir, allJobs, count)
        except:
            logging.error('From run: Failed generate_file function')
            raise ValueError('Failed generate_file function').with_traceback(sys.exc_info()[2])

        top = os.getcwd()

        if self.runExec:
            os.chdir(self.dirpath[icnt])
            if self.run_command:
                run_cmd = self.run_command.split()
            else:
                run_cmd = []
            if self.executable:
                run_cmd += [self.executable]
            if self.input_option:
                run_cmd += [self.input_option]

            run_cmd += [self.filepath[icnt]]

            # get the current environment and add the settings from job
            # definition.
            tmp_env = os.environ
            if self.runEnv is not None:
                for k, v in self.runEnv.items():
                    tmp_env[k] = v

            logging.info('run command: {!s}'.format(run_cmd))
            if self.runEnv:
                logging.info('run environment: {!s}'.format(self.runEnv))
            ### Recheck 2 ###
            ## Checks if output should go to file or screen and runs the run_cmd
            if self.job_stdout:
                job_proc = subprocess.run( 
                    run_cmd,
                    env=tmp_env)
            else:
                job_out_file = self.label + '.log'
                job_err_file = self.label + '.err'
                with open(job_out_file, 'a') as o, open(job_err_file, 'a') as e:
                    ## runs the run_cmd with job_out_file
                    job_proc = subprocess.run( 
                        run_cmd,
                        stdout=o,
                        stderr=e,
                        env=tmp_env)
            ### Recheck 2 end ###


            # set success for the testcase depending on job's return code
            success = job_proc.returncode == 0
            if not success:
                logging.error('Running job: {!s}'.format(run_cmd))
                if self.abort_failure:
                    raise ValueError('self.abort_failure = true')

            mail_dict['success'].append(success)
            ### Recheck 2 ###
            # trys to get the compiler from the solver output
            try:
                comp = 'Unknown'
                rev = 'Unknown'
                rt = 'Unknown'
                with open(job_out_file, 'r', errors='replace') as logfile:
                    for line in logfile:
                        if comp == 'Unknown':
                            m = COMP_PATTERN.search(line)
                            if m:
                                comp = m.group(0)
                        if rev == 'Unknown':
                            m = REV_PATTERN.search(line)
                            if m:
                                rev = m.group(0)
                        if rt == 'Unknown':
                            m = RT_PATTERN.search(line)
                            if m:
                                rt = m.group(0).strip()
                        if comp != 'Unknown' and rev != 'Unknown' \
                            and rt != 'Unknown':
                            break
                logging.info('Finished in {0}'.format(rt))
                mail_dict['timing'].append(rt)
                mail_dict['compiler'].append(comp)
                mail_dict['changeset'].append(rev)
            except FileNotFoundError:
                mail_dict['compiler'].append('no log file')
                mail_dict['changeset'].append('no log file')

            cwd = os.getcwd()
            ### Saves the solvername of the casename
            solver = self.solver_name
            mail_dict['solver'].append(solver)
            ### Set the validation of this Job to TRUE or FALSE
            mail_dict['validation'].append(self.validation)
            ### saves the category of the validation
            if self.validation == False:
                mail_dict['category'].append('No validation')
            else:
                mail_dict['category'].append(self.val_category)
            mail_dict['val_loadtxt_args'].append(self.val_loadtxt_args)

            # saves if validate with md5
            mail_dict['md5'].append(self.md5)

            ### saves the casename in the mail_dict
            try:
                testcase_name = self.label + '_' + self.params[0][0] \
                        + str(iparam[0])
                mail_dict['case_name'].append(testcase_name)
            except:
                testcase_name = self.label
                mail_dict['case_name'].append(testcase_name)
            ### saves the log_path in the dict
            try:
                current_log_path = cwd + '/' + job_out_file
                mail_dict['log_path'].append(current_log_path)
            except:
                mail_dict['log_path'].append(None)
            ### saves the position what to validate
            mail_dict['position'].append(self.position)
            ### saves the ref_path in the mail dict and adds the top dir
            try:
                mail_dict['ref_path'].append(self.ref)
            except:
                mail_dict['ref_path'].append(None)

            ### saves the output for validation and adds the current dir
            current_out_path = cwd + '/'
            try:
                if isinstance(self.val_out, str):
                    output = current_out_path + self.val_out
                else:
                    output = self.val_out

                mail_dict['out_path'].append(output)
            except:
                mail_dict['out_path'].append(None)


            ### saves if the log has to go into the attachment
            mail_dict['attachment'].append(self.attachment)

            ### Checks if the job result have to go to the mail
            mail_dict['mail'].append(self.mail)

            ### Calls the performance function if it set to true to get the
            ### performance of the job and save the result in the mail_dict
            if mail_dict['grep_performance']:
                solname = solver.split('/')[-1]
                try:
                    perf_file = open(get_timing_file(self.filepath[icnt]))
                    tinfo = TimeInfoFrom(perf_file)
                    perfcol = perfname(solname)
                    if (perfcol != None):
                        perf = tinfo[perfname(solname)]
                        os.chdir(top)
                        perf_diff = perf_store.append_info(tinfo,
                                                           solname,
                                                           testcase_name)
                    else:
                        perf = 'Unsupported'
                        perf_diff = 'N/A'
                except FileNotFoundError:
                    perf = 'no timing.res'
                    perf_diff = 'N/A'
                except KeyError:
                    perf = 'N/A'
                    perf_diff = 'N/A'

                mail_dict['performance'].append(perf)
                mail_dict['performance_diff'].append(perf_diff)
            else:
                mail_dict['performance'].append('---')
                mail_dict['performance_diff'].append('---')

            ### Recheck 2 end ###

        os.chdir(top)
        return mail_dict



    def runForParams(self, curDir, ijob, allJobs, count, perf_store, mail_dict):
        """ Run job for each paramter
        """

        for iparam in product(*self.params_vals):
            logging.debug('current count '+ str(count))
            mail_dict = self.run(
                    iparam=iparam,
                    icnt=count[ijob],
                    curDir=curDir,
                    allJobs=allJobs,
                    count=count,
                    perf_store=perf_store,
                    mail_dict=mail_dict)
            count[ijob] = count[ijob] + 1
        return mail_dict
