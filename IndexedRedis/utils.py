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


class KeyList(list):
	'''
		KeyList - A list which is indexable by both values and integer indexes.

		Each modifying operation needs to recalc indexes
	'''
	
	def __init__(self, *args, **kwargs):
		list.__init__(self, *args, **kwargs)

		self.idxDict = {}

		self.__recalcIndexes()

	def __recalcIndexes(self):
		idxDict = {}
		for i in range(len(self)):
			val = self[i]

			idxDict[val] = i

		self.idxDict = idxDict

	def __getitem__(self, item):
		isInt = False
		try:
			int(item)
			isInt = True
		except:
			pass

		if isInt is True:
			return list.__getitem__(self, item)

		if item not in self.idxDict:
			raise KeyError('No such key in list: %s' %(repr(item), ))
		
		return list.__getitem__(self, self.idxDict[item])

	
	def append(self, *args, **kwargs):
		ret = list.append(self, *args, **kwargs)
		self.__recalcIndexes()
		return ret
	
	def extend(self, *args, **kwargs):
		origID = id(self)

		ret = list.extend(self, *args, **kwargs)
		self.__recalcIndexes()
		return ret
	
	def insert(self, *args, **kwargs):
		ret = list.insert(self, *args, **kwargs)
		self.__recalcIndexes()
		return ret


	def clear(self, *args, **kwargs):
		ret = list.clear(*args, **kwargs)
		self.__recalcIndexes()
		return ret
	
	def __setitem__(self, *args, **kwargs):
		ret = list.__setitem__(self, *args, **kwargs)
		self.__recalcIndexes()
		return ret
	
	def __delitem__(self, *args, **kwargs):
		ret = list.__delitem__(self, *args, **kwargs)
		self.__recalcIndexes()
		return ret
	
	def __add__(self, *args, **kwargs):
		lst = list.__add__(self, *args, **kwargs)
		return KeyList(lst)
	
	def __iadd__(self, *args, **kwargs):
		lst = list.__iadd__(self, *args, **kwargs)
		return KeyList(lst)


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
