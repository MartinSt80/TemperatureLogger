#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ow, time

# initiate owserver port set in /etc/owfs.config
ow.init('localhost:4304')
ow.error_level(ow.error_level.fatal)
ow.error_print(ow.error_print.stderr)

while True:
	# initiate temperature conversion
	ow._put('/simultaneous/temperature','1')
	# allow Sensors to get the reading ready
	time.sleep(1)
	# get list of active sensors
	# ow.Sensor(arg), arg -- allows to address only a subset of sensors
	for sensor in ow.Sensor("/").sensorList():
		print(sensor.id, sensor.temperature)
	print('---')
	time.sleep(5)
