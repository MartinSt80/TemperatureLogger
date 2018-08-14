#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import math
import os
import time

import matplotlib
import ow

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from lib import Options, Errors, Reporting, Shrink_DB


class TemperatureReading:

	def __init__(self, temp, date_time, sec_time, sensor_id, name):
		self.temperature = temp
		self.time_as_string = date_time
		self.offset_epoch_time = sec_time
		self.sensor_ID = sensor_id
		self.sensor_name = name

def checkMount():
	if not os.path.ismount(OPTIONS.getValue('save_dir')):
		# Anyone out there? (ping DHCP server)
		DHCP_response = os.system('ping -c 1 ' + OPTIONS.getValue('DHCP_IP'))
		if DHCP_response != 0:
			raise Errors.NetworkError('network', 'Not connected to DHCP')

		# is the NAS there? (ping NAS)
		NAS_response = os.system('ping -c 1 ' + OPTIONS.getValue('mount_IP'))
		if NAS_response != 0:
			raise Errors.NetworkError('NAS', 'NAS does not respond to ping!')

		# try to mount NAS
		mount_response = os.system('sudo mount -t cifs '+ OPTIONS.getValue('mount_source') + OPTIONS.getValue('save_dir') + ' -o credentials=' + OPTIONS.getValue('mount_credentials'))
		if mount_response != 0:
			raise Errors.NetworkError('NAS', 'NAS is available, but could not be mounted')

def readTemperatures():

	# initiate owserver port set in /etc/owfs.config
	ow.init('localhost:' + OPTIONS.getValue('sensor_port'))
	ow.error_level(ow.error_level.fatal)
	ow.error_print(ow.error_print.stderr)

	# initiate temperature conversion & get sensor list
	ow._put('/simultaneous/temperature','1')
	time.sleep(1)
	active_sensors = ow.Sensor("/").sensorList()
	sensor_data = []

	for sensor in active_sensors:

		sensor_ID = str(sensor)[1:12]

		try:
			sensor_name = SENSOR_LIST.getValue(sensor_ID)
		except KeyError:
			sensor_name = 'Unknown sensor!'

		temp = float(sensor.temperature)
		date_time = time.strftime("%Y%m%d%H%M", time.localtime())
		sec_time = time.time() - float(OPTIONS.getValue('time_offset'))

		sensor_data.append(TemperatureReading(temp, date_time, sec_time, sensor_ID, sensor_name))

	return sensor_data

def checkTemperatures(reading):
	# a temperature readout of 85 indicates an internal sensor error
	if reading.temperature == 85:
		raise Errors.SensorError(reading.sensor_ID[3:], reading.sensor_name)
	# Check if temperature is within acceptable range set in the options
	if reading.temperature < int(OPTIONS.getValue('lower_limit')) or reading.temperature > int(OPTIONS.getValue('upper_limit')):
		raise Errors.TemperatureError(reading.temperature, reading.sensor_ID[3:], reading.sensor_name, 'limit')

def writeTemperatures(reading):

	save_file = OPTIONS.getValue('save_dir') + 'Data/' + reading.sensor_ID + '.dat'
	error_log = OPTIONS.getValue('save_dir') + 'error_log.dat'

	if reading.temperature == 85:		# failed sensor: temp == 85
		if os.path.exists(error_log):
			with open(error_log, 'a') as f:
				f.write("%0.0f" % reading.offset_epoch_time + '\t' + reading.time_as_string + '\t' + reading.sensor_ID + '\t' + "%0.2f" % reading.temperature + '\n')
		else:
			with open(error_log, 'w') as f:
				f.write("%0.0f" % reading.offset_epoch_time + '\t' + reading.time_as_string + '\t' + reading.sensor_ID + '\t' + "%0.2f" % reading.temperature + '\n')

	else:
		if os.path.exists(save_file):
			with open(save_file, 'a') as f:
				f.write("%0.0f" % reading.offset_epoch_time + '\t' + reading.time_as_string + '\t' + "%0.2f" % reading.temperature + '\n')
		else:
			with open(save_file, 'w') as f:
				f.write("%0.0f" % reading.offset_epoch_time + '\t' + reading.time_as_string + '\t' + "%0.2f" % reading.temperature + '\n')

