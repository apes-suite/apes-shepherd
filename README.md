# apes-shepherd
Executing APES tools with different parameters

This python script automates the input file generation for given set of input parameters 
and execute them with given executable in recursively for multiple jobs with
different executables.

## INPUT FILE
Input file for shepherd is also a python file with can be provided through command
line argument. If no input file is given then shepherd will look for default 
input file is params.py.
If input file is not found in the given dir then it will exit with an error message.

### Global parameters

`prod_dir`: Production directory, default production directory is 'prod'. It is 
          the parent directory under which shepherd output files are generated.

`loglevel`: logging detail on shepherd. Options: INFO, DEBUG, WARNING

### Shepherd Job parameter

`executable`: path to executable file to run. Must be defined. 
            If there is no executable then set it to None.

`template`: path to template file with parameters to change are defined with in $!..!$ or
          without any parameter to change autual input file for given executable
          look examples inside config/ or testcase/. 
          Pyratemplate library is used to generate input file from template file

`extension`: extension of the input file for executable. Example: 'lua', 'py'

`params`: list of parameters which will be altered regarding to the specified
        parameters. It is not possible to define ranges; you have to specify
        distinct values. Example:
        ['polynomial_degree','1','2','3','4','5']

        When more than one paramter is specified, one output file for every
        possible permutation is written. Tehe following example results in four
        files (1a, 1b, 2a, 2b):
        ['m','1','2'],['l','a','b']

        When you only want to have some permutations, you again have to specify
        them in a distinct manner (mind the parenthesis instead of brackets for
        distinct permutations):
        [('1','a'),('2','b')]

        These parameter can also be used to identify the directory or filename
        generated by shepherd.
        See also: create_dir

`additional_params`: dictionary with additional parameters to change in template file 
                   which are not used to create directory or filenames

`run_exec`: default is False. Set to True to run executable or submit jobs in clusters or HPC machines

`run_command`: option to run exectuable. Example: 'mpirun -np 4' to run executable in parallel
             or 'qsub' to submit job in hermit
             Example: <run_command> <executable> <input_file>

`input_option`: option to use inbetween job exectuable and input file while exectution.
            Example: <run_command> <executable> <input_option> <input_file>

`run_last`: default is False. Set to True, to run job not in recursive but in the end 
          after completion of all other jobs. min of dependent jobs is used as the parent
          directory to run this job. Check example given in testcase/taylorGreenVortex

`create_dir`: default is True to create directory for each parameter set defined in params list.
            If false it will append the parameter set to filename itself without creating 
            a directory

`create_subdir`: list of directories to be created for this job inside
               directory created for each parameter set

`prefix`: string which is used to set prefix of dirname for each parameter set defined for this job

`label`: string to identify the job if multiple jobs with dependency are defined.

`depend`: list of dependent jobs. last dependent job in the shepherd job list is used as a parent 
        directory for this job

`create_depend_path`: default is False. Set to True if you want to use file path and file name
                    of the dependent jobs in the current job template file. 
                    Example: If job with label 'job2' depend on job with label 'job1'.
                    If 'job2' wants to access 'job1' output filename and directory path
                    then set create_depend_path = True and access filename and directory
                    path of 'job1' in 'job2' template file as $!job1_file!$ and $!job1_path!$
                    respectively.

`create_depend_params`: default is False. Concept is same as above with an extension to
                      use dependent job params.
                      lets say 'job1' contains parameter like 'param1' and 'job2' wants
                      to use it then set create_depend_path = True and access that 'param1'
                      in 'job2' template as $!job1_param1!$.

`abort_failure`: default is False. Abort shepherd if certain job fails during its run.
