# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.foreign - Foreign field, links to another object
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import sys
import weakref

from . import IRField, irNull

from .null import IR_NULL_STR

from ..compat_str import isStringy, to_unicode, isBaseStringy


__all__ = ( 
	'ForeignLinkDataBase', 'ForeignLinkData', 'ForeignLinkMultiData',
	'IRForeignLinkFieldBase', 'IRForeignLinkField', 'IRForeignMultiLinkField'
)

class ForeignLinkDataBase(object):
	'''
		ForeignLinkDataBase - Base class for data relating to foreign links
	'''
	pass

class ForeignLinkData(ForeignLinkDataBase):
	'''
		ForeignLinkData - Link data for storing information about a foreign object (id and maybe object itself).

		Can fetch object if not already fetched
	'''

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
			return self.getPk()
		elif name == 'obj':
			return self.getObj()

		raise KeyError('No such item: "%s". Possible keys are:  [ "pk", "obj" ]' %(name, ) )

	@property
	def foreignModel(self):
		'''
			foreignModel - Resolve and return the weakref to the associated foreign model
		'''
		return self._foreignModel()

	def getObj(self):
		'''
			getObj - Fetch (if not fetched) and return the obj associated with this data.
		'''
		if self.obj is None:
			if not self.pk:
				return None
			self.obj = self.foreignModel.objects.get(self.pk)

		return self.obj
	
	def getObjs(self):
		'''
			getObjs - Fetch (if not fetched) and return the obj associated with this data.

				Output is iterable.
		'''
		return [ self.getObj() ]
	
	def getPk(self):
		'''
			getPk - Resolve any absent pk's off the obj's (like if an obj has been saved), and return the pk.
		'''
		if not self.pk and self.obj:
			if self.obj._id:
				self.pk = self.obj._id

		return self.pk
	
	def getPks(self):
		return [ self.getPk() ]

	def isFetched(self):
		'''
			isFetched - Check if the associated obj has been fetched or not.
		'''
		return not bool(self.obj is None)


	def __repr__(self):
		foreignModelName = self._foreignModel and self._foreignModel().__name__ or 'None'

		return self.__class__.__name__ + '(pk=%s , foreignModel=%s , obj=%s)' %(self.pk, foreignModelName, self.obj)

	def __eq__(self, other):
		if self.__class__ != other.__class__:
			return False
		
		if other.getPk() == self.getPk():
			return True

		return False
		
	def __ne__(self, other):
		return not self.__eq__(other)

	def objHasUnsavedChanges(self):
		'''
			objHasUnsavedChanges - Check if any object has unsaved changes, cascading.
		'''
		if not self.obj:
			return False

		return self.obj.hasUnsavedChanges(cascadeObjects=True)
			


# TODO: Maybe create a base which both of these extend,
#   As having multiple in a singular field name can get confusing
class ForeignLinkMultiData(ForeignLinkData):
	'''
		ForeignLinkMultiData - Link data with multiple links.

		@see ForeignLinkData
	'''

	def __init__(self, pk=None, foreignModel=None, obj=None):
		'''
			__init__ - Create a ForeignLinkMultiData

			@see ForeignLinkData
		'''
		ForeignLinkData.__init__(self, pk, foreignModel, obj)
		
		pk = self.pk
		obj = self.obj
		if pk and not obj:
			self.obj = [None for i in range(len(pk))]

		elif obj and not pk:
			self.pk = []
			for thisObj in obj:
				if thisObj._id:
					self.pk.append(thisObj._id)
				else:
					raise ValueError('Unset id')
		elif len(obj) != len(pk):
			if len(pk) > len(obj):
				self.obj += [None for i in range( len(pk) - len(obj) ) ]
			else:
				for thisObj in obj[len(pk):]:
					if thisObj._id:
						self.pk.append(thisObj._id)
					else:
						raise ValueError('unset id')


	def getPk(self):
		'''
			getPk - @see ForeignLinkData.getPk
		'''
		if not self.pk or None in self.pk:
			for i in range( len(self.pk) ):
				if self.pk[i]:
					continue

				if self.obj[i] and self.obj[i]._id:
					self.pk[i] = self.obj[i]._id

		return self.pk

	def getPks(self):
		return self.getPk()


	def getObj(self):
		'''
			getObj - @see ForeignLinkData.getObj

				Except this always returns a list
		'''
		if self.obj:
			needPks = [ (i, self.pk[i]) for i in range(len(self.obj)) if self.obj[i] is None]

			if not needPks:
				return self.obj

			fetched = list(self.foreignModel.objects.getMultiple([needPk[1] for needPk in needPks]))
			
			i = 0
			for objIdx, pk in needPks:
				self.obj[objIdx] = fetched[i]
				i += 1

		return self.obj

	def getObjs(self):
		'''
			getObjs - @see ForeignLinkData.getObjs
		'''
		return self.getObj()

	def isFetched(self):
		'''
			isFetched - @see ForeignLinkData.isFetched
		'''
		if not self.obj:
			return False

		if not self.pk or None in self.obj:
			return False
		return not bool(self.obj is None)


	def objHasUnsavedChanges(self):
		'''
			objHasUnsavedChanges - @see ForeignLinkData.objHasUnsavedChanges

			True if ANY object has unsaved changes.
		'''
		if not self.obj:
			return False

		for thisObj in self.obj:
			if not thisObj:
				continue
			if thisObj.hasUnsavedChanges(cascadeObjects=True):
				return True

		return False


