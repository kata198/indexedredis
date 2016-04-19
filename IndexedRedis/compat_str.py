# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# IRQueryableList - QueryableList with some added callbacks to IndexedRedis
#

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import sys

__all__ = ('defaultEncoding', 'to_unicode', 'tobytes')

try:
	global defaultEncoding
	defaultEncoding = sys.getdefaultencoding()
	if defaultEncoding == 'ascii':
		defaultEncoding = 'utf-8'
except:
	defaultEncoding = 'utf-8'

# Encoding stuff

def setEncoding(encoding):
	'''
		setEncoding - Sets the encoding used by IndexedRedis. 

		@note Aliased as "setIndexedRedisEncoding" so import * has a namespaced name.

		@param encoding - An encoding (like utf-8)
	'''
	global defaultEncoding
	defaultEncoding = encoding

setIndexedRedisEncoding = setEncoding

def getEncoding():
	'''
		getEncoding - Get the encoding that IndexedRedis will use

	@note Aliased as "setIndexedRedisEncoding" so import * has a namespaced name.

	'''
	global defaultEncoding
	return defaultEncoding

getIndexedRedisEncoding = getEncoding

# String Assurance

if bytes == str:
	# Python 2
	def to_unicode(x):
		if isinstance(x, unicode):
			return x
		elif isinstance(x, str):
			return x.decode(defaultEncoding)
		else:
			return str(x).decode(defaultEncoding)


	def tobytes(x):
		if isinstance(x, str):
			return x
		return str(x)
#	tobytes = lambda x : str(x)
else:
	# Python 3
	
	def to_unicode(x):
		if isinstance(x, bytes) is False:
			return str(x)
		return x.decode(defaultEncoding)

	def tobytes(x):
		if isinstance(x, bytes) is True:
			return x
		return x.encode(defaultEncoding)

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
