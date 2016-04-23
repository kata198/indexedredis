# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# IRQueryableList - QueryableList with some added callbacks to IndexedRedis
#

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import sys

__all__ = ('defaultIREncoding', 'to_unicode', 'tobytes', 'setDefaultIREncoding', 'setEncoding', 'getDefaultIREncoding', 'getEncoding')

try:
	global defaultIREncoding
	defaultIREncoding = sys.getdefaultencoding()
	if defaultIREncoding == 'ascii':
		defaultIREncoding = 'utf-8'
except:
	defaultIREncoding = 'utf-8'

# COMPAT: OLD NAME (defaultEncoding -> defaultIREncoding)
global defaultEncoding
defaultEncoding = defaultIREncoding

# Encoding stuff

def setDefaultIREncoding(encoding):
	'''
		setDefaultIREncoding - Sets the default encoding used by IndexedRedis.
		  This will be the default encoding used for field data. You can override this on a
		  per-field basis by using an IRField (such as IRUnicodeField or IRRawField)

		@param encoding - An encoding (like utf-8)
	'''
	try:
		b''.decode(encoding)
	except:
		raise ValueError('setDefaultIREncoding was provided an invalid codec. Got (encoding="%s")' %(str(encoding), ))

	global defaultIREncoding
	defaultIREncoding = encoding
	# COMPAT: OLD NAME (defaultEncoding -> defaultIREncoding
	global defaultEncoding
	defaultEncoding = defaultIREncoding

setIndexedRedisEncoding = setDefaultIREncoding
setEncoding = setDefaultIREncoding

def getDefaultIREncoding():
	'''
		getEncoding - Get the default encoding that IndexedRedis will use for all field data.
		  You can override this on a per-field basis by using an IRField (such as IRUnicodeField or IRRawField)

		  @return <str> - Default encoding string
	'''
	global defaultIREncoding
	return defaultIREncoding

getIndexedRedisEncoding = getDefaultIREncoding
getEncoding = getDefaultIREncoding

# String Assurance

if bytes == str:
	# Python 2
	def to_unicode(x):
		if isinstance(x, unicode):
			return x
		elif isinstance(x, str):
			return x.decode(defaultIREncoding)
		else:
			return str(x).decode(defaultIREncoding)


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
		return x.decode(defaultIREncoding)

	def tobytes(x):
		if isinstance(x, bytes) is True:
			return x
		return x.encode(defaultIREncoding)

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
