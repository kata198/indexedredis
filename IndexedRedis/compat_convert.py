# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#  
# Some conversion functions

import copy


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

# TODO: Add a "filterFetchOnlyFields" helper method

def compat_convertPickleFields(mdlClass):
	'''
		compat_convertPickleFields - Convert pickle fields on given model from the old format to the new format.

		This is not threadsafe, should be run while things are not in motion. Will only affect the pickle-type fields.

		This function expects that all objects are either old format or new format, does not handle mixed.
	
		@param mdlClass - <IndexedRedis.IndexedRedisModel> - The Model
	'''
	from IndexedRedis.fields import IRPickleField
	from IndexedRedis.fields.compat_pickle import IRCompatPickleField

	pickleFields = [field for field in mdlClass.FIELDS if issubclass(field.__class__, IRPickleField)]

	if not pickleFields:
		return

	pickleFieldsStr = [str(field) for field in pickleFields]

	allPks = mdlClass.objects.getPrimaryKeys()


	oldFields = copy.copy(mdlClass.FIELDS)

	# Switch to old compat type for fetch
	for i in range(len(oldFields)):
		if issubclass(oldFields[i].__class__, IRPickleField):
			mdlClass.FIELDS[i] = IRCompatPickleField(str(oldFields[i]))


	partialObjs = mdlClass.objects.getMultipleOnlyFields(allPks, pickleFieldsStr)

	# Restore fields
	mdlClass.FIELDS = copy.copy(oldFields)

	for partialObj in partialObjs:
		for fieldName in pickleFieldsStr:
			partialObj._origData[fieldName] = '________UNSET#%$@#$%rfwesdv'


	# Save using new class
	mdlClass.saver.save(partialObjs)
		


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