def plotTemperatures(data_file, current_time):

	def formatTemperatureDifference(temp_diff):
		if (temp_diff < 2):
			text = 'less than 2'
			stab_color = 'ForestGreen'
		elif (temp_diff >= 2 and temp_diff < 4):
			text = 'less than 4'
			stab_color = 'OliveDrab'
		elif (temp_diff >= 4 and temp_diff < 6):
			text = 'less than 6'
			stab_color = 'DarkOrange'
		else:
			text = 'more than 6'
			stab_color = 'FireBrick'

		return text, stab_color

	def annotatePlot(hours, temps, avg_temp, stab_text, barcolor, name, avg_line):
		plt.annotate(name, xy=(0.15, 0.8),
				xycoords='figure fraction',
				horizontalalignment='left', verticalalignment='bottom',
				fontsize=11)
		if not hours == []:
			plt.annotate('Current temperature: {:.1f} $^\circ$C'.format(temps[-1] + avg_temp), xy=(0.87, 0.8),
				xycoords='figure fraction',
				horizontalalignment='right', verticalalignment='bottom',
				fontsize=11)
		else:
			plt.annotate('No sensor data within the last 3 h!', xy=(0.87, 0.8),
				xycoords='figure fraction',
				horizontalalignment='right', verticalalignment='bottom',
				fontsize=11)

		if (hours[0] < -1):
			plt.annotate('Temperature changed ' + stab_text + '$^\circ$C over {:.1f} h'.format(hours[-1] - hours[0]), xy=(0.87, 0.13),
				xycoords='figure fraction',
				horizontalalignment='right', verticalalignment='bottom',
				fontsize=10,color=barcolor)
			plt.annotate('Average temperature: {:.1f} $^\circ$C'.format(avg_temp), xy=(0.87, 0.2),
				xycoords='figure fraction',
				horizontalalignment='right', verticalalignment='bottom',
				fontsize=10, color='blue')

			plt.setp(avg_line, color='blue', linestyle='--', linewidth=2.0)

	with open(data_file, 'r') as f:
		line_number = sum(1 for line in f)

	if (line_number > 37):
		epoch_times = np.loadtxt(data_file, delimiter='\t', skiprows=line_number - 37, usecols=(0,))
		temperatures = np.loadtxt(data_file, delimiter='\t', skiprows=line_number - 37, usecols=(2,))

		time_before_current = (epoch_times - current_time + float(OPTIONS.getValue('time_offset'))) / 3600

		time_values = []
		temp_values = []
		for time_v, temp_v in zip(time_before_current, temperatures):
			if time_v >= -3.:
				time_values.append(time_v)
				temp_values.append(temp_v)

		sensor_id = data_file[-15:-4]
		try:
			sensor_name = SENSOR_LIST.getValue(sensor_id)
		except KeyError:
			sensor_name = 'Unknown sensor!'

		average_temperature = sum(temp_values) / float(len(temp_values))
		temp_values = [t - average_temperature for t in temp_values]
		max_temperature = max(temp_values)
		min_temperature = min(temp_values)
		temperature_difference = max_temperature - min_temperature
		text_snippet, bar_color = formatTemperatureDifference(temperature_difference)

		plt.figure(1, figsize=(8,4))
		plt.bar(time_values, temp_values, width=0.12, alpha=0.4, color=bar_color)
		zero_line = plt.plot([-3, 0], [0, 0])
		plt.setp(zero_line, color='black', linestyle=':', linewidth=1.0)

		plt.xlim((-3,0))
		y_max = math.ceil(max_temperature)
		y_min = math.floor(min_temperature)
		if (y_max - max_temperature < 0.4):
			y_max += 1
		if (min_temperature - y_min < 0.4):
			y_min -= 1
		plt.ylim(y_min, y_max)
		y_ticks = np.linspace(y_min, y_max, (y_max - y_min)*2 + 1)
		y_labels = []
		for y_tick in y_ticks:
			y_labels.append(str(round(average_temperature + y_tick, 1)))
		plt.yticks(y_ticks, y_labels)
		plt.tick_params(axis='x', labelsize=10)
		plt.tick_params(axis='y', labelsize=10)
		plt.ylabel('Temperature / $^\circ$C', fontsize=10)
		plt.xlabel('Hours from ' + time.strftime("%d %b %Y %H:%M", time.localtime()), fontsize=10)
		annotatePlot(time_values, temp_values, average_temperature, text_snippet, bar_color, sensor_name, zero_line)
		plt.savefig(OPTIONS.getValue('save_dir') + 'Plots/' + sensor_id + '.png')
		plt.savefig(OPTIONS.getValue('apache_plot_dir') + sensor_id + '.png')
		plt.close(1)

		if temperature_difference >= 6:
			raise Errors.TemperatureError(temperature_difference, sensor_id, sensor_name, 'unstable')


OPTIONS = Options.OptionReader('TemploggerOptions.txt')
SENSOR_LIST = Options.OptionReader('SensorList.txt')

sensor_readings = readTemperatures()

for reading in sensor_readings:
	try:
		checkTemperatures(reading)
	except (Errors.SensorError, Errors.TemperatureError) as e:
		Reporting.reportError(e)

try:
	checkMount()
except Errors.NetworkError as e:
	if e.entity == "BIC-NAS":
		Reporting.reportError(e)
	raise e
else:
	for reading in sensor_readings:
		writeTemperatures(reading)

	file_list = glob.glob(os.path.join(OPTIONS.getValue('save_dir'), 'Data', '*.dat'))
	# create plots from available data sets
	for file_name in file_list:
		try:
			plotTemperatures(file_name, time.time())
		except Errors.TemperatureError as e:
			Reporting.reportError(e)

	# every week make a backup and run Shrink_DB.py to form averages in the DB
	last_backup_taken = os.path.join(OPTIONS.getValue('save_dir'), 'Backup', 'last_backup.txt')
	if os.path.exists(last_backup_taken):
		with open(last_backup_taken, "r") as f:
			last_backup = float(f.read())
		if (time.time() - last_backup > 604800):
			Shrink_DB.archiveData(OPTIONS.getValue('save_dir'), file_list, OPTIONS.getValue('time_offset'))
			with open(last_backup_taken, "w") as f:
				f.write(str(time.time()))
	else:
		Shrink_DB.archiveData(OPTIONS.getValue('save_dir'), file_list, OPTIONS.getValue('time_offset'))
		with open(last_backup_taken, "w") as f:
			f.write(str(time.time()))