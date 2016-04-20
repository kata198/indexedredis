# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
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

	def __init__(self, name, chainedFields):
		if not name:
			raise ValueError('IRFieldChain has empty name.')

		self.chainedFields = []
		hasToBytes = False
		for field in chainedFields:
			if str(field) != '':
				raise ValueError('IRFieldChain has chained fields with a name set. The name should only be provided to the IRFieldChain object itself.')
			if not issubclass(field.__class__, IRField):
				raise ValueError("IRFieldChain's 'chainedFields' (second arg) should only contain IRField objects or subclasses thereof. Got: %s %s" %(str(type(field)), repr(field)))

			if hasattr(field, 'toBytes'):
				hasToBytes = True

			self.chainedFields.append(field)

		if hasToBytes is True:
			self.toBytes = self._toBytes


	def toStorage(self, value):
		'''
			toStorage - Convert the value to a string representation for storage.

			  The default implementation will work here for basic types.

			@param value - The value of the item to convert
			@return A string value suitable for storing.
		'''
		for chainedField in self.chainedFields:
			value = chainedField.toStorage(value)

		return value

	def convert(self, value):
		'''
			convert - Convert the value from storage (string) to the value type.

			@return - The converted value, or "irNull" if no value was defined (and field type is not default/string)
		'''
		if value in ('', irNull):
			return irNull

		# XXX: Maybe just set this as a property
		chainedFieldsReversed = self.chainedFields[:]
		chainedFieldsReversed.reverse()

		for chainedField in chainedFieldsReversed:
			value = chainedField.convert(value)

		return value

	def _toBytes(self, value):
		for chainedField in self.chainedFields:
			if hasattr(chainedField, 'toBytes'):
				value = chainedField.toBytes(value)
		return value
		

	def __new__(self, name, chainedFields=None):
		if not name:
			raise ValueError('IRChainedField defined without a name!')

		return IRField.__new__(self, name)


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
