### function to get the performance of a shepherd_job
import os
from os.path import expanduser
import subprocess

def TimeInfoFrom(timefile, row=-1):
    """ (filehandle, int) -> dict

        Parse a timing.res file and return a dict of the data found in row.
        The provided timefile needs to be a handle to a proper readable
        timing.res file.
        Its header (starting with a #) will be parsed and the columns
        are used as keys in the returned dictionaries.
        The values of the dict are read from the given row, which defaults
        to the last row, if not provided.
        Note that row numbering starts with the header (row 0).
        The returned dictionary will contain an additional 'fileStatus'
        entry to indicate if the parsing is deemed fine or if something is
        awry.
        There will only be valid data in the dictionary if fileStatus is the
        string 'OK'.

        The following example shows an arbitrary file without a # as first
        character in the first line:

        >>> import io
        >>> timing = io.StringIO()
        >>> timing.write('No #  Line.\\n')
        12
        >>> timing.write('Invalid Dat.\\n')
        13
        >>> TimeInfoFrom(timing)
        {'fileStatus': '# Symbol not found!'}
        >>> timing.close()

        The following example is resembling an actual timing.res file and
        illustrates how the resulting dictionary can be used to access
        individual columns from the file:

        >>> import io
        >>> timing = io.StringIO()
        >>> timing.write('#  Revision nProcs KDUPS simloop| pFeval|pF_projTestFu.\\n')
        56
        >>> timing.write(' a6f202c6e1a9 1 5.681E+00 360.517E+00 3.335E+00   108.747E-03\\n')
        62
        >>> timeinfo = TimeInfoFrom(timing)
        {'fileStatus': 'OK', 'Revision': 'a6f202c6e1a9', 'nProcs': '1', 'KDUPS': '5.681E+00', 'simloop': '360.517E+00', 'pFeval': '3.335E+00', 'pF_projTestFu.': '108.747E-03'}
        >>> timeinfo['KDUPS']
        '5.681E+00'
        >>> timing.close()

        Here is an example, where the number of columns in the data and the
        header do not match:

        >>> import io
        >>> timing = io.StringIO()
        >>> timing.write('#  Revision nProcs KDUPS simloop| pFeval|pF_projTestFu.\\n')
        56
        >>> timing.write(' a6f202c6e1a9 1 5.681E+00 360.517E+00 3.335E+00   108.7   -33\\n')
        62
        >>> TimeInfoFrom(timing)
        {'fileStatus': 'Inconsistent Columns in File!'}
        >>> timing.close()

    """

    timeinfo = {}

    # Get content of timing file.
    timefile.seek(0) # Always start at beginning of file.
    lines = timefile.readlines()

    # Extract columns
    columns = []

    # Will only consider this file if the first line starts with '#'
    if (lines[0][0] == '#'):

        # First split by whitespace (arbitrary many)
        raw_columns = lines[0].split()

        # Now we need to check for | seperators.
        # We split at | characters and discard resulting empty strings at the
        # end.
        # Put all entries found this way in order into a single list for the
        # columns.
        for rc in raw_columns:
            limited = rc.split('|')
            if (limited[-1] == ''):
                limited.pop()
            columns += limited

        # If the first column is the standalone '#', remove it, otherwise the
        # immediately following textfield is overflowing and we strip the '#'
        # from its column name.
        if (columns[0] == '#'):
            del columns[0]
        else:
            columns[0] = columns[0].replace('#', '')

        # Get the last line and put it into a dict with the column names
        # as headers:
        datline = lines[row].split()
        if (len(datline) == len(columns)):
            timeinfo['fileStatus'] = 'OK'
            for col in range(len(columns)):
                timeinfo[columns[col]] = datline[col]
        else:
            timeinfo['fileStatus'] = 'Inconsistent Columns in File!'
    else:
        timeinfo['fileStatus'] = '# Symbol not found!'

    return(timeinfo)


def tail(f, n, offset=0):
    ''' (string, int, int) -> List of strings
        Returns the last n lines from a text file, using tail.
        Optionally offset lines can be cut off, in this case n+offset lines
        will be read from the end of the file and offset lines will be
        discarded from the end.
    '''
    proc = subprocess.Popen(['tail', '-n', '{0}'.format(n + offset), f],
                            stdout=subprocess.PIPE)
    lines = proc.stdout.readlines()
    if offset > 0:
        return lines[:-offset]
    else:
        return lines


def sanitize(fname, sname):
    ''' (string, string) -> string
        Sanitize the fname for the testcase in the loris database with
        respect to the solver that ran the test given in sname.
        Returns the sanitized string (replaced whitespace and start with
        solver name).
    '''
    import re

    # Look for sname:
    solvpat = re.compile('([^a-zA-Z0-9]|\A)'+sname+'([^a-zA-Z0-9]|\Z)')
    # Replace spaces:
    sanitized = fname.replace(' ', '_')
    # Remove sname
    sanitized = re.sub(solvpat, r'\1\2', sanitized)

    # Check for duplicated '_'.
    locations = [ind for ind, char in enumerate(sanitized) if char == '_']
    dupes = []
    for ind in range(1,len(locations)):
        if (locations[ind] == locations[ind-1]+1):
            dupes.append(locations[ind])
    # Cut out duplicated characters
    for d in dupes[::-1]:
        sanitized = sanitized[:d] + sanitized[d+1:]

    return '{0}-{1}'.format(sname, sanitized.strip('_'))


