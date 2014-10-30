#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import traceback
import logging


def except_info():
	"""
	:return:
	"""
	return traceback.format_exc()

console_logger = logging.getLogger("console")
console_logger.setLevel(logging.DEBUG)
console_logger.addHandler(logging.StreamHandler())