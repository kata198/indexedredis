# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# null - The irNull singleton and IRNullType
#

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import sys

__all__ = ('IR_NULL_STR', 'IR_NULL_BYTES', 'IR_NULL_UNICODE', 'IR_NULL_STRINGS', 'IRNullType', 'irNull')


try:
	unicode
except NameError:
	unicode = str


IR_NULL_STR = 'IRNullType()'
IR_NULL_BYTES = b'IRNullType()'
IR_NULL_UNICODE = u'IRNullType()'

if sys.version_info.major >= 3:
	IR_NULL_STRINGS = (IR_NULL_STR, IR_NULL_BYTES)
else:
	# This generates a unicode warning, but we SHOULDN'T have such a condition.. I don't think
#	IR_NULL_STRINGS = (IR_NULL_STR, IR_NULL_UNICODE)
	IR_NULL_STRINGS = (IR_NULL_STR, )


# TODO: May be indexed as empty string on types that would str the value. empty string != null

# There is an odd "feature" of python 2.7 where the __eq__ method is not called when
#  u'' == irNull
#  however it is in all other forms (including: irNull == u'')
#  
#  when IRNullType extends str. But when it extends unicode, it works as expected.
#
if unicode == str:
	IrNullBaseType = str
else:
	IrNullBaseType = unicode

class IRNullType(IrNullBaseType):
	'''
		The type to represent NULL for anything except string which has no NULL.

		Values of this type only equal other values of this type (i.e. '' does not equal IRNullType())
		Even False does not equal IRNull.

		You probably shouldn't ever need to use this directly, instead use the static instance, "irNull", defined in this module.
	'''

	def __new__(self, val=''):
		'''
			Don't let this be assigned a value.
		'''
		return IrNullBaseType.__new__(self, '')

	def __eq__(self, otherVal):
		return bool(issubclass(otherVal.__class__, IRNullType))
	
	def __ne__(self, otherVal):
		return not bool(issubclass(otherVal.__class__, IRNullType))

	def __str__(self):
		return ''

	def __bool__(self):
		return False
	
	def __nonzero__(self):
		return False
	
	def __repr__(self):
		return IR_NULL_STR


# For all fields which have a type, if they have a null value this will be returned. IRNullType('') != str('') so you can
#  filter out nulls on result like:
#  myObjs = MyModel.objects.all()
#  notNullMyFieldObjs = results.filter(myField__ne=IR_NULL)
global irNull
irNull = IRNullType()

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
