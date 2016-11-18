# Copyright (c) 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#  
# Some random utility functions



# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :


def hashDictOneLevel(myDict):
	'''
		A function which can generate a hash of a one-level 
		  dict containing strings (like REDIS_CONNECTION_PARAMS)

		@param myDict <dict> - Dict with string keys and values

		@return <long> - Hash of myDict
	'''
	keys = [str(x) for x in myDict.keys()]
	keys.sort()

	lst = []
	for key in keys:
		lst.append(key + '__~~__')

	return '+_[,'.join(lst).__hash__()


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
