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

# XXX: This pickle class uses base64 encoding and decoding implicitly, so it could possibly get double-encoded.
#  I originally did that so that it could be used for indexes, but noting that python2 and python3 have different
#  results for pickling the same object (they can decode the same pickle, but when you pickle a new object such as
#  when filtering, you get a different result) I may just drop it.
from base64 import b64encode, b64decode

#def returnIt(val):
#	return val
#b64encode = b64decode = returnIt

class IRPickleField(IRField):
	'''
		IRPickleField - A field which pickles its data before storage and loads after retrieval
	'''

	# Sigh.... so we _can_ index on a pickle'd field, except even with the same protocol the pickling is different between python2 and python3
	CAN_INDEX = False

	def __init__(self, name=''):
		self.valueType = None

	def toStorage(self, value):
		if value in ('', irNull):
			return value
		if type(value) == str:
			return value
		return b64encode(pickle.dumps(value, protocol=2)).decode('ascii')

	def convert(self, value):
		if not value:
			return value
		origData = value
#		print ( "%s: %s" %(str(type(value)), str(dir(value))) )
		loadedPickle = self.__loadPickle(value)
		if loadedPickle is not None:
			return loadedPickle
#		if hasattr(value, 'encode'):
#			print ('c2')
#			value = value.encode('ascii')
#			return pickle.loads(b64decode(value))
		return origData

	if sys.version_info.major == 2:
		@staticmethod
		def __loadPickle(value):
			if hasattr(value, 'encode'):
				value = value.encode('ascii')
				return pickle.loads(b64decode(value))
			return None
	else:
		@staticmethod
		def __loadPickle(value):
			if type(value) == str:
				value = value.decode('ascii')
			if type(value) == bytes:
				return pickle.loads(b64decode(value), encoding='bytes')
			return None

	def __new__(self, name=''):
		return IRField.__new__(self, name)

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
