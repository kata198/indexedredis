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
	'''
	   IRFieldChain -
	   
	   These chain together the operations from multiple fields.

	   toStorage is applied left-to-right,
	   fromInput and fromStorage is applied right-to-left.

	   The output of one field is the input of the next.
	'''

	# TODO: We can probably index if all chained field types are indexable, but just disallow for now.
	CAN_INDEX = False

	def __init__(self, name, chainedFields, defaultValue=irNull, hashIndex=False):
		'''
			__init__ - Create an IRFieldChain object.

			  These chain together the operations from multiple fields.

			  toStorage is applied left-to-right,
			  fromInput and fromStorage is applied right-to-left.

			  The output of one field is the input of the next.


			@see IRField.__init__
		'''
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

		(canIndex, mustHashIndex) = self._checkCanIndex()

		if mustHashIndex is True:
			hashIndex = mustHashIndex

		self.CAN_INDEX = canIndex

		self.hashIndex = hashIndex



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

	def _toIndex(self, value):
		
		for chainedField in self.chainedFields:
			value = chainedField._toIndex(value)

		return value

	def _getReprProperties(self):
		chainedFieldsRepr = []
		for chainedField in self.chainedFields:
			fieldRepr = chainedField.__class__.__name__ + '( ' + ', '.join(chainedField._getReprProperties()) + ' )'
			chainedFieldsRepr.append(fieldRepr)

		return ['chainedFields=[ %s ]' %(', '.join(chainedFieldsRepr), )]

	def copy(self):
		return self.__class__(name=self.name, chainedFields=[field.copy() for field in self.chainedFields], defaultValue=self.defaultValue)


	def _checkCanIndex(self):
		'''
			_checkCanIndex - Check if we CAN index (if all fields are indexable).
				Also checks the right-most field for "hashIndex" - if it needs to hash we will hash.
				  Otherwise, we won't (unless hashIndex=True in constructor, TODO)
		'''
		# TODO: I think we can actually just check if the right-most is indexable, rather than check them all..
		#   Since if you can index its output, you can index the whole thing.
		if not self.chainedFields:
			return (False, False)

		for chainedField in self.chainedFields:
			if chainedField.CAN_INDEX is False:
				return (False, False)

		return (True, self.chainedFields[-1].hashIndex)



	def __new__(self, name, chainedFields=None, defaultValue=irNull, hashIndex=False):
		if not name:
			raise ValueError('IRChainedField defined without a name!')

		return IRField.__new__(self, name)


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
