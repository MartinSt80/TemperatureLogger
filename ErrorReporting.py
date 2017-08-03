#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
import email.utils
from email.mime.text import MIMEText
import Options


class NetworkError(Exception):
	"""Raised when the NAS is not mounted

	Attributes:
		entity -- 'NAS' - only the NAS storage is affected 'network' - no connection to LAN
		msg  -- explains what is going wrong
	"""
	def __init__(self, entity, msg):
		self.entity = entity
		self.msg = msg

class SensorError(Exception):
	"""Raised when a sensor is malfunctioning

	Attributes:
		ID -- Sensor ID
		name -- Sensor name/Location
	 """
	def __init__(self, ID, name):
		self.ID = ID
		self.name = name

class TemperatureError(Exception):
	"""Raised when a temperature value exceeds the limits set in the options or fluctuates too much

	Attributes:
		temp -- measured temperature
		ID -- Sensor ID
		name -- Sensor name/Location
		condition -- 'limit' -  upper or lower limit reached, 'unstable' - temperature is fluctuating too much
	 """
	def __init__(self, temp, ID, name, condition):
		self.temp = temp
		self.ID = ID
		self.name = name
		self.condition = condition


def sendMail(msg):

	MAIL_OPTIONS = Options.OptionReader('AlertMailOptions.txt')

	msg['To'] = email.utils.formataddr(('', MAIL_OPTIONS.getValue('mail_recipients')))
	msg['From'] = email.utils.formataddr((MAIL_OPTIONS.getValue('mail_from'), MAIL_OPTIONS.getValue('mail_sender')))
	recipients = MAIL_OPTIONS.getValue('mail_recipients').split(',')

	with open(MAIL_OPTIONS.getValue('mail_credentials'), 'r') as f:
		password = f.read()[:-1]
	server = smtplib.SMTP(MAIL_OPTIONS.getValue('mail_server'), int(MAIL_OPTIONS.getValue('mail_port')))
	try:
		# initiate connection
		server.ehlo()
		# Try to encrypt the session
		if server.has_extn('STARTTLS'):
			server.starttls()
			# reinitiate server connection over TLS
			server.ehlo()
		server.login(MAIL_OPTIONS.getValue('mail_user'), password)
		server.sendmail(MAIL_OPTIONS.getValue('mail_sender'), recipients, msg.as_string())
	finally:
		server.quit()


def reportError(error):

	if error.__class__.__name == 'NetworkError':
		msg = MIMEText(error.msg)
		msg['Subject'] = error.msg

	if error.__class__.__name == 'TemperatureError':
		if error.condition == 'limit':
			msg = MIMEText('Sensor ' + error.id + ' measures a temperature of {:.1f} °C'.format(error.temp) + ' in room ' + error.name + '!', 'plain', 'utf-8')
		if error.condition == 'unstable':
			msg = MIMEText('Sensor ' + error.id + ' measures a temperature fluctuation of more than {:.1f} °C'.format(error.temp) + ' in room ' + error.name + '!', 'plain', 'utf-8')
		msg['Subject'] = 'Temperature alarm: ' + error.name

	if error.__class__.__name == 'SensorError':
		msg = MIMEText('Sensor '+ error.ID + ' in room ' + error.name + ' is not responding!')
		msg['Subject'] = 'Sensor alarm: ' + error.name

	sendMail(msg)