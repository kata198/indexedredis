# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.pickle - Some types and objects related to pickled . Use this in place of IRField ( in FIELDS array ) to activate


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import sys

from . import IRField, irNull
try:
	import cPickle as pickle
except ImportError:
	import pickle

from IndexedRedis.compat_str import isStringy, isEncodedString, tobytes

# NOTE: This pickle class originally had implcit base64 encoding and decoding so it could be used for indexes,
#  but even with same protocol python2 and python3, and possibly even different platforms and same version
#  create different pickles for the same objects. Can be as simple as the system supports microseconds,
#  or has additional methods, or whatever, but it's not reliable so don't allow it.

try:
	unicode
except NameError:
	unicode = str


PICKLE_HEADER = b'~\x06\x28\x19\x89PKL'

class IRNewPickleField(IRField):
	'''
		IRNewPickleField - A field which pickles its data before storage and loads after retrieval.

		This supports pickling ALL items, but is not compatible with the old pickle module. Use compat_convertPickleFields to convert.
	'''

	# Sigh.... so we _can_ index on a pickle'd field, except even with the same protocol the pickling is different between python2 and python3
	CAN_INDEX = False

	def __init__(self, name=''):
		self.valueType = None

	@staticmethod
	def _ensure_pickle_header(value):
		value = tobytes(value)
		if not value.startswith(PICKLE_HEADER):
			return PICKLE_HEADER + value
		return value

	@staticmethod
	def _strip_pickle_header(value):
		value = tobytes(value)
		if value.startswith(PICKLE_HEADER):
			value = value[len(PICKLE_HEADER):]
		return value
	
	@staticmethod
	def _has_pickle_header(value):
		value = tobytes(value)
		return value.startswith(PICKLE_HEADER)


	def toStorage(self, value):
		if self._isNullValue(value):
			return value
		if isStringy(value):
			if IRNewPickleField._has_pickle_header(value):
				return value

		return IRNewPickleField._ensure_pickle_header(pickle.dumps(value, protocol=2))
		raise AssertionError("oops, didn't expect a %s object!" %(value.__class__.__name__, ))

	def convert(self, value):
		if not value:
			return value
		origData = value
		loadedPickle = self.__loadPickle(value)
		if loadedPickle is not None:
			return loadedPickle
		return origData

	@staticmethod
	def __loadPickle(value):
		if not isEncodedString(value) and isStringy(value) and IRNewPickleField._has_pickle_header(value):
			return pickle.loads(IRNewPickleField._strip_pickle_header(value))
		return None

	def __new__(self, name=''):
		return IRField.__new__(self, name)

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
