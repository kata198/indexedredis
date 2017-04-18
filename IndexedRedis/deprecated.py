# Copyright (c) 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# deprecated - Mark things as deprecated.
#

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from hashlib import md5

import traceback
import sys

__all__ = ('toggleDeprecatedMessages', 'deprecated', 'deprecatedMessage')

global __deprecatedMessagesEnabled
__deprecatedMessagesEnabled = True

def toggleDeprecatedMessages(enabled):
	'''
		toggleDeprecatedMessages - Normally, a deprecated message will log up to once per message.
		  Call toggleDeprecatedMessages(False) to turn them off altogether (like on a Production codebase)
		
		@param enabled <bool> - False to disable deprecated messages, otherwise True.
	'''

	global __deprecatedMessagesEnabled
	__deprecatedMessagesEnabled = enabled


global _alreadyWarned
_alreadyWarned = {}

def deprecatedMessage(msg, key=None, printStack=False):
	'''
		deprecatedMessage - Print a deprecated messsage (unless they are toggled off). Will print a message only once (based on "key")

		@param msg <str> - Deprecated message to possibly print
		
		@param key <anything> - A key that is specific to this message. 
			If None is provided (default), one will be generated from the md5 of the message.
		        However, better to save cycles and provide a unique key if at all possible.
			The decorator uses the function itself as the key.

		@param printStack <bool> Default False, if True print a stack trace
	'''
	if __deprecatedMessagesEnabled is False:
		return
	if not _alreadyWarned:
		# First warning, let them know how to disable. 
		sys.stderr.write('== DeprecatedWarning: warnings can be disabled by calling IndexedRedis.toggleDeprecatedMessages(False)\n')
	if key is None:
		from .compat_str import tobytes
		key = md5(tobytes(msg)).hexdigest()

	if key not in _alreadyWarned:
		_alreadyWarned[key] = True
		sys.stderr.write('== DeprecatedWarning: %s\n' %(msg, ))
		if printStack:
			sys.stderr.write('  at:\n')
			curStack = traceback.extract_stack()

			sys.stderr.write('  ' + '\n  '.join(traceback.format_list(curStack[:-2])).replace('\t', '    ') + '\n')


def deprecated(msg):

	def _deprecated_decorator(func):

		def _deprecated_wrapper(*args, **kwargs):
			deprecatedMessage(msg, func)
			return func(*args, **kwargs)

		return _deprecated_wrapper

	return _deprecated_decorator
            
            
# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
