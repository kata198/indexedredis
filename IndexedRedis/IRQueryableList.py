# Copyright (c) 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# IRQueryableList - QueryableList with some added callbacks to IndexedRedis
#


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import pprint

from QueryableList import QueryableListObjs

__all__ = ('IRQueryableList', )


class IRQueryableList(QueryableListObjs):
	'''
		IRQueryableList - A QueryableList for IndexedRedis models.

		Only supports models of one type. Preferably, you should pass "mdl" to init, otherwise
		  it will infer from the first object.

		For performance, there is NOT type checking that all models provided are of the same type,
		this is your responsibility. 

		IndexedRedis will only ever return an IRQueryableList that follow these constraints (always have model defined,
		  and only one type of model ever contained), but if you explicitly append objects you need to make sure they
		  are of the correct type.
	'''

	def __init__(self, val=None, mdl=None):
		'''
			__init__ - Create this object

			@param val - None for empty list, IndexedRedisModel for a one-item list, or a list/tuple or subclass of initial values.
			@param mdl - The IndexedRedisModel that this list will contain. Provide this now if you can, otherwise it will be inferred from
			  the first item added or present in the list.

			@raises ValueError if "mdl" is not an IndexedRedisModel
		'''
		if val is None:
			QueryableListObjs.__init__(self)
		else:
			QueryableListObjs.__init__(self, val)


		self.mdl = mdl

		if not mdl:
			# If not explicitly defined, try to infer model if objects were provided.
			#  otherwise, inference will be attempted when an operation that requires it is performed.
			self.mdl = self.getModel()
		else:
			# This is called in getModel() if we did infer, so no need to call twice.
			self.__validate_model(mdl)


	@staticmethod
	def __validate_model(mdl):
		'''
			__validate_model - Internal function to check that model is of correct type.

			Uses a class variable that has been defined for IndexedRedisModel s for a long time, not the type itself, to prevent circular imports etc.
	
			@param mdl - type to validate
		'''
		if not hasattr(mdl, '_is_ir_model'):
			raise ValueError('Model %s is not an IndexedRedisModel' %(str(mdl.__class__.__name__),))

	def getModel(self):
		'''
			getModel - get the IndexedRedisModel associated with this list. If one was not provided in constructor,
			  it will be inferred from the first item in the list (if present)

			  @return <None/IndexedRedisModel> - None if none could be found, otherwise the IndexedRedisModel type of the items in this list.

			@raises ValueError if first item is not the expected type.
		'''
		if not self.mdl and len(self) > 0:
			mdl = self[0].__class__
			self.__validate_model(mdl)

			self.mdl = mdl

		return self.mdl


	def delete(self):
		'''
			delete - Delete all objects in this list.

			@return <int> - Number of objects deleted
		'''
		if len(self) == 0:
			return 0
		mdl = self.getModel()
		return mdl.deleter.deleteMultiple(self)


	def save(self):
		'''
			save - Save all objects in this list
		'''
		if len(self) == 0:
			return []
		mdl = self.getModel()
		return mdl.saver.save(self)


	def reload(self):
		'''
			reload - Reload all objects in this list. 
				Updates in-place. To just fetch all these objects again, use "refetch"

			@return - List (same order as current objects) of either exception (KeyError) if operation failed,
			  or a dict of fields changed -> (old, new)
		'''
		if len(self) == 0:
			return []
		mdl = self.getModel()

		ret = []
		for obj in self:
			res = None
			try:
				res = obj.reload()
			except Exception as e:
				res = e

			ret.append(res)

		return ret


	def refetch(self):
		'''
			refetch - Fetch a fresh copy of all items in this list.
				Returns a new list. To update in-place, use "reload".

			@return IRQueryableList<IndexedRedisModel> - List of fetched items
		'''

		if len(self) == 0:
			return IRQueryableList()

		mdl = self.getModel()
		pks = [item._id for item in self if item._id]

		return mdl.objects.getMultiple(pks)
	
	def pprint(self, stream=None):
		dicts = [obj.asDict(includeMeta=True, forStorage=False, strKeys=True) for obj in self]

		pprint.pprint(dicts, stream=stream)


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
