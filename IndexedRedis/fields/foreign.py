# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.foreign - Foreign field, links to another object
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import weakref

from . import IRField, irNull

from ..compat_str import isStringy


# NOTE: Current status, works to link already-saved objects, by integer id or model itself.

# Remaining work:

# TODO: Need to think about linking not-saved objects. You can set the model, and so long as sub is saved first it will work, but if main then ref get saved, the link will not be created.
# TODO: Work out cascading saves (like if linked to unsaved object, save that object as well as current object. May get hairy in some places.)
# TODO: Maybe work out a way to fetch all sub objects in one swoop with the original objects
# TODO: Provide some sort of "reload child" mechanism
# TODO: Other relations. One-to-one, one-to-many. Many to one is free.
# TODO: Possibly have child object saved when parent is saved, if changes are present?


class ForeignLinkData(object):

	__slots__ = ('pk', 'obj', '_foreignModel')

	def __init__(self, pk=None, foreignModel=None, obj=None):
		'''
			__init__ - Create a ForeignLinkData object

			@param pk <int> - The primary key of the foreign object
			@param obj <None/IndexedRedisModel> - The resolved object, or None if not yet resolved
		'''
		self.pk = pk
		self.obj = obj

		if foreignModel is not None:
			# Shouldn't share a weakref...
			if issubclass(foreignModel.__class__, weakref.ReferenceType):
				foreignModel = foreignModel()

			self._foreignModel = weakref.ref(foreignModel)
		else:
			self._foreignModel = None
	
	def __getitem__(self, name):
		if not isStringy(name):
			raise ValueError('Indexes must be string. %s is not supported' %( hasattr(name, '__name__') and name.__name__ or name.__class__.__name__, ) )

		if name == 'pk':
			return self.pk
		elif name == 'obj':
			return self.obj

		raise KeyError('No such item: "%s". Possible keys are:  [ "pk", "obj" ]' %(name, ) )

	@property
	def foreignModel(self):
		return self._foreignModel()

	def getObj(self):
		if self.obj is None:
			self.obj = self.foreignModel.objects.get(self.pk)

		return self.obj
	
	def getPk(self):
		return self.pk


class IRForeignLinkField(IRField):
	'''
		IRForeignLinkField - A field which provides a one-to-one mapping to another IndexedRedisModel object.

	'''

	CAN_INDEX = True

	def __init__(self, name='', foreignModel=None):
		'''
			__init__ - Create an IRForeignLinkField. Only takes a name

			@param name <str> - Field name

			This field type does not support indexing.
		'''
		IRField.__init__(self, name, valueType=int, defaultValue=irNull)

		if foreignModel:
			if not isinstance(foreignModel, type):
				raise ValueError('foreignModel must point to a type (class), not an instance.')
			if not hasattr(foreignModel, '_is_ir_model'):
				raise ValueError('foreignModel must extend IndexedRedisModel')

		self._foreignModel = weakref.ref(foreignModel)

	@property
	def foreignModel(self):
		return self._foreignModel()


	def _fromStorage(self, value):
		value = super(IRForeignLinkField, self)._fromStorage(value)

		if not value:
			return value

		return ForeignLinkData(value, self.foreignModel)

	def _fromInput(self, value):
		if hasattr(value, '_is_ir_model'):
			return ForeignLinkData(value._id, self.foreignModel)

		elif isinstance(value, int):
			return ForeignLinkData(int(value), self.foreignModel)

		# TODO: Temp exception
		raise ValueError('Unknown input: <%s>   %s' %(value.__class__.__name__, repr(value)) )
	
	def _toStorage(self, value):
		if isinstance(value, ForeignLinkData):
			return str(value.pk)

		elif isinstance(value, int):
			return str(value)
		elif hasattr(value, '_is_ir_model'):
			return str(value._id)

		# TODO: Temp print
		sys.stderr.write('XXX: Unknown type to storage.... %s     %s\n' %(value.__class__.__name__, repr(value)))
		 
		return value
	
	def _toIndex(self, value):
		# Support passing either an integer or the model itself
		if issubclass(value.__class__, IRForeignLinkField):
			return value.pk

		return super(IRForeignLinkField, self)._toIndex(value)

	def _getReprProperties(self):
		return [
			'foreignModel=%s' %(self.foreignModel.__name__, )
		]

	def copy(self):
		return self.__class__(name=self.name, foreignModel=self.foreignModel)

	def __new__(self, name='', foreignModel=None):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
