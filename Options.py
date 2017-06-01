#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


class OptionReader:

	def __init__(self, file_name):
		self.optionfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)
		with open(self.optionfile, 'r') as f:
			content = f.readlines()
		self.options = {}
		for line in content:
			if not (line.startswith('#') or line in ['\n', '\r\n']):
				single_option = line.strip('\r\n').split('=')
				self.options[single_option[0].strip(' ')] = single_option[1].strip(' ')

	def getValue(self, key):
		return self.options[key]