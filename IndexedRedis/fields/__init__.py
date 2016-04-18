# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields - Some types and objects related to advanced fields
#


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

__all__ = ('IRField', 'IRNullType', 'irNull', 'IRPickleField')

from ..compat_str import tostr


try:
	unicode
except NameError:
	unicode = str

class IRField(str):
	'''
		IRField - An advanced field TODO document
	'''

	def __init__(self, val='', valueType=None):
		if valueType in (str, bytes, unicode):
			valueType = None
		if valueType != None:
			if not isinstance(valueType, type):
				raise ValueError('valueType %s is not a type. Use int, str, etc' %(repr(valueType,)))
			if valueType == bool:
				self.convert = self._convertBool
		else:
			self.convert = self._noConvert
		self.valueType = valueType

	def toStorage(self, value):
		return tostr(value)

	def convert(self, value):
		if value in ('', irNull):
			return irNull
		return self.valueType(value)

	def _noConvert(self, value):
		return value

	def _convertBool(self, value):
		if value == '':
			return irNull
		xvalue = value.lower()
		if xvalue in ('true', '1'):
			return True
		elif xvalue in ('false', '0'):
			return False

		# I'm not sure what to do here... Should we raise an exception because the data is invalid? Should just return True?
		raise ValueError('Unexpected value for bool type: %s' %(value,))

	@classmethod
	def canIndex(cls):
		return True

	def __new__(cls, val='', valueType=None):
		return str.__new__(cls, val)





class IRNullType(str):
	'''
		The type to represent NULL for anything except string which has no NULL.
	'''

	def __new__(cls, val=''):
		'''
			Don't let this be assigned a value.
		'''
		return str.__new__(cls, '')

	def __eq__(self, otherVal):
		return bool(isinstance(otherVal, IRNullType))
	
	def __ne__(self, otherVal):
		return not bool(isinstance(otherVal, IRNullType))

	def __str__(self):
		return ''
	
	def __repr__(self):
		return 'IRNullType()'


# For all fields which have a type, if they have a null value this will be returned. IRNullType('') != str('') so you can
#  filter out nulls on result like:
#  myObjs = MyModel.objects.all()
#  notNullMyFieldObjs = results.filter(myField__ne=IR_NULL)
global irNull
irNull = IRNullType()

from .compressed import IRCompressedField
from .pickle import IRPickleField

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
