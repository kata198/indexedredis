# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.foreign - Foreign field, links to another object
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import sys
import weakref

from . import IRField, irNull

from ..compat_str import isStringy, to_unicode


# NOTE: Current status, works to link objects, cascade save works, cascade fetch works.
#   Resolution happens on member access, unless it is already fetched or cascadeFetch=True on calling the fetching method.

# Remaining work:

# TODO: Need to think about linking not-saved objects. You can set the model, and so long as sub is saved first it will work, but if main then ref get saved, the link will not be created.


# TODO: Provide some sort of "reload child" mechanism
# TODO: Related, look into the "reload" method and add option to reload foreign links or leave them alone.

# TODO: Handle deleting fields
# TODO: Cleanup and reuse code


class ForeignLinkDataBase(object):
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

	def isFetched(self):
		return not bool(self.obj is None)


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
	def getObj(self):
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

	def isFetched(self):
		if not self.obj:
			return False

		if not self.pk or None in self.obj:
			return False
		return not bool(self.obj is None)


class IRForeignLinkFieldBase(IRField):
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
		elif value == None:
			return irNull

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

class IRForeignMultiLinkField(IRForeignLinkField):
	'''
		IRForeignMultiLinkField - A field which links to a list of foreign objects
	'''

	CAN_INDEX = False

	def _fromStorage(self, value):
		if not value:
			value = ''
		else:
			value = to_unicode(value)

		try:
			pks = [int(x) for x in value.split(',')]
		except Exception as e:
			sys.stderr.write('Got exception pulling multi link field from storage:  %s:   %s\n' %(e.__class__.__name__, str(e)))
			pass
			# TODO:

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
				else:
					raise ValueError('Unknown element in list:  <%s>  %s' %(value.__class__.__name__, repr(value)) )

			return ForeignLinkMultiData( pk=pks, foreignModel=self.foreignModel, obj=objs)
		elif values == None:
			return irNull

		# TODO: Temp exception
		raise ValueError('Unknown input: <%s>   %s' %(values.__class__.__name__, repr(values)) )
	
	def _toStorage(self, value):
		if isinstance(value, ForeignLinkMultiData):
			return ','.join([str(eachPk) for eachPk in value.pk])

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

		# TODO: Temp print
		sys.stderr.write('XXX: Unknown type to storage.... %s     %s\n' %(value.__class__.__name__, repr(value)))
		 
		return value
	
#	def _toIndex(self, value):
#		# Support passing either an integer or the model itself
#		if issubclass(value.__class__, IRForeignLinkField):
#			return value.pk
#
#		return super(IRForeignLinkField, self)._toIndex(value)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
