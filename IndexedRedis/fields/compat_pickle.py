# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.pickle - Some types and objects related to pickled . Use this in place of IRField ( in FIELDS array ) to activate


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import sys

from . import IRField, irNull
try:
	import cPickle as pickle
except ImportError:
	import pickle

# NOTE: This pickle class originally had implcit base64 encoding and decoding so it could be used for indexes,
#  but even with same protocol python2 and python3, and possibly even different platforms and same version
#  create different pickles for the same objects. Can be as simple as the system supports microseconds,
#  or has additional methods, or whatever, but it's not reliable so don't allow it.

try:
	unicode
except NameError:
	unicode = str

class IRCompatPickleField(IRField):
	'''
		IRCompatPickleField - A field which pickles its data before storage and loads after retrieval.

			TODO: Does not support strings/bytes but should support all other complex object types (object, custom classes, lists, etc)
	'''

	# Sigh.... so we _can_ index on a pickle'd field, except even with the same protocol the pickling is different between python2 and python3
	CAN_INDEX = False

	def __init__(self, name=''):
		self.valueType = None

	def toStorage(self, value):
		if self._isNullValue(value):
			return value
		if type(value) in (str, unicode):
			return value
		return pickle.dumps(value, protocol=2)

	def convert(self, value):
		if not value:
			return value
		origData = value
		loadedPickle = self.__loadPickle(value)
		if loadedPickle is not None:
			return loadedPickle
		return origData

	if sys.version_info.major == 2:
		@staticmethod
		def __loadPickle(value):
			if hasattr(value, 'encode'):
				return pickle.loads(value)
			return None
	else:
		@staticmethod
		def __loadPickle(value):
			if type(value) == bytes:
				return pickle.loads(value, encoding='bytes')
			return None

	def __new__(self, name=''):
		return IRField.__new__(self, name)

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