class IRForeignLinkFieldBase(IRField):
	'''
		IRForeignLinkFieldBase - Base class for Foreign Link fields
	'''
	pass

class IRForeignLinkField(IRForeignLinkFieldBase):
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
		'''
			foreignModel - Resolve and return the weakref to the associated Foreign Model
		'''
		return self._foreignModel()


	def _fromStorage(self, value):
		value = super(IRForeignLinkField, self)._fromStorage(value)

		if not value:
			return value

		return ForeignLinkData(value, self.foreignModel)

	def _fromInput(self, value):

		if hasattr(value, '_is_ir_model'):
			return ForeignLinkData(value._id, self.foreignModel, value)

		elif isinstance(value, int):

			return ForeignLinkData(int(value), self.foreignModel)

		elif isBaseStringy(value) and value.isdigit():

			return ForeignLinkData(int(value), self.foreignModel)

		elif value in (None, irNull):

			return irNull

		elif issubclass(value.__class__, ForeignLinkData):

			return value

		raise ValueError('Unknown input (expected either irNull, int (pk), or %s. Got: <%s>   %s' %(self.foreignModel.__name__, value.__class__.__name__, repr(value)) )
	
	def _toStorage(self, value):

		if isinstance(value, int):
			return str(value)

		elif isinstance(value, ForeignLinkData):
			pk = value.getPk()
			if pk:
				return str(pk)
			else:
				return IR_NULL_STR

		elif hasattr(value, '_is_ir_model'):
			if value._id:
				return str(value._id)
			else:
				# Linked to an unsaved object, and cascadeSave must be False... hope they know what they're doing! :)
				return IR_NULL_STR


		raise ValueError('Unknown value type headed for storage:   <%s>   %s' %(value.__class__.__name__, repr(value)))


	def _toIndex(self, value):
		# Support passing either an integer or the model itself
		if issubclass(value.__class__, IRForeignLinkField):
			return value.getPk()

		return super(IRForeignLinkField, self)._toIndex(value)

	def _getReprProperties(self):
		return [
			'foreignModel=%s' %(self.foreignModel.__name__, )
		]

	def copy(self):
		return self.__class__(name=self.name, foreignModel=self.foreignModel)

	def isMulti(self):
		'''
			isMulti - Returns True if this is a MultiLink object (expects lists), otherwise False (expects object)

			@return <bool>
		'''
		return False

	def __new__(self, name='', foreignModel=None):
		return IRField.__new__(self, name)


class IRForeignMultiLinkField(IRForeignLinkField):
	'''
		IRForeignMultiLinkField - A field which links to a list of foreign objects
	'''

	# So... technically we CAN index this. But I feel like most legit scenarios would need a "link contains" operation,
	#  while direct-redis filtering only supports equals and not equals.. so really they're looking at client-side filtering anyway.
	# But... allow it anyway.
	CAN_INDEX = True

	def _fromStorage(self, value):
		if not value:
			value = ''
		else:
			value = to_unicode(value)

		try:
			pks = [int(x) for x in value.split(',')]
		except Exception as e:
			raise ValueError('Got exception pulling multi link field from storage:  %s:   %s\n' %(e.__class__.__name__, str(e)))

		return ForeignLinkMultiData(pk=pks, foreignModel=self.foreignModel)

	def _fromInput(self, values):
		if issubclass(values.__class__, (tuple, list, set)):
			pks = []
			objs = []
			for value in values:
				if hasattr(value, '_is_ir_model'):

					pks.append(value._id)
					objs.append(value)

				elif isinstance(value, int):

					pks.append(value)
					objs.append(None)

				elif isBaseStringy(value) and value.isdigit():

					pks.append( int(value) )
					objs.append( None )

				elif value in (irNull, None):
					continue
				else:
					raise ValueError('Unknown element in list:  <%s>  %s' %(value.__class__.__name__, repr(value)) )

			return ForeignLinkMultiData( pk=pks, foreignModel=self.foreignModel, obj=objs)

		elif values in (None, irNull):
			return irNull
		elif issubclass(values.__class__, ForeignLinkMultiData):
			return values

		raise ValueError('Unknown input: <%s>   %s' %(values.__class__.__name__, repr(values)) )
	
	def _toStorage(self, value):
		if isinstance(value, ForeignLinkMultiData):
			return ','.join([str(eachPk) for eachPk in value.getPk()])

		elif issubclass(value.__class__, (list, tuple, set)):
			ret = []
			for val in value:
				if hasattr(val, '_is_ir_model'):
					ret.append(str(val._id))
				elif isinstance(val, int):
					ret.append(str(val))
				elif isStringy(val):
					ret.append(str(int(val)))
				else:
					raise ValueError('Unknown element in list:  <%s>  %s' %(value.__class__.__name__, repr(value)) )
			return ','.join(ret)
		elif isBaseStringy(value):
			# For index
			return value


		raise ValueError('Unknown value type headed for storage:   <%s>   %s' %(value.__class__.__name__, repr(value)))
	

	def isMulti(self):
		'''
			isMulti - Returns True if this is a MultiLink object (expects lists), otherwise False (expects object)

			@return <bool>
		'''
		return True

	def _toIndex(self, value):
		# Support passing either an integer or the model itself
		if issubclass(value.__class__, IRForeignMultiLinkField):
			return ','.join(value.getPk())

		return super(IRForeignLinkField, self)._toIndex(value)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
