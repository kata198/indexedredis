# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.pickle - Some types and objects related to pickled . Use this in place of IRField ( in FIELDS array ) to activate


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :


from . import IRField, irNull
try:
	import cPickle as pickle
except ImportError:
	import pickle

from base64 import b64encode, b64decode


class IRPickleField(IRField):
	'''
		IRPickleField - A field which pickles its data before storage and loads after retrieval
	'''

	def __init__(self, name):
		self.valueType = None

	def toStorage(self, value):
		if value in ('', irNull):
			return value
		if type(value) == str:
			return value
		return b64encode(pickle.dumps(value)).decode('ascii')

	def convert(self, value):
		if not value:
			return value
		origData = value
		if hasattr(value, 'encode'):
			value = value.encode('ascii')
			return pickle.loads(b64decode(value))
		return origData

	def __new__(self, name):
		return IRField.__new__(self, name)

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
