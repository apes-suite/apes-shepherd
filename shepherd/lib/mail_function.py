### function to send Email
import os
import logging
import smtplib
import email
from email.mime.multipart import MIMEMultipart
#from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import email.encoders
# For guessing MIME type
import mimetypes

# Import the email modules we'll need
import email
import email.mime.application

from shepherd.lib.performance import perfname

import subprocess
import random
import tempfile

class SSHTunnel:
    ''' Helper class to establish a SSH tunnel.
        Based on the code provided in https://stackoverflow.com/a/36485576
        by kainjow.

        Use it like this:

            with SSHTunnel('robin.inf.tu-dresden.de', '25', '22', 'checker') as tunnel:
                print "Connected on port {0} at {1}".format(tunnel.local_port, tunnel.local_host)

        port, user and key may remain empty, the local user will be used for the login, with
        the default identity keys of ssh. If no port is provided, port 22 will be used.
    '''

    def __init__(self, host, remote_port, port='22', user=None, key=None):
        self.cmd = ['ssh', '-MfN', '-o', 'ExitOnForwardFailure=yes']
        self.host = host
        self.remote_port = remote_port
        self.port = port
        self.user = user
        self.key = key
        self.local_port = random.randint(20000, 65535)
        #self.local_host = '127.0.0.1'
        self.local_host = 'localhost'

        # Get a temporary file name
        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.close()
        self.socket = tmpfile.name

        self.cmd.append('-S')
        self.cmd.append(self.socket)

        self.cmd.append('-p')
        self.cmd.append(self.port)

        if self.key is not None:
            self.cmd.append('-i')
            self.cmd.append(self.key)

        if self.user is not None:
            self.cmd.append('-l')
            self.cmd.append(self.user)

        self.cmd.append('-L')
        self.cmd.append('{0}:{1}:{2}'.format(self.local_port, self.local_host, self.remote_port))

        self.cmd.append(self.host)

        self.open = False

    def start(self):
        #exit_status = subprocess.call(['ssh', '-MfN',
        #    '-S', self.socket,
        #    '-i', self.key,
        #    '-p', self.port,
        #    '-l', self.user,
        #    '-L', '{}:{}:{}'.format(self.local_port, self.local_host, self.remote_port),
        #    '-o', 'ExitOnForwardFailure=yes',
        #    self.host
        #])
        exit_status = subprocess.call(self.cmd)
        if exit_status != 0:
            raise Exception('SSH tunnel failed with status: {}'.format(exit_status))
        if self.send_control_command('check') != 0:
            raise Exception('SSH tunnel failed to check')
        self.open = True

    def stop(self):
        if self.open:
            if self.send_control_command('exit') != 0:
                raise Exception('SSH tunnel failed to exit')
            self.open = False

    def send_control_command(self, cmd):
        cmdline = ['ssh', '-S', self.socket, '-O', cmd]
        if isinstance(self.user, str):
            cmdline.append('-l')
            cmdline.append(self.user)
        cmdline.append(self.host)
        return subprocess.check_call(cmdline)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()

# builds the mail_body
def mail_body(data, run_label):
    body = 'This is the report of Shepherd for a '+ run_label +' run\n\n'
    body += 'started at: ' + data['date'] + '\n'
    body += 'by user   : ' + data['user'] + '\n'
    body += 'on machine: ' + data['machine'] + '\n\n'

    line = '| {0:^14s} | {1:^9s} | {2:^15s} |{3:^8s} | {4:>8s} | {5:>14s} | {6:>11s} | {7:30s} |\n'
    separator = (2+14+3+9+3+15+3+8+3+8+3+14+3+11+3+30+2)*'-' + '\n'
    solver_header = separator + line.format(
                  'changeset', 'success', 'val_method', 'result', 'time',
                  'performance', 'perfdiff(%)', 'Testcase' )
    solver_header += separator

    solver_body = {}

    for testcase in range(len(data['solver'])):
        if data['mail'][testcase]:
            solver_name = data['solver'][testcase]
            if not solver_name in solver_body:
                perfcolname = perfname(solver_name)
                if perfcolname == None:
                    perfcolname = 'No Perf'
                solver_header = separator + line.format(
                              'changeset', 'success', 'val_method', 'result',
                              'time', perfcolname, 'perfdiff(%)', 'Testcase' )
                solver_header += separator
                solver_body[solver_name] = \
                        'Solver: {}\nCompiler: {}\n{}'.format(
                                solver_name,
                                data['compiler'][testcase],
                                solver_header)

            if data['success'][testcase]:
                sucstr = 'OK'
            else:
                sucstr = 'FAILED'

            if type(data['performance'][testcase]) is float:
                perfstr = '{0:14.3f}'.format(data['performance'][testcase])
            else:
                perfstr = data['performance'][testcase]

            if type(data['performance_diff'][testcase]) is float:
                perfdiffstr = '{0:9.1f}'.format(
                        data['performance_diff'][testcase])
            elif data['performance_diff'][testcase] is None:
                perfdiffstr = 'None'
            else:
                perfdiffstr = data['performance_diff'][testcase]

            solver_body[solver_name] += line.format(
                    data['changeset'][testcase],
                    sucstr,
                    data['category'][testcase],
                    data['result'][testcase],
                    data['timing'][testcase],
                    perfstr,
                    perfdiffstr,
                    data['case_name'][testcase])

    for sb in solver_body:
        body += solver_body[sb]
        body += separator
        body += '\n'

    body += "\n\n"

    logging.info(body)

    return body

