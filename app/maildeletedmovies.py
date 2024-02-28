# Name: mailadeletedmovies
# Coder: Marco Janssen (mastodon @marc0janssen@mastodon.online)
# date: 2024-02-28 19:36:00
# update: 2024-02-28 19:36:00

import logging
import sys
import configparser
import shutil
import smtplib
import os

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
from socket import gaierror
from chump import Application


class MDM():

    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO)

        config_dir = "/config/"
        app_dir = "/app/"
        log_dir = "/logging/lists/"

        self.config_file = "mailupdatedlists.ini"
        self.exampleconfigfile = "mailupdatedlists.ini.example"
        self.log_file = "mailadeletedmovies.log"
        self.movieslist = "del_radarr.txt"

        self.config_filePath = f"{config_dir}{self.config_file}"
        self.log_filePath = f"{log_dir}{self.log_file}"
        self.list_filePath = f"{config_dir}{self.movieslist}"

        try:
            with open(self.config_filePath, "r") as f:
                f.close()
            try:
                self.config = configparser.ConfigParser()
                self.config.read(self.config_filePath)

                # GENERAL
                self.enabled = True if (
                    self.config['GENERAL']['ENABLED'] == "ON") else False
                self.verbose_logging = True if (
                    self.config['GENERAL']['VERBOSE_LOGGING'] == "ON") \
                    else False

                # NODE
                self.nodename = self.config['NODE']['NODE_NAME']

                # MAIL
                self.mail_port = int(
                    self.config['MAIL']['MAIL_PORT'])
                self.mail_server = self.config['MAIL']['MAIL_SERVER']
                self.mail_login = self.config['MAIL']['MAIL_LOGIN']
                self.mail_password = self.config['MAIL']['MAIL_PASSWORD']
                self.mail_sender = self.config['MAIL']['MAIL_SENDER']

                # MOVIES
                self.receivers = list(
                    self.config['MOVIES']['RECEIVERS'].split(","))

                # PUSHOVER
                self.pushover_user_key = self.config['PUSHOVER']['USER_KEY']
                self.pushover_token_api = self.config['PUSHOVER']['TOKEN_API']
                self.pushover_sound = self.config['PUSHOVER']['SOUND']

            except KeyError as e:
                logging.error(
                    f"Seems a key(s) {e} is missing from INI file. "
                    f"Please check for mistakes. Exiting."
                )

                sys.exit()

            except ValueError as e:
                logging.error(
                    f"Seems a invalid value in INI file. "
                    f"Please check for mistakes. Exiting. "
                    f"MSG: {e}"
                )

                sys.exit()

        except IOError or FileNotFoundError:
            logging.error(
                f"Can't open file {self.config_filePath}"
                f", creating example INI file."
            )

            shutil.copyfile(f'{app_dir}{self.exampleconfigfile}',
                            f'{config_dir}{self.exampleconfigfile}')
            sys.exit()

    def writeLog(self, init, msg):
        try:
            if init:
                logfile = open(self.log_filePath, "w")
            else:
                logfile = open(self.log_filePath, "a")
            logfile.write(f"{datetime.now()} - {msg}")
            logfile.close()
        except IOError:
            logging.error(
                f"Can't write file {self.log_filePath}."
            )

    def run(self):
        # Setting for PushOver
        self.appPushover = Application(self.pushover_token_api)
        self.userPushover = self.appPushover.get_user(self.pushover_user_key)

        sender_email = self.mail_sender
        receiver_email = ", ".join(self.receivers)

        message = MIMEMultipart()
        message["From"] = sender_email
        message['To'] = receiver_email
        message['Subject'] = (
            f"Movies verwijderd - {self.nodename}"
        )

        # attachment = open(self.log_filePath, 'rb')
        # obj = MIMEBase('application', 'octet-stream')
        # obj.set_payload((attachment).read())
        # encoders.encode_base64(obj)
        # obj.add_header(
        #     'Content-Disposition',
        #     "attachment; filename= "+self.log_file
        # )
        # message.attach(obj)

        if self.enabled:
            try:
                with open(self.list_filePath, 'r') as file:
                    body = file.read()

                logging.info(
                    f"MoviesAdded - Sending movie list to "
                    f"{receiver_email}"
                    )

                self.writeLog(
                    False,
                    f"MoviesAdded - Sending movie list to "
                    f"{receiver_email}"
                )

                os.remove(self.list_filePath)

            except FileNotFoundError:
                logging.error(
                    f"Can't find file "
                    f"{self.list_filePath}."
                )
            except IOError:
                logging.error(
                    f"Can't read file "
                    f"{self.list_filePath}."
                )

            # logfile = open(self.log_filePath, "r")
            # body += ''.join(logfile.readlines())
            # logfile.close()

            plain_text = MIMEText(
                body, _subtype='plain', _charset='UTF-8')
            message.attach(plain_text)

            my_message = message.as_string()

            try:
                email_session = smtplib.SMTP(
                    self.mail_server, self.mail_port)
                email_session.starttls()
                email_session.login(
                    self.mail_login, self.mail_password)
                email_session.sendmail(
                    sender_email,
                    [receiver_email],
                    my_message
                    )
                email_session.quit()

                if self.verbose_logging:
                    logging.info(
                        f"MoviesAdded - Mail Sent to "
                        f"{receiver_email}."
                    )

                self.writeLog(
                    False,
                    f"MoviesAdded - Mail Sent to "
                    f"{receiver_email}.\n"
                )

                self.message = \
                    self.userPushover.send_message(
                        message=f"MoviesAdded - "
                        f"Movies list sent to "
                        f"{receiver_email}",
                        sound=self.pushover_sound
                        )

            except (gaierror, ConnectionRefusedError):
                logging.error(
                    "Failed to connect to the server. "
                    "Bad connection settings?")
            except smtplib.SMTPServerDisconnected:
                logging.error(
                    "Failed to connect to the server. "
                    "Wrong user/password?"
                )
            except smtplib.SMTPException as e:
                logging.error(
                    f"SMTP error occurred: {str(e)}.")


if __name__ == '__main__':

    mailadeletedmovies = MDM()
    mailadeletedmovies.run()
    mailadeletedmovies = None
