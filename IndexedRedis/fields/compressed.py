# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.compressed - Some types and objects related to compressed fields
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :


import zlib
import bz2

from . import IRField, irNull

from ..compat_str import tobytes


__all__ = ('COMPRESS_MODE_BZ2', 'COMPRESS_MODE_ZLIB', 'IRCompressedField')

COMPRESS_MODE_ZLIB = 'zlib'
COMPRESS_MODE_BZ2 = 'bz2'

# TODO: Figure out why this is getting compressed and decompressed for each save. 

class IRCompressedField(IRField):

	# TODO: maybe support other compression levels. The headers change with different levels.
	#  These are for 9.
	def __init__(self, val, valueType=None, compressMode=COMPRESS_MODE_ZLIB):
		if valueType is not None:
			raise ValueError('IRCompressedField with any valueType other than None is invalid.')
		self.valueType = None
		if compressMode == COMPRESS_MODE_ZLIB:
			self.compressMode = compressMode
			self.header = b'x\xda'
		elif compressMode == COMPRESS_MODE_BZ2:
			self.compressMode = compressMode
			self.header = b'BZh9'
		else:
			raise ValueError('Invalid compressMode, "%s", for field "%s". Should be one of the IndexedRedis.fields.compressed.COMPRESS_MODE_* constants.' %(str(compressMode), val))

	def getCompressMod(self):
		if self.compressMode == COMPRESS_MODE_ZLIB:
			return zlib
		if self.compressMode == COMPRESS_MODE_BZ2:
			return bz2

	def toStorage(self, value):
		if value in ('', irNull):
			return value
		if tobytes(value[:len(self.header)]) == self.header:
			return value
		return self.getCompressMod().compress(tobytes(value), 9)

	def convert(self, value):
		if not value:
			return value
		if tobytes(value[:len(self.header)]) == self.header:
			return self.getCompressMod().decompress(value)

		return value

	@classmethod
	def canIndex(cls):
		return False

	def __new__(self, val, valueType=None, compressMode=COMPRESS_MODE_ZLIB):
		return str.__new__(self, val)


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