# prepare the mail with needed settings
def prepare_mail(to, subject, text):
    logging.info('prepare mail...')
    msg = MIMEMultipart()
    msg['From'] = 'regressioncheck@geb.inf.tu-dresden.de'
    if type(to) in (list, tuple):
        msg['To'] = ', '.join(to)
    else:
        msg['To'] = to
    msg['Subject'] = subject
    logging.info("Sending mail to: " + msg['To'])
    msg.attach(email.mime.text.MIMEText(text))
    return msg

# send text files with mail, prepare_mail first, then send_mail
def txt_file_to_mail(msg, path, filename):
    if filename == None:
        return None
    logging.info('Try to send file ', os.path.normpath(filename))
    fpath = os.path.join(path, filename)
    if not os.path.isfile(fpath):
        fpath = filename
    try:
        with open(fpath, 'rb') as lfile:
            f_log = lfile.read()
    except:
        f_log = b"This log file couldn't be read!"
    att_file = email.mime.application.MIMEApplication(
            f_log,
            _subtype='txt')
    att_file.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(att_file)
    return None

# Attach detailed logs for failed runs. prepare_mail first, then send_mail
def att_logs(msg, mail_dict):
    for file in range(len(mail_dict['attachment'])):
        if mail_dict['attachment'][file] \
                and mail_dict['mail'][file] \
                and not mail_dict['success'][file]:
            try:
                log_file = mail_dict['log_path'][file]
                err_file = log_file.replace('.log', '.err')
                log_name = mail_dict['case_name'][file] + '.log'
                err_name = mail_dict['case_name'][file] + '.err'
                f_log = open(log_file, 'rb')
                f_err = open(err_file, 'rb')
                att_log = email.mime.application.MIMEApplication(
                        f_log.read(),
                        _subtype="txt")
                att_err = email.mime.application.MIMEApplication(
                        f_err.read(),
                        _subtype="txt")
                f_log.close()
                f_err.close()
                att_log.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=log_name)
                att_err.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=err_name)
                msg.attach(att_log)
                msg.attach(att_err)
                logging.info('attached log files to mail')
            except:
                msg.attach('Error while attaching details')
                logging.error('Error while attaching details')
        elif not mail_dict['attachment'][file]:
                logging.info('No attachment because there is: \
                        attachment = False in your input file.')
        elif not mail_dict['mail'][file]:
                logging.info(str(mail_dict['mail'][file]))
                logging.warning('No attachment because there is: \
                        mail = False in your input file.')
        else:
                logging.info('No attachment4.')
    return None

# sends the mail, has to be prepared first with prepare_mail
def send_mail(to, msg, sender='regressioncheck@geb.inf.tu-dresden.de', host='localhost', port=25, tunnel=None):
    ''' Send a mail using sender for the from field and the smtp server defined by host, port and tunnel.

        If tunnel is provided, its settings are used and the host and port settings are ignored.
        tunnel needs to be a dict that provides the configuration options for the tunnel:

        host: name of the ssh host to connect to
        optional:
        remote_port: the port to connect to on the host send mail will set this to 25 if not provided
        port: if a different port than 22 is to be used for the ssh connection
        user: login to use for the host
        key: path to the private key file to use for the login
    '''
    logging.info('send mail...')
    try:
        if tunnel is not None:
            if 'remote_port' not in tunnel:
                tunnel['remote_port'] = '25'
            with SSHTunnel(**tunnel) as tun:
                server = smtplib.SMTP(tun.local_host, tun.local_port)
                server.sendmail(
                        sender,
                        to,
                        msg.as_string())
                server.close()
        else:
            server = smtplib.SMTP(host, port)
            server.sendmail(
                    sender,
                    to,
                    msg.as_string())
            server.close()

        logging.info('Successfully sent mail')

    except:
        logging.error('Error: unable to send mail')
