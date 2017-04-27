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
	def to_unicode(x, encoding=None):
		'''
			to_unicode - Ensure a given value is decoded into unicode type

			@param x - Value
			@param encoding <None/str> (default None) - None to use defaultIREncoding, otherwise an explicit encoding

			@return - "x" as a unicode type
		'''
		if encoding is None:
			global defaultIREncoding
			encoding = defaultIREncoding

		if isinstance(x, unicode):
			return x
		elif isinstance(x, str):
			return x.decode(encoding)
		else:
			return str(x).decode(encoding)


	def tobytes(x, encoding=None):
		'''
			tobytes - Ensure that a given value is encoded into bytes (str on python2)

			@param x - Value
			@param encoding <None/str> (default None) - None to use defaultIREncoding, otherwise an explicit encoding

			@return - "x" as a bytes (str on python2) type
		'''
		if encoding is None:
			global defaultIREncoding
			encoding = defaultIREncoding

		if isinstance(x, str):
			return x
		try:
			return str(x)
		except:
			return x.encode(encoding)
#	tobytes = lambda x : str(x)

	def isStringy(x):
		'''
			isStringy - Check if a given value extends from any string-like type (basestring on python2)

			@param x - Value to check

			@return <bool> - True if "x" is a stringy type
		'''
		return issubclass(x.__class__, basestring)

	def isBaseStringy(x):
		'''
			isBaseStringy - Chek if is a "basestring" extending class.

			@param x - Value to chek

			@return <bool> - True if "x" is a "basestring" extending type
		'''
		return issubclass(x.__class__, basestring)
	
	encoded_str_type = unicode

	def isEmptyString(x):
		'''
			isEmptyString - Check if x is an empty string
		'''
		if issubclass(x.__class__, str):
			return bool(x == '')
		elif issubclass(x.__class__, unicode):
			return bool(x == u'')

		return False

else:
	# Python 3
	def to_unicode(x, encoding=None):
		'''
			to_unicode - Ensure a given value is decoded into unicode type (str on python3)

			@param x - Value
			@param encoding <None/str> (default None) - None to use defaultIREncoding, otherwise an explicit encoding

			@return - "x" as a unicode (str on python3) type
		'''
		if encoding is None:
			global defaultIREncoding
			encoding = defaultIREncoding

		if isinstance(x, bytes) is False:
			return str(x)
		return x.decode(encoding)

	def tobytes(x, encoding=None):
		'''
			tobytes - Ensure that a given value is encoded into bytes

			@param x - Value
			@param encoding <None/str> (default None) - None to use defaultIREncoding, otherwise an explicit encoding

			@return - "x" as a bytes type
		'''
		if encoding is None:
			global defaultIREncoding
			encoding = defaultIREncoding

		if isinstance(x, bytes) is True:
			return x
		return x.encode(encoding)

	def isStringy(x):
		'''
			isStringy - Check if a given value extends from any string-like type (str or bytes on python3)

			@param x - Value to check

			@return <bool> - True if "x" is a stringy type
		'''
		return issubclass(x.__class__, (str, bytes))

	def isBaseStringy(x):
		'''
			isBaseStringy - Chek if is a "basestring" extending class.

			@param x - Value to chek

			@return <bool> - True if "x" is a "basestring" extending type
		'''
		return issubclass(x.__class__, basestring)
	

	def isEmptyString(x):
		'''
			isEmptyString - Check if x is an empty string
		'''
		if issubclass(x.__class__, bytes):
			return bool(x == b'')
		elif issubclass(x.__class__, str):
			return bool(x == '')
		return False

	encoded_str_type = str

def isEncodedString(x):
	'''
		isEncodedString - Check if a given string is "encoded" with a codepage.

		  Note this means UNICODE, not BYTES, even though python uses "decode" to apply an encoding and "encode" to get the raw bytes..
	'''
	return issubclass(x.__class__, encoded_str_type)

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
