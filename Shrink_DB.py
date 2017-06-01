#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from time import strftime, localtime, time
import os, time, shutil, zipfile
import numpy as np


def shrinkIt(file_list, time_offset):

	# Reads DB averages data points if time distance is smaller than roundX[0] until time reaches roundX[1]
	def reduceDatapoints(fname, time_ave, time_stop, offset):

		# Writes or appends three arrays to files row per row
		def writeToFile(fname, secs_arr, date_arr, temp_arr, arg):
			if arg == 'w':
				if secs_arr != []:
					with open(fname, 'w') as f:
						f.write("%0.0f" % secs_arr[0] + '\t' + date_arr[0] + '\t' + "%0.2f" % temp_arr[0] + '\n')
					f = open(fname, "a")
					for i in range(1, len(secs_arr)):
						f.write("%0.0f" % secs_arr[i] + '\t' + date_arr[i] + '\t' + "%0.2f" % temp_arr[i] + '\n')
					f.close()
				else:
					f = open(fname, "w")
					f.close()

			elif arg == 'a':
				if secs_arr != []:
					f = open(fname, "a")
					for i in range(len(secs_arr)):
						f.write("%0.0f" % secs_arr[i] + '\t' + date_arr[i] + '\t' + "%0.2f" % temp_arr[i] + '\n')
					f.close()

		secs = np.loadtxt(fname, dtype = 'i', delimiter='\t', usecols=(0,))
		date = np.loadtxt(fname, dtype = 'str', delimiter='\t', usecols=(1,))
		temp = np.loadtxt(fname, dtype = 'f', delimiter='\t', usecols=(2,))

		f = open(fname, "w")
		f.close()

		secs_mean = []
		temp_mean = []

		i=0

		while secs[i] < time.time() - offset - time_stop:
			j = i+1
			while secs[j] - secs[i] <= time_ave:
				secs_mean.append(secs[j-1])
				temp_mean.append(temp[j-1])
				j += 1
			if len(secs_mean) != 0:
				secs_new = sum(secs_mean)/len(secs_mean)
				date_new = strftime("%Y%m%d%H%M", localtime(secs_new+offset))
				temp_new = float(sum(temp_mean))/len(temp_mean)
				with open(fname, 'a') as f:
					f.write(str(secs_new) + '\t' + date_new + '\t' + "%0.2f" % temp_new + '\n')
				secs_mean = []
				temp_mean = []
				i = j-1
			else:
				with open(fname, 'a') as f:
					f.write(str(secs[i]) + '\t' + date[i] + '\t' + "%0.2f" % temp[i] + '\n')
				i = j
		writeToFile(fname, secs[i:len(secs)], date[i:len(date)], temp[i:len(temp)], 'a')


	round0 = [1800, 604800]			# data older than 7 days is averaged to 2 data points per hour
	round1 = [7200, 2678400]		# data older than 31 days is averaged to 1 data point per 2 hours
	round2 = [86400, 31536000]		# data older than 1 year is averaged to 1 data point per day
		
	for file_name in file_list:	
		file_old = file_name[:-3] + 'old'
		shutil.copy(file_name, file_old)
		try:
			reduceDatapoints(file_name, round0[0], round0[1], time_offset)
			reduceDatapoints(file_name, round1[0], round1[1], time_offset)
			reduceDatapoints(file_name, round2[0], round2[1], time_offset)
			os.remove(file_old)
		except:
			shutil.copy(file_old, file_name)
			os.remove(file_old)


def zipData(save_dir, datafile_list):
		zipped_file = os.path.join(save_dir, 'Backup', strftime("%Y%m%d", localtime()), '.zip')
		with zipfile.ZipFile(zipped_file, 'a', zipfile.ZIP_DEFLATED) as datazip:
			for file_name in datafile_list:
				datazip.write(file_name)

def archiveData(save_dir, file_list, time_offset):
	try:
		zipData(save_dir, file_list)
	except:
		pass
	else:
		shrinkIt(file_list, time_offset)