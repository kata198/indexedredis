# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.pickle - Some types and objects related to pickled . Use this in place of IRField ( in FIELDS array ) to activate


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField, irNull
try:
	import cPickle as pickle
except ImportError:
	import pickle

from IndexedRedis.compat_str import isStringy, isEncodedString, isEmptyString

# NOTE: This pickle class originally had implcit base64 encoding and decoding so it could be used for indexes,
#  but even with same protocol python2 and python3, and possibly even different platforms and same version
#  create different pickles for the same objects. Can be as simple as the system supports microseconds,
#  or has additional methods, or whatever, but it's not reliable so don't allow it.

class IRPickleField(IRField):
	'''
		IRPickleField - A field which pickles its data before storage and loads after retrieval.

		This uses the python2 format, so is safe to use between python2 and python3.

		Because even with the same format, python2 and python3 can output different pickle strings for the same object,
		  as well as different host configurations may lead to different output, this field type is not indexable.
	'''

	# Sigh.... so we _can_ index on a pickle'd field, except even with the same protocol the pickling is different between python2 and python3
	CAN_INDEX = False

	def __init__(self, name='', defaultValue=irNull):
		'''
			__init__ - Create an IRPickleField

			@param name <str> - Field name

			@param defaultValue - The default value of this field

			Because even with the same format, python2 and python3 can output different pickle strings for the same object,
			  as well as different host configurations may lead to different output, this field type is not indexable.
		'''
		self.valueType = None
		self.defaultValue = defaultValue

	def _toStorage(self, value):
		if isEmptyString(value):
			return ''

		return pickle.dumps(value, protocol=2)

	def _fromStorage(self, value):
		if isEmptyString(value):
			return ''

		origData = value
		# TODO: Maybe not needed anymore?
		loadedPickle = self.__loadPickle(value)
		if loadedPickle is not None:
			return loadedPickle
		return origData
	
	def _fromInput(self, value):
		return value

	@staticmethod
	def __loadPickle(value):
		if not isEncodedString(value) and isStringy(value):
			return pickle.loads(value)
		return None

	def _getReprProperties(self):
		return []

	def copy(self):
		return self.__class__(name=self.name, defaultValue=self.defaultValue)

	def __new__(self, name='', defaultValue=irNull):
		return IRField.__new__(self, name)

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
