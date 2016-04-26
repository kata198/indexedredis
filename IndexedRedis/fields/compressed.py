# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.compressed - Some types and objects related to compressed fields. Use in place of IRField ( in FIELDS array to activate functionality )
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :


import zlib
import bz2

from . import IRField, irNull

from ..compat_str import tobytes


__all__ = ('COMPRESS_MODE_BZ2', 'COMPRESS_MODE_ZLIB', 'IRCompressedField')

# COMPRESS_MODE_ZLIB - Use to compress using zlib (gzip)
COMPRESS_MODE_ZLIB = 'zlib'
# COMPRESS_MODE_BZ2 - Use to compress using bz2 (bz2)
COMPRESS_MODE_BZ2 = 'bz2'

try:
	unicode
except NameError:
	unicode = str


class IRCompressedField(IRField):
	'''
		IRCompressedField - A field that automatically compresses/decompresses going to/from Redis.

		Pass this into the FIELDS array of the model to get this functionality,

		like: 
			FIELDS  = [ ..., IRCompressedField('my_compressed_field', compressMode=COMPRESS_MODE_ZLIB]
	'''

	CAN_INDEX = False

	# TODO: maybe support other compression levels. The headers change with different levels.
	#  These are for 9.
	def __init__(self, name='', compressMode=COMPRESS_MODE_ZLIB):
		'''
			__init__ - Create this object
		'''
		self.valueType = None
		if compressMode == COMPRESS_MODE_ZLIB:
			self.compressMode = compressMode
			self.header = b'x\xda'
		elif compressMode == COMPRESS_MODE_BZ2:
			self.compressMode = compressMode
			self.header = b'BZh9'
		else:
			raise ValueError('Invalid compressMode, "%s", for field "%s". Should be one of the IndexedRedis.fields.compressed.COMPRESS_MODE_* constants.' %(str(compressMode), name))


	def getCompressMod(self):
		if self.compressMode == COMPRESS_MODE_ZLIB:
			return zlib
		if self.compressMode == COMPRESS_MODE_BZ2:
			return bz2

	def toStorage(self, value):
		if self._isNullValue(value):
			return value
		if tobytes(value[:len(self.header)]) == self.header:
			return value
		return self.getCompressMod().compress(tobytes(value), 9)

	def convert(self, value):
		if not value:
			return value
		if issubclass(value.__class__, (bytes, str, unicode)) and tobytes(value[:len(self.header)]) == self.header:
			return self.getCompressMod().decompress(value)

		return value

	def __new__(self, name='', compressMode=COMPRESS_MODE_ZLIB):
		return IRField.__new__(self, name)


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
