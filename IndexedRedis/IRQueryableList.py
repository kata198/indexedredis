# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields - Some types and objects related to advanced fields
#


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :


from QueryableList import QueryableListObjs


class IRQueryableList(QueryableListObjs):


	# TODO: Decide if this should just take "mdl" as an additional argument to constructor, or infer from stored objects.

	def delete(self):
		'''
			delete - Delete all objects in this list.

			@return <int> - Number of objects deleted
		'''
		if len(self) == 0:
			return 0
		mdl = self[0].__class__
		return mdl.deleter.deleteMultiple(self)


	def save(self):
		'''
			save - Save all objects in this list
		'''
		if len(self) == 0:
			return []
		mdl = self[0].__class__
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
		mdl = self[0].__class__

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

		mdl = self[0].__class__
		pks = [item._id for item in self if item._id]

		return mdl.objects.getMultiple(pks)


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