def perfname(solver):
    ''' (string) -> string
        Provide the name of the performance measure for a given solver or None
        if no performance measure for the given solver is known.
    '''
    try:
        name = {'musubi': 'MLUPs',
                'ateles': 'KDUPS',
                'seeder': 'MFEPS'}[solver]
    except KeyError:
        name = None
    return name


class perfDB:
    ''' Description of the performance database to keep track of past
        performance measurements.
    '''

    def __init__(self, repository_address, working_path = 'loris'):
        ''' Initialize the database with the path to the Mercurial repository
            to use for as storage.
            repository_address needs to be a string describing the location
            of the repository to store the performance data in. Set it to None
            if no performance data should be tracked.
            working_path is the location of the local copy of the database in
            the repository to work in. If not provided the repository will be
            cloned into a directory called 'loris' in the current working
            directory.
        '''

        self.repository_address = repository_address
        self.db_path = working_path
        self.wrote_to_db = False

        if isinstance(repository_address, str):
            # Only if repository_path is provided the database information
            # will be considered.

            if not os.path.exists(self.db_path):
                # If the db_path does not exist yet we try to clone it.
                try:
                    subprocess.run( [ 'hg', 'clone',
                                      self.repository_address,
                                      self.db_path ],
                                   check=True )
                except CalledProcessError:
                    # Cloning was not successful, ignore the database.
                    self.has_repo = False
                    return
            else:
                try:
                    # If the db_path directory all exists, assume it to be a clone
                    # and try to pulla and update it.
                    subprocess.run(['hg', 'pull', '-u'], cwd=self.db_path, check=True)
                except CalledProcessError:
                    # Pulling was not successful, ignore the database.
                    self.has_repo = False
                    return

            self.has_repo = True

        else:
            self.has_repo = False


        if self.has_repo:
            # Get the name of the current machine.
            import platform
            self.machine = platform.node()
            self.machine_db = os.path.join(self.db_path, self.machine)

            # Create a directory for the current machine if needed.
            os.makedirs(self.machine_db, exist_ok=True)


    def append_info(self, timeinfo, solver, testcase):
        ''' (perfDB, dict, string, string) -> string
            Put the timeinfo for the testcase of the provided solver into the
            database and return the difference to the last observed performance.
            timeinfo: a dict with the timing data from the timing.res file.
            solver: name of the solver
            testcase: a name for the testcase that was run

            returns the change in performance in percent or 'N/A' if not
            available.
        '''
        if not self.has_repo:
            # Only do anything if there is actually a repository to act on.
            return 'N/A'

        try:
            perf = timeinfo[perfname(solver)]
        except KeyError:
            # Could not find the performance in the provided timeinfo dict.
            return 'N/A'

        import json
        import datetime

        dbinfo = timeinfo.copy()
        if 'fileStatus' in dbinfo:
            del dbinfo['fileStatus']

        dbinfo['date'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='minutes')

        subprocess.run(['hg', 'update'], cwd=self.db_path)
        testcase_filename = sanitize(testcase, solver) + '.json'
        testcase_path = os.path.join(self.machine_db, testcase_filename)

        # Get the performance of the last run
        try:
            old_perf_list = tail(testcase_path, n=1)
            last_perf = json.loads(old_perf_list[-1])[perfname(solver)]
            perf_diff = '{0:.3f}'.format( 100 * (  float(perf)
                                                 - float(last_perf) )
                                          / float(last_perf) )
        except:
            # Something went wrong with obtaining the performance
            # difference
            perf_diff = 'N/A'

        # Write the data of the current run into the database file.
        with open(testcase_path, 'a') as testcase_file:
            json.dump(dbinfo, testcase_file)
            testcase_file.write('\n')
        # Toggle flag, that we wrote to the database
        self.wrote_to_db = True
        # Add the file to the repository (in case it is not yet in).
        subprocess.call( ['hg', 'add', testcase_filename],
                         cwd = self.machine_db,
                         stderr = subprocess.DEVNULL )

        return perf_diff


    def commit(self, message):
        ''' (perfDB, string) -> None
            Commits pending changes in the performance database to the Mercurial
            repository with the provided message as log message.
            The commit will also be pushed to the remote repository after the commit.
        '''
        if self.wrote_to_db:
            subprocess.run(['hg', 'commit', '-m', message], cwd=self.db_path)
            self.wrote_to_db = False
            subprocess.run(['hg', 'push', '-f'], cwd=self.db_path)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
