# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# chain - Support for chaining multiple IRField's (so for example to compress a json value)
#


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from ..compat_str import to_unicode

from . import IRField, irNull

try:
	unicode
except NameError:
	unicode = str

class IRFieldChain(IRField):

	# TODO: We can probably index if all chained field types are indexable, but just disallow for now.
	CAN_INDEX = False

	def __init__(self, name, chainedFields, defaultValue=irNull):
		if not name:
			raise ValueError('IRFieldChain has empty name.')

		self.chainedFields = []

		for field in chainedFields:
			# If we got jsut a class, construct it.
			if type(field) == type:
				field = field()
			if str(field) != '':
				raise ValueError('IRFieldChain has chained fields with a name set. The name should only be provided to the IRFieldChain object itself.')
			if not issubclass(field.__class__, IRField):
				raise ValueError("IRFieldChain's 'chainedFields' (second arg) should only contain IRField objects or subclasses thereof. Got: %s %s" %(str(type(field)), repr(field)))


			self.chainedFields.append(field)

		self.defaultValue = defaultValue



	def _toStorage(self, value):
		'''
			_toStorage - Convert the value to a string representation for storage.

			@param value - The value of the item to convert
			@return A string value suitable for storing.
		'''

		for chainedField in self.chainedFields:
			value = chainedField.toStorage(value)

		return value

	def _fromStorage(self, value):
		'''
			_fromStorage - Convert the value from storage (string) to the value type.

			@return - The converted value, or "irNull" if no value was defined (and field type is not default/string)
		'''

		for i in range(len(self.chainedFields)-1, -1, -1):
			chainedField = self.chainedFields[i]
			value = chainedField._fromStorage(value)

		return value
	
	def _fromInput(self, value):

		for i in range(len(self.chainedFields)-1, -1, -1):
			chainedField = self.chainedFields[i]
			value = chainedField._fromInput(value)

		return value

	def _getReprProperties(self):
		chainedFieldsRepr = []
		for chainedField in self.chainedFields:
			fieldRepr = chainedField.__class__.__name__ + '( ' + ', '.join(chainedField._getReprProperties()) + ' )'
			chainedFieldsRepr.append(fieldRepr)

		return ['chainedFields=[ %s ]' %(', '.join(chainedFieldsRepr), )]


	def __new__(self, name, chainedFields=None, defaultValue=irNull):
		if not name:
			raise ValueError('IRChainedField defined without a name!')

		return IRField.__new__(self, name)


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
