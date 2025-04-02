### function to creat tag to push to the repository
#DISABLED#import os
#DISABLED#import subprocess
import logging

def create_tag(sol_dir):
    # put a check if the current revision is the working one
    # pushed by recheck or not
    logging.warning('Attempted to create a new tag in %s', sol_dir)
    logging.warning('Creating tags disabled for now!')
#DISABLED#    logging.info('Checking for directory %s', sol_dir)
#DISABLED#    if os.path.exists(sol_dir):
#DISABLED#        logging.info('Directory for %s exists.\
#DISABLED#                Creating working tag if last user was not regressioncheck.',
#DISABLED#                sol_dir)
#DISABLED#        last_user = subprocess.check_output(
#DISABLED#                'hg parent --template={author|user}'.split(),
#DISABLED#                cwd=sol_dir).decode('utf-8')
#DISABLED#        parent_changeset = subprocess.check_output(
#DISABLED#                'hg identify --num'.split(),
#DISABLED#                cwd=sol_dir)
#DISABLED#
#DISABLED#        if not last_user == 'regressioncheck':
#DISABLED#            logging.info(' Creating Tag:')
#DISABLED#            logging.info(' for: {!s}'.format(sol_dir))
#DISABLED#            logging.info(' last user = {!s}'.format(last_user))
#DISABLED#            logging.info(' Last user was not checker:\n\n')
#DISABLED#            logging.info(' Parent:')
#DISABLED#            logging.info(parent_changeset.decode(' utf-8\n'))
#DISABLED#            logging.info(' Creating a working tag and pushing')
#DISABLED#            cmd1 = 'hg tag -f working'
#DISABLED#            cmd2 = 'hg push -f -r tip'
#DISABLED#            logging.info(cmd1)
#DISABLED#            logging.info(cmd2)
#DISABLED#            subprocess.call(cmd1.split(), cwd=sol_dir)
#DISABLED#            subprocess.call(cmd2.split(), cwd=sol_dir)
#DISABLED#        else:
#DISABLED#            logging.warning(' Not creating tag. \
#DISABLED#                    Last user was "regressioncheck".')
#DISABLED#    else:
#DISABLED#        logging.warning(' Subdirectory {!s} is not existing.\n'.format(sol_dir))
#DISABLED#        logging.warning(' Cannot create working tag.')
