# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# IRQueryableList - QueryableList with some added callbacks to IndexedRedis
#

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import sys

__all__ = ('defaultIREncoding', 'to_unicode', 'tobytes', 'setDefaultIREncoding', 'getDefaultIREncoding')

try:
	global defaultIREncoding
	defaultIREncoding = sys.getdefaultencoding()
	if defaultIREncoding == 'ascii':
		defaultIREncoding = 'utf-8'
except:
	defaultIREncoding = 'utf-8'

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

def getDefaultIREncoding():
	'''
		getDefaultIREncoding - Get the default encoding that IndexedRedis will use for all field data.
		  You can override this on a per-field basis by using an IRField (such as IRUnicodeField or IRRawField)

		  @return <str> - Default encoding string
	'''
	global defaultIREncoding
	return defaultIREncoding


# String Assurance

if bytes == str:
	# Python 2
	def to_unicode(x):
		global defaultIREncoding
		if isinstance(x, unicode):
			return x
		elif isinstance(x, str):
			return x.decode(defaultIREncoding)
		else:
			return str(x).decode(defaultIREncoding)


	def tobytes(x):
		global defaultIREncoding
		if isinstance(x, str):
			return x
		try:
			return str(x)
		except:
			return x.encode(defaultIREncoding)
#	tobytes = lambda x : str(x)

	def isStringy(x):
		return issubclass(x.__class__, basestring)
	
	encoded_str_type = unicode

else:
	# Python 3
	def to_unicode(x):
		global defaultIREncoding
		if isinstance(x, bytes) is False:
			return str(x)
		return x.decode(defaultIREncoding)

	def tobytes(x):
		global defaultIREncoding
		if isinstance(x, bytes) is True:
			return x
		return x.encode(defaultIREncoding)

	def isStringy(x):
		return issubclass(x.__class__, (str, bytes))

	encoded_str_type = str

def isEncodedString(x):
	return issubclass(x.__class__, encoded_str_type)

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
