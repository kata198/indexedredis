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

		# TODO: reload and refetch


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
