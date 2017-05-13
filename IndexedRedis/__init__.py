# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#  IndexedRedis A redis-backed very very fast ORM-style framework that supports indexes, and searches with O(1) efficency.
#    It has syntax similar to Django and Flask and other ORMs, but is itself unique in many ways.



# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import copy
import codecs
import pprint
import random
import redis
import sys
import uuid

from collections import defaultdict

from . import fields
from .fields import IRField, IRFieldChain, IRClassicField, IRNullType, irNull, IR_NULL_STR
from .compat_str import to_unicode, tobytes, setDefaultIREncoding, getDefaultIREncoding
from .utils import hashDictOneLevel, KeyList

from .IRQueryableList import IRQueryableList



from .deprecated import deprecated, toggleDeprecatedMessages, deprecatedMessage

# * imports
__all__ = ('INDEXED_REDIS_PREFIX', 'INDEXED_REDIS_VERSION', 'INDEXED_REDIS_VERSION_STR', 
	'IndexedRedisDelete', 'IndexedRedisHelper', 'IndexedRedisModel', 'IndexedRedisQuery', 'IndexedRedisSave',
	'isIndexedRedisModel', 'setIndexedRedisEncoding', 'getIndexedRedisEncoding', 'InvalidModelException',
	'fields', 'IRField', 'IRFieldChain', 'irNull',
	'setDefaultIREncoding', 'getDefaultIREncoding',
	'setDefaultRedisConnectionParams', 'getDefaultRedisConnectionParams',
	'toggleDeprecatedMessages',
	 )

# Prefix that all IndexedRedis keys will contain, as to not conflict with other stuff.
INDEXED_REDIS_PREFIX = '_ir_|'

# Version as a tuple (major, minor, patchlevel)
INDEXED_REDIS_VERSION = (5, 0, 2)

# Version as a string
INDEXED_REDIS_VERSION_STR = '5.0.2'

# Package version
__version__ = INDEXED_REDIS_VERSION_STR

# Default max number of connections to each unique server, as connections can get eaten up in some circumstances,
#   and python-redis has default of 2^31 connections... which doesn't make any sense given only 65535 ports..
#   In a network-outage scenario, python-redis can quickly leak connections and exhaust all private ports
REDIS_DEFAULT_POOL_MAX_SIZE = 32

global _defaultRedisConnectionParams
_defaultRedisConnectionParams = { 'host' : '127.0.0.1', 'port' : 6379, 'db' : 0 }

global RedisPools
RedisPools = {}

global _redisManagedConnectionParams
_redisManagedConnectionParams = {}

def setDefaultRedisConnectionParams( connectionParams ):
	'''
		setDefaultRedisConnectionParams - Sets the default parameters used when connecting to Redis.

		  This should be the args to redis.Redis in dict (kwargs) form.

		  @param connectionParams <dict> - A dict of connection parameters.
		    Common keys are:

		       host <str> - hostname/ip of Redis server (default '127.0.0.1')
		       port <int> - Port number			(default 6379)
		       db  <int>  - Redis DB number		(default 0)

		   Omitting any of those keys will ensure the default value listed is used.

		  This connection info will be used by default for all connections to Redis, unless explicitly set otherwise.
		  The common way to override is to define REDIS_CONNECTION_PARAMS on a model, or use AltConnectedModel = MyModel.connectAlt( PARAMS )

		  Any omitted fields in these connection overrides will inherit the value from the global default.

		  For example, if your global default connection params define host = 'example.com', port=15000, and db=0, 
		    and then one of your models has
		       
		       REDIS_CONNECTION_PARAMS = { 'db' : 1 }
		    
		    as an attribute, then that model's connection will inherit host='example.com" and port=15000 but override db and use db=1


		    NOTE: Calling this function will clear the connection_pool attribute of all stored managed connections, disconnect all managed connections,
		      and close-out the connection pool.
		     It may not be safe to call this function while other threads are potentially hitting Redis (not that it would make sense anyway...)

		     @see clearRedisPools   for more info
	'''
	global _defaultRedisConnectionParams
	_defaultRedisConnectionParams.clear()

	for key, value in connectionParams.items():
		_defaultRedisConnectionParams[key] = value
	
	clearRedisPools()

def getDefaultRedisConnectionParams():
	'''
		getDefaultRedisConnectionParams - Gets A COPY OF the default Redis connection params.

		@see setDefaultRedisConnectionParams for more info

		@return <dict> - copy of default Redis connection parameters
	'''
	global _defaultRedisConnectionParams
	return copy.copy(_defaultRedisConnectionParams)

def clearRedisPools():
	'''
		clearRedisPools - Disconnect all managed connection pools, 
		   and clear the connectiobn_pool attribute on all stored managed connection pools.

		   A "managed" connection pool is one where REDIS_CONNECTION_PARAMS does not define the "connection_pool" attribute.
		   If you define your own pools, IndexedRedis will use them and leave them alone.

		  This method will be called automatically after calling setDefaultRedisConnectionParams.

		  Otherwise, you shouldn't have to call it.. Maybe as some sort of disaster-recovery call..
	'''
	global RedisPools
	global _redisManagedConnectionParams

	for pool in RedisPools.values():
		try:
			pool.disconnect()
		except:
			pass
	
	for paramsList in _redisManagedConnectionParams.values():
		for params in paramsList:
			if 'connection_pool' in params:
				del params['connection_pool']
	
	RedisPools.clear()
	_redisManagedConnectionParams.clear()
		

def getRedisPool(params):
	'''
		getRedisPool - Returns and possibly also creates a Redis connection pool
			based on the REDIS_CONNECTION_PARAMS passed in.

			The goal of this method is to keep a small connection pool rolling
			to each unique Redis instance, otherwise during network issues etc
			python-redis will leak connections and in short-order can exhaust
			all the ports on a system. There's probably also some minor
			performance gain in sharing Pools.

			Will modify "params", if "host" and/or "port" are missing, will fill
			them in with defaults, and prior to return will set "connection_pool"
			on params, which will allow immediate return on the next call,
			and allow access to the pool directly from the model object.

			@param params <dict> - REDIS_CONNECTION_PARAMS - kwargs to redis.Redis

			@return redis.ConnectionPool corrosponding to this unique server.
	'''
	global RedisPools
	global _defaultRedisConnectionParams
	global _redisManagedConnectionParams

	if not params:
		params = _defaultRedisConnectionParams
		isDefaultParams = True
	else:
		isDefaultParams = bool(params is _defaultRedisConnectionParams)

	if 'connection_pool' in params:
		return params['connection_pool']

	hashValue = hashDictOneLevel(params)

	if hashValue in RedisPools:
		params['connection_pool'] = RedisPools[hashValue]
		return RedisPools[hashValue]
	
	# Copy the params, so that we don't modify the original dict
	if not isDefaultParams:
		origParams = params
		params = copy.copy(params)
	else:
		origParams = params

	checkAgain = False
	if 'host' not in params:
		if not isDefaultParams and 'host' in _defaultRedisConnectionParams:
			params['host'] = _defaultRedisConnectionParams['host']
		else:
			params['host'] = '127.0.0.1'
		checkAgain = True
	if 'port' not in params:
		if not isDefaultParams and 'port' in _defaultRedisConnectionParams:
			params['port'] = _defaultRedisConnectionParams['port']
		else:
			params['port'] = 6379
		checkAgain = True
	
	if 'db' not in params:
		if not isDefaultParams and 'db' in _defaultRedisConnectionParams:
			params['db'] = _defaultRedisConnectionParams['db']
		else:
			params['db'] = 0
		checkAgain = True


	if not isDefaultParams:
		otherGlobalKeys = set(_defaultRedisConnectionParams.keys()) - set(params.keys())
		for otherKey in otherGlobalKeys:
			if otherKey == 'connection_pool':
				continue
			params[otherKey] = _defaultRedisConnectionParams[otherKey]
			checkAgain = True

	if checkAgain:
		hashValue = hashDictOneLevel(params)
		if hashValue in RedisPools:
			params['connection_pool'] = RedisPools[hashValue]
			return RedisPools[hashValue]

	connectionPool = redis.ConnectionPool(**params)
	origParams['connection_pool'] = params['connection_pool'] = connectionPool
	RedisPools[hashValue] = connectionPool

	# Add the original as a "managed" redis connection (they did not provide their own pool)
	#   such that if the defaults change, we make sure to re-inherit any keys, and can disconnect
	#   from clearRedisPools
	origParamsHash = hashDictOneLevel(origParams)
	if origParamsHash not in _redisManagedConnectionParams:
		_redisManagedConnectionParams[origParamsHash] = [origParams]
	elif origParams not in _redisManagedConnectionParams[origParamsHash]:
		_redisManagedConnectionParams[origParamsHash].append(origParams)


	return connectionPool



# COMPAT STUFF
try:
	classproperty
except NameError:
	class classproperty(object):
		def __init__(self, getter):
			self.getter = getter
		def __get__(self, instance, owner):
			return self.getter(owner)



# This is an incrementing integer, for each copy of a model (to ensure they have a unique name)
global _modelCopyMap
_modelCopyMap = defaultdict(lambda : int(1))


# Changing redis encoding into requested encoding
decodeDict = lambda origDict : {to_unicode(key) : origDict[key] for key in origDict}

global validatedModels
validatedModels = set()

def isIndexedRedisModel(model):
	return hasattr(model, '_is_ir_model')


class InvalidModelException(Exception):
	'''
		InvalidModelException - Raised if a model fails validation (not valid)
	'''
	pass

class IndexedRedisModel(object):
	'''
           IndexedRedisModel - This is the model you should extend.

		See: https://github.com/kata198/indexedredis/blob/master/README.md for documentation


            **Attributes**

		FIELDS - An array of IRField objects, which define the fields on this model.

		INDEXED_FIELDS - The field names on which to index

		KEY_NAME - A string of the "key" name which will be used for this model

	        REDIS_CONNECTION_PARAMS - A dict which provides fields to override over the inherited default Redis connection

	     
	     **Basic Usage**

	       The basic model for usage is,

		# Filtering

	       MyModel.objects.filter(field1='value1', field2__ne='notvalue2').all()   # Fetch all objects where field1 is "value1" and field2 is not "notvalue2"

		# Creating / Saving object

	       myObj = MyModel()

	       myObj.field1 = 'value1'

	       myObj.save()

	       
	       There are many more methods and usage, etc, see pydoc or README for more information.

	'''
	
	# FIELDS - A list of field names, as strings.
	FIELDS = []

	# INDEXED_FIELDS - A list of field names that will be indexed, as strings. Must also be present in FIELDS.
	#  You can only search on indexed fields, but they add time to insertion/deletion
	INDEXED_FIELDS = []

	# KEY_NAME - A string of a unique name which corrosponds to objects of this type.
	KEY_NAME = None

	# REDIS_CONNECTION_PARAMS - A dictionary of parameters to redis.Redis such as host or port. Unless "connection_pool" is specified,
	#   each unique server will be assigned a pool to prevent leaking private ports, and on first connection of this model
	#   that pool will be accessable via REDIS_CONNECTION_PARAMS['connection_pool']
	REDIS_CONNECTION_PARAMS = {}

	# Internal property to check inheritance
	_is_ir_model = True

	def __init__(self, *args, **kwargs):
		'''
			__init__ - Set the values on this object. MAKE SURE YOU CALL THE SUPER HERE, or else things will not work.
		'''
		self.validateModel()

		object.__setattr__(self, '_origData', {})

		# Figure out if we are convert from the database, or from direct input
		if kwargs.get('__fromRedis', False) is True:
			convertFunctionName = 'fromStorage'
		else:
			convertFunctionName = 'fromInput'

		for thisField in self.FIELDS:
			if thisField not in kwargs:
				val = thisField.getDefaultValue()
			else:
				val = kwargs[thisField]
				val = getattr(thisField, convertFunctionName)(val)

			object.__setattr__(self, thisField, val)
			# Generally, we want to copy the value incase it is used by reference (like a list)
			#   we will miss the update (an append will affect both).
			try:
				self._origData[thisField] = copy.copy(val)
			except:
				self._origData[thisField] = val
				

		object.__setattr__(self, '_id', kwargs.get('_id', None))


	def __setattr__(self, keyName, value):
		'''
			__setattr__ - Will be used to set an attribute on this object.

			  If the attribute is a field (in self.FIELDS), it will be converted via the field type's #fromInput method.

			  Otherwise, it will just set the attribute on this object.
		'''
		try:
			idx = self.FIELDS.index(keyName)
		except:
			idx = -1

		if idx != -1:
			value = self.FIELDS[idx].fromInput(value)

		object.__setattr__(self, keyName, value)

	
	def asDict(self, includeMeta=False, forStorage=False, strKeys=False):
		'''
			toDict / asDict - Get a dictionary representation of this model.

			@param includeMeta - Include metadata in return. For now, this is only pk stored as "_id"

			@param convertValueTypes <bool> - default True. If False, fields with fieldValue defined will be converted to that type.
				Use True when saving, etc, as native type is always either str or bytes.

			@param strKeys <bool> Default False - If True, just the string value of the field name will be used as the key.
				Otherwise, the IRField itself will be (although represented and indexed by string)

			@return - Dictionary reprensetation of this object and all fields
		'''
		ret = {}
		for thisField in self.FIELDS:
			val = getattr(self, thisField, thisField.getDefaultValue())
			if forStorage is True:
				val = thisField.toStorage(val)

			if strKeys:
				ret[str(thisField)] = val
			else:
				ret[thisField] = val
				

		if includeMeta is True:
			ret['_id'] = getattr(self, '_id', '')
		return ret

	toDict = asDict


	def pprint(self, stream=None):
		'''
			pprint - Pretty-print a dict representation of this object.

			@param stream <file/None> - Either a stream to output, or None to default to sys.stdout
		'''
		pprint.pprint(self.asDict(includeMeta=True, forStorage=False, strKeys=True), stream=stream)


	def hasUnsavedChanges(self):
		'''
			hasUnsavedChanges - Check if any unsaved changes are present in this model, or if it has never been saved.

			@return <bool> - True if any fields have changed since last fetch, or if never saved. Otherwise, False
		'''
		if not self._id or not self._origData:
			return True

		for thisField in self.FIELDS:
			thisVal = getattr(self, thisField, '')

			if self._origData.get(thisField, '') != thisVal:
				return True
		return False
	
	def getUpdatedFields(self):
		'''
			getUpdatedFields - See changed fields.
			
			@return - a dictionary of fieldName : tuple(old, new).

			fieldName may be a string or may implement IRField (which implements string, and can be used just like a string)
		'''
		updatedFields = {}
		for thisField in self.FIELDS:
			thisVal = getattr(self, thisField, '')

			if self._origData.get(thisField, '') != thisVal:
				updatedFields[thisField] = (self._origData[thisField], thisVal)
		return updatedFields

	def _getUpdatedFieldsForStorage(self):
		'''
			_getUpdatedFieldsForStorage - Gets any changed fields, taking into account the storage representation

			@return - A dictionary of the fieldName : tuple(oldStorage, newStorage)

			fieldName may be a string or may implement IRField (which implements string, and can be used just like a string)
		'''

		updatedFields = {}
		for thisField in self.FIELDS:
			thisVal = getattr(self, thisField, thisField.getDefaultValue())

			thisVal = thisField.toStorage( thisVal )
			origVal = thisField.toStorage( self._origData.get(thisField, thisField.getDefaultValue()) )

			if thisVal != origVal:
				updatedFields[thisField] = (origVal, thisVal)
		return updatedFields


	@classproperty
	def objects(cls):
		'''
			objects - Start filtering
		'''
		cls.validateModel()
		return IndexedRedisQuery(cls)

	@classproperty
	def saver(cls):
		'''
			saver - Get an IndexedRedisSave associated with this model
		'''
		cls.validateModel()
		return IndexedRedisSave(cls)

	@classproperty
	def deleter(cls):
		'''
			deleter - Get access to IndexedRedisDelete for this model.
			@see IndexedRedisDelete.
			Usually you'll probably just do Model.objects.filter(...).delete()
		'''
		cls.validateModel()
		return IndexedRedisDelete(cls)

	def save(self):
		'''
			save - Save this object.
			
			Will perform an "insert" if this object had not been saved before,
			  otherwise will update JUST the fields changed on THIS INSTANCE of the model.

			  i.e. If you have two processes fetch the same object and change different fields, they will not overwrite
			  eachother, but only save the ones each process changed.

			If you want to save multiple objects of type MyModel in a single transaction,
			and you have those objects in a list, myObjs, you can do the following:

				MyModel.saver.save(myObjs)

			@see #IndexedRedisSave.save

			@return <list> - Single element list, id of saved object (if successful)
		'''
		saver = IndexedRedisSave(self.__class__)
		return saver.save(self)
	
	def delete(self):
		'''
			delete - Delete this object
		'''
		deleter = IndexedRedisDelete(self.__class__)
		return deleter.deleteOne(self)

	def getPk(self):
		'''
			getPk - Gets the internal primary key associated with this object
		'''
		return self._id
		
	
	@classmethod
	def reset(cls, newObjs):
		'''
			reset - Remove all stored data associated with this model (i.e. all objects of this type),
				and then save all the provided objects in #newObjs , all in one atomic transaction.

			Use this method to move from one complete set of objects to another, where any querying applications
			will only see the complete before or complete after.

			@param newObjs list<IndexedRedisModel objs> - A list of objects that will replace the current dataset

			To just replace a specific subset of objects in a single transaction, you can do MyModel.saver.save(objs)
			  and just the objs in "objs" will be inserted/updated in one atomic step.

			This method, on the other hand, will delete all previous objects and add the newly provided objects in a single atomic step,
			  and also reset the primary key ID generator

			@return list<int> - The new primary keys associated with each object (same order as provided #newObjs list)
		'''
		conn = cls.objects._get_new_connection()

		transaction = conn.pipeline()
		transaction.eval("""
		local matchingKeys = redis.call('KEYS', '%s*')

		for _,key in ipairs(matchingKeys) do
			redis.call('DEL', key)
		end
		""" %( ''.join([INDEXED_REDIS_PREFIX, cls.KEY_NAME, ':']), ), 0)
		saver = IndexedRedisSave(cls)
		nextID = 1
		for newObj in newObjs:
			saver.save(newObj, False, nextID, transaction)
			nextID += 1
		transaction.set(saver._get_next_id_key(), nextID)
		transaction.execute()

		return list( range( 1, nextID, 1) )


	def hasSameValues(self, other):
		'''
			hasSameValues - Check if this and another model have the same fields and values.

			This does NOT include id, so the models can have the same values but be different objects in the database.

			@param other <IndexedRedisModel> - Another model

			@return <bool> - True if all fields have the same value, otherwise False
		'''
		if self.FIELDS != other.FIELDS:
			return False

		for field in self.FIELDS:
			if getattr(self, field) != getattr(other, field):
				return False

		return True


	def __eq__(self, other):
		'''
			__eq__ - Check if two IndexedRedisModels are equal.

			They are equal if they have the same type and same field values (including id).

			To check if two models have the same values (but can have different ids), use #hasSameValues method.
		'''
		# Check if the same type
		if type(self) != type(other):
			return False

		if not self.hasSameValues(other):
			return False

		if getattr(self, '_id', None) != getattr(other, '_id', None):
			return False

		return True

	def __ne__(self, other):
		'''
			__ne__ - Check if two IndexedRedisModels are NOT equal.

			@see IndexedRedisModel.__eq__
		'''
		return not self.__eq__(other)


	def __str__(self):
		'''
                    __str__ - Returns a string representation of this object's state.
                        See implementation.

                    @return <str>- 
                        Some samples:
                        (Pdb) str(z)
                        '<Song obj _id=24 at 0x7f3c6a3a4490>'
                        (Pdb) z.artist = 'New Artist'
                        (Pdb) str(z)
                        '<Song obj _id=24 (Unsaved Changes) at 0x7f3c6a3a4490>'
		'''
                    
		myClassName = self.__class__.__name__
		myDict = self.asDict(True, forStorage=False, strKeys=True)
		_id = myDict.pop('_id', 'None')
		myPointerLoc = "0x%x" %(id(self),)
		if not _id or _id == 'None':
			return '<%s obj (Not in DB) at %s>' %(myClassName, myPointerLoc)
		elif self.hasUnsavedChanges():
			return '<%s obj _id=%s (Unsaved Changes) at %s>' %(myClassName, to_unicode(_id), myPointerLoc)
		return '<%s obj _id=%s at %s>' %(myClassName, to_unicode(_id), myPointerLoc)

	def __repr__(self):
		'''
                    __repr__ - Returns a string of the constructor/params to recreate this object.
                        Example: objCopy = eval(repr(obj))

                        @return - String of python init call to recreate this object
		'''
		myDict = self.asDict(True, forStorage=False, strKeys=True)
		myClassName = self.__class__.__name__

		ret = [myClassName, '(']
		# Only show id if saved
		_id = myDict.pop('_id', '')
		if _id:
			ret += ['_id="', to_unicode(_id), '", ']

		key = None
		for key, value in myDict.items():
			ret += [key, '=', repr(value), ', ']

		if key is not None or not _id:
			# At least one iteration, so strip trailing comma
			ret.pop()
		ret.append(')')

		return ''.join(ret)


	def copy(self, copyPrimaryKey=False, copyValues=False):
		'''
                    copy - Copies this object.

                    @param copyPrimaryKey <bool> default False - If True, any changes to the copy will save over-top the existing entry in Redis.
                        If False, only the data is copied, and nothing is saved.

		    @param copyValues <bool> default False - If True, every field value on this object will be explicitly copied. If False,
		      an object will be created with the same values, and depending on the type may share the same reference.
		      
		      This is the difference between a copy and a deepcopy.

	            @return <IndexedRedisModel> - Copy of this object, per above

		    If you need a copy that IS linked, @see IndexedRedisModel.copy
		'''
		cpy = self.__class__(**self.asDict(copyPrimaryKey, forStorage=False))
		if copyValues is True:
			for fieldName in cpy.FIELDS:
				setattr(cpy, fieldName, copy.deepcopy(getattr(cpy, fieldName)))
		return cpy

	def __copy__(self):
		'''
			__copy__ - Used by the "copy" module to make a copy,
			  which will NOT be linked to the original entry in the database, but will contain the same data

		       @return <IndexedRedisModel> - Copy of this object, per above
		'''
		return self.copy(copyPrimaryKey=False, copyValues=False)

	def __deepcopy__(self, *args, **kwargs):
		'''
			__deepcopy__ - Used by the "copy" module to make a deepcopy.

			  Will perform a deepcopy of all attributes, which will NOT be linked to the original entry in the database.


			  If you need a copy that IS linked, @see IndexedRedisModel.copy

		       @return <IndexedRedisModel> - Deep copy of this object, per above
		'''
		# Generate an unlinked model with explicit copies of all values
		cpy = self.copy(copyPrimaryKey=False, copyValues=True)

		# Also make copies of FIELDS and INDEXED_FIELDS
		cpy.FIELDS = cpy.FIELDS[:]
		cpy.INDEXED_FIELDS = cpy.INDEXED_FIELDS[:]

		# Copy all data

		return cpy



	def saveToExternal(self, redisCon):
		'''
			saveToExternal - Saves this object to a different Redis than that specified by REDIS_CONNECTION_PARAMS on this model.

			@param redisCon <dict/redis.Redis> - Either a dict of connection params, a la REDIS_CONNECTION_PARAMS, or an existing Redis connection.
				If you are doing a lot of bulk copies, it is recommended that you create a Redis connection and pass it in rather than establish a new
				connection with each call.

			@note - You will generate a new primary key relative to the external Redis environment. If you need to reference a "shared" primary key, it is better
					to use an indexed field than the internal pk.

		'''
		if type(redisCon) == dict:
			conn = redis.Redis(**redisCon)
		elif hasattr(conn, '__class__') and issubclass(conn.__class__, redis.Redis):
			conn = redisCon
		else:
			raise ValueError('saveToExternal "redisCon" param must either be a dictionary of connection parameters, or redis.Redis, or extension thereof')

		saver = self.saver

		# Fetch next PK from external
		forceID = saver._getNextID(conn) # Redundant because of changes in save method
		myCopy = self.copy(False)

		return saver.save(myCopy, usePipeline=True, forceID=forceID, conn=conn)

	def reload(self):
		'''
                reload - Reload this object from the database, overriding any local changes and merging in any updates.

                    @raises KeyError - if this object has not been saved (no primary key)

                    @return - Dict with the keys that were updated. Key is field name that was updated,
		       and value is tuple of (old value, new value). 

		'''
		_id = self._id
		if not _id:
			raise KeyError('Object has never been saved! Cannot reload.')

		currentData = self.asDict(False, forStorage=False)

		# Get the object, and compare the unconverted "asDict" repr.
		#  If any changes, we will apply the already-convered value from
		#  the object, but we compare the unconverted values (what's in the DB).
		newDataObj = self.objects.get(_id)
		if not newDataObj:
			raise KeyError('Object with id=%d is not in database. Cannot reload.' %(_id,))

		newData = newDataObj.asDict(False, forStorage=False)
		if currentData == newData:
			return []

		updatedFields = {}
		for thisField, newValue in newData.items():
			defaultValue = thisField.getDefaultValue()
			currentValue = currentData.get(thisField, defaultValue)
			if currentValue != newValue:
				# Use "converted" values in the updatedFields dict, and apply on the object.
				updatedFields[thisField] = ( currentValue, newValue) 
				setattr(self, thisField, newValue)
				self._origData[thisField] = newDataObj._origData[thisField]

		return updatedFields



	def __getstate__(self):
		'''
                pickle uses this
		'''
		myData = self.asDict(True, forStorage=False)
		myData['_origData'] = self._origData
		return myData

	def __setstate__(self, stateDict):
		'''
                pickle uses this
		'''
		self.__class__.validateModel()
		for key, value in stateDict.items():
			setattr(self, key, value)
		self._origData = stateDict['_origData']

	@classmethod
	def copyModel(mdl):
		'''
			copyModel - Copy this model, and return that copy.

			  The copied model will have all the same data, but will have a fresh instance of the FIELDS array and all members,
			    and the INDEXED_FIELDS array.
			  
			  This is useful for converting, like changing field types or whatever, where you can load from one model and save into the other.

			@return <IndexedRedisModel> - A copy class of this model class with a unique name.
		'''
			     
		copyNum = _modelCopyMap[mdl]
		_modelCopyMap[mdl] += 1
		mdlCopy = type(mdl.__name__ + '_Copy' + str(copyNum), mdl.__bases__, copy.deepcopy(dict(mdl.__dict__)))

		mdlCopy.FIELDS = [field.copy() for field in mdl.FIELDS]
		
		mdlCopy.INDEXED_FIELDS = [str(idxField) for idxField in mdl.INDEXED_FIELDS] # Make sure they didn't do INDEXED_FIELDS = FIELDS or something wacky,
											    #  so do a comprehension of str on these to make sure we only get names

		mdlCopy.validateModel()

		return mdlCopy


	@classmethod
	def validateModel(model):
		'''
			validateModel - Class method that validates a given model is implemented correctly. Will only be validated once, on first model instantiation.

			@param model - Implicit of own class

			@return - True

			@raises - InvalidModelException if there is a problem with the model, and the message contains relevant information.
		'''
		if model == IndexedRedisModel:
			import re
			if re.match('.*pydoc(|[\d]|[\d][\.][\d])([\.]py(|[co])){0,1}$', sys.argv[0]):
				return
			raise ValueError('Cannot use IndexedRedisModel directly. You must implement this class for your model.')

		global validatedModels
		keyName = model.KEY_NAME
		if not keyName:
			raise InvalidModelException('"%s" has no KEY_NAME defined.' %(str(model.__name__), ) )

		if model in validatedModels:
			return True

		failedValidationStr = '"%s" Failed Model Validation:' %(str(model.__name__), ) 

		# Convert items in model to set
		#model.FIELDS = set(model.FIELDS)

		
		fieldSet = set(model.FIELDS)
		indexedFieldSet = set(model.INDEXED_FIELDS)

		if not fieldSet:
			raise InvalidModelException('%s No fields defined. Please populate the FIELDS array with a list of field names' %(failedValidationStr,))


		if hasattr(model, 'BASE64_FIELDS'):
			raise InvalidModelException('BASE64_FIELDS is no longer supported since IndexedRedis 5.0.0 . Use IndexedRedis.fields.IRBase64Field in the FIELDS array for the same functionality.')

		if hasattr(model, 'BINARY_FIELDS'):
			raise InvalidModelException('BINARY_FIELDS is no longer supported since IndexedRedis 5.0.0 . Use IndexedRedis.fields.IRBytesField in the FIELDS array for the same functionality, use IRBytesField for same functionality. Use IRField(valueType=bytes) for python-3 only support. Use IRRawField to perform no conversion at all.')

		newFields = []
		updatedFields = []
		mustUpdateFields = False

		for thisField in fieldSet:
			if thisField == '_id':
				raise InvalidModelException('%s You cannot have a field named _id, it is reserved for the primary key.' %(failedValidationStr,))

			# XXX: Is this ascii requirement still needed since all is unicode now?
			try:
				codecs.ascii_encode(thisField)
			except UnicodeDecodeError as e:
				raise InvalidModelException('%s All field names must be ascii-encodable. "%s" was not. Error was: %s' %(failedValidationStr, to_unicode(thisField), str(e)))
			# If a classic string field, convert to IRClassicField
			if issubclass(thisField.__class__, IRField):
				newFields.append(thisField)
			else:
				mustUpdateFields = True
				newField = IRClassicField(thisField)
				newFields.append(newField)
				updatedFields.append(thisField)

				thisField = newField

			if str(thisField) == '':
				raise InvalidModelException('%s Field defined without a name, or name was an empty string. Type=%s  Field is:  %s' %(failedValidationStr, str(type(thisField)), repr(thisField)   ) )

			if thisField in indexedFieldSet and thisField.CAN_INDEX is False:
				raise InvalidModelException('%s Field Type %s - (%s) cannot be indexed.' %(failedValidationStr, str(thisField.__class__.__name__), repr(thisField)))

			if hasattr(IndexedRedisModel, thisField) is True:
				raise InvalidModelException('%s Field name %s is a reserved attribute on IndexedRedisModel.' %(failedValidationStr, str(thisField)))



		if mustUpdateFields is True:
			model.FIELDS = newFields
			deprecatedMessage('Model "%s" contains plain-string fields. These have been converted to IRClassicField objects to retain the same functionality. plain-string fields will be removed in a future version. The converted fields are: %s' %(model.__name__, repr(updatedFields)), 'UPDATED_FIELDS_' + model.__name__)

		model.FIELDS = KeyList(model.FIELDS)

		if bool(indexedFieldSet - fieldSet):
			raise InvalidModelException('%s All INDEXED_FIELDS must also be present in FIELDS. %s exist only in INDEXED_FIELDS' %(failedValidationStr, str(list(indexedFieldSet - fieldSet)), ) )
		
		validatedModels.add(model)
		return True

	@deprecated('IndexedRedisModel.connect is deprecated old name. Please use connectAlt instead.')
	@classmethod
	def connect(cls, redisConnectionParams):
		'''
			connect - DEPRECATED NAME - @see connectAlt
			  Create a class of this model which will use an alternate connection than the one specified by REDIS_CONNECTION_PARAMS on this model.

			@param redisConnectionParams <dict> - Dictionary of arguments to redis.Redis, same as REDIS_CONNECTION_PARAMS.

			@return - A class that can be used in all the same ways as the existing IndexedRedisModel, but that connects to a different instance.
		'''
		return cls.connectAlt(redisConnectionParams)

	@classmethod
	def connectAlt(cls, redisConnectionParams):
		'''
			connectAlt - Create a class of this model which will use an alternate connection than the one specified by REDIS_CONNECTION_PARAMS on this model.

			@param redisConnectionParams <dict> - Dictionary of arguments to redis.Redis, same as REDIS_CONNECTION_PARAMS.

			@return - A class that can be used in all the same ways as the existing IndexedRedisModel, but that connects to a different instance.

			  The fields and key will be the same here, but the connection will be different. use #copyModel if you want an independent class for the model
		'''
		if not isinstance(redisConnectionParams, dict):
			raise ValueError('redisConnectionParams must be a dictionary!')

		hashVal = hashDictOneLevel(redisConnectionParams)

		modelDictCopy = copy.deepcopy(dict(cls.__dict__))
		modelDictCopy['REDIS_CONNECTION_PARAMS'] = redisConnectionParams

		ConnectedIndexedRedisModel = type('AltConnect' + cls.__name__ + str(hashVal), cls.__bases__, modelDictCopy)

		return ConnectedIndexedRedisModel

		
class IndexedRedisHelper(object):
	'''
		IndexedRedisHelper - internal helper class which ties together all the actions
	'''


	def __init__(self, mdl):
		'''
			Internal constructor

			@param mdl - IndexedRedisModel implementer
		'''
		self.mdl = mdl
		self.keyName = self.mdl.KEY_NAME

		self.fields = self.mdl.FIELDS

		self.indexedFields = [self.fields[fieldName] for fieldName in self.mdl.INDEXED_FIELDS]
			
		self._connection = None

	def __copy__(self):
		return self.__class__(self.mdl)
	
	__deepcopy__ = __copy__

	def _get_new_connection(self):
		'''
			_get_new_connection - Get a new connection
			internal
		'''
		pool = getRedisPool(self.mdl.REDIS_CONNECTION_PARAMS)
		return redis.Redis(connection_pool=pool)

	def _get_connection(self):
		'''
			_get_connection - Maybe get a new connection, or reuse if passed in.
				Will share a connection with a model
			internal
		'''
		if self._connection is None:
			self._connection = self._get_new_connection() 
		return self._connection

	def _get_ids_key(self):
		'''
			_get_ids_key - Gets the key holding primary keys
			internal
		'''
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName + ':keys'])

	def _add_id_to_keys(self, pk, conn=None):
		'''
			_add_id_to_keys - Adds primary key to table
			internal
		'''
		if conn is None:
			conn = self._get_connection()
		conn.sadd(self._get_ids_key(), pk)
	
	def _rem_id_from_keys(self, pk, conn=None):
		'''
			_rem_id_from_keys - Remove primary key from table
			internal
		'''
		if conn is None:
			conn = self._get_connection()
		conn.srem(self._get_ids_key(), pk)

	def _add_id_to_index(self, indexedField, pk, val, conn=None):
		'''
			_add_id_to_index - Adds an id to an index
			internal
		'''
		if conn is None:
			conn = self._get_connection()
		conn.sadd(self._get_key_for_index(indexedField, val), pk)

	def _rem_id_from_index(self, indexedField, pk, val, conn=None):
		'''
			_rem_id_from_index - Removes an id from an index
			internal
		'''
		if conn is None:
			conn = self._get_connection()
		conn.srem(self._get_key_for_index(indexedField, val), pk)
		
	def _get_key_for_index(self, indexedField, val):
		'''
			_get_key_for_index - Returns the key name that would hold the indexes on a value
			Internal - does not validate that indexedFields is actually indexed. Trusts you. Don't let it down.

			@param indexedField - string of field name
			@param val - Value of field

			@return - Key name string, potentially hashed.
		'''
		# If provided an IRField, use the toIndex from that (to support compat_ methods
		if hasattr(indexedField, 'toIndex'):
			val = indexedField.toIndex(val)
		else:
		# Otherwise, look up the indexed field from the model
			val = self.fields[indexedField].toIndex(val)


		return ''.join( [INDEXED_REDIS_PREFIX, self.keyName, ':idx:', indexedField, ':', val] )

	def _compat_get_str_key_for_index(self, indexedField, val):
		'''
			_compat_get_str_key_for_index - Return the key name as a string, even if it is a hashed index field.
			  This is used in converting unhashed fields to a hashed index (called by _compat_rem_str_id_from_index which is called by compat_convertHashedIndexes)

			  @param inde
			@param indexedField - string of field name
			@param val - Value of field

			@return - Key name string, always a string regardless of hash
		'''
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':idx:', indexedField, ':', getattr(indexedField, 'toStorage', to_unicode)(val)])

	@deprecated('_compat_rem_str_id_from_index is deprecated.')
	def _compat_rem_str_id_from_index(self, indexedField, pk, val, conn=None):
		'''
			_compat_rem_str_id_from_index - Used in compat_convertHashedIndexes to remove the old string repr of a field,
				in order to later add the hashed value,
		'''
		if conn is None:
			conn = self._get_connection()
		conn.srem(self._compat_get_str_key_for_index(indexedField, val), pk)


	def _get_key_for_id(self, pk):
		'''
			_get_key_for_id - Returns the key name that holds all the data for an object
			Internal

			@param pk - primary key

			@return - Key name string
		'''
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':data:', to_unicode(pk)])

	def _get_next_id_key(self):
		'''
			_get_next_id_key - Returns the key name that holds the generator for primary key values
			Internal

			@return - Key name string
		'''
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':next'])

	def _peekNextID(self, conn=None):
		'''
			_peekNextID - Look at, but don't increment the primary key for this model.
				Internal.

			@return int - next pk
		'''
		if conn is None:
			conn = self._get_connection()
		return to_unicode(conn.get(self._get_next_id_key()) or 0)

	def _getNextID(self, conn=None):
		'''
			_getNextID - Get (and increment) the next primary key for this model.
				If you don't want to increment, @see _peekNextID .
				Internal.
				This is done automatically on save. No need to call it.

			@return int - next pk
		'''
		if conn is None:
			conn = self._get_connection()
		return int(conn.incr(self._get_next_id_key()))

	def _getTempKey(self):
		'''
			_getTempKey - Generates a temporary key for intermediate storage
		'''
		return self._get_ids_key() + '__' + uuid.uuid4().__str__()

class IndexedRedisQuery(IndexedRedisHelper):
	'''
		IndexedRedisQuery - The query object. This is the return of "Model.objects" and "Model.objects.filter*"
	'''
	
	def __init__(self, *args, **kwargs):
		IndexedRedisHelper.__init__(self, *args, **kwargs)

		self.filters = [] # Filters are ordered for optimization
		self.notFilters = []

	def __copy__(self):
		ret = self.__class__(self.mdl)
		ret.filters = self.filters[:]
		ret.notFilters = self.notFilters[:]

		return ret
	
	__deepcopy__ = __copy__


	def _redisResultToObj(self, theDict):
		if '_id' in theDict:
			theDict['_id'] = int(theDict['_id'])

		decodedDict = decodeDict(theDict)
		decodedDict['__fromRedis'] = True

		obj = self.mdl(**decodedDict)

		return obj
	

	def filter(self, **kwargs):
		'''
			filter - Add filters based on INDEXED_FIELDS having or not having a value.
			  Note, no objects are actually fetched until .all() is called

				Use the field name [ model.objects.filter(some_field='value')] to filter on items containing that value.
				Use the field name suffxed with '__ne' for a negation filter [ model.objects.filter(some_field__ne='value') ]

			Example:
				query = Model.objects.filter(field1='value', field2='othervalue')

				objs1 = query.filter(something__ne='value').all()
				objs2 = query.filter(something__ne=7).all()


			@returns - A copy of this object, with the additional filters. If you want to work inline on this object instead, use the filterInline method.
		'''
		selfCopy = self.__copy__()
		return IndexedRedisQuery._filter(selfCopy, **kwargs)

	def filterInline(self, **kwargs):
		'''
			filterInline - @see IndexedRedisQuery.filter. This is the same as filter, but works inline on this object instead of creating a copy.
				Use this is you do not need to retain the previous filter object.
		'''
		return IndexedRedisQuery._filter(self, **kwargs)

	@staticmethod
	def _filter(filterObj, **kwargs):
		'''
			Internal for handling filters; the guts of .filter and .filterInline
		'''
		for key, value in kwargs.items():
			if key.endswith('__ne'):
				notFilter = True
				key = key[:-4]
			else:
				notFilter = False
			if key not in filterObj.indexedFields:
				raise ValueError('Field "' + key + '" is not in INDEXED_FIELDS array. Filtering is only supported on indexed fields.')

			if notFilter is False:
				filterObj.filters.append( (key, value) )
			else:
				filterObj.notFilters.append( (key, value) )

		return filterObj #chaining

		

	def count(self):
		'''
			count - gets the number of records matching the filter criteria

			Example:
				theCount = Model.objects.filter(field1='value').count()
		'''
		conn = self._get_connection()
		
		numFilters = len(self.filters)
		numNotFilters = len(self.notFilters)
		if numFilters + numNotFilters == 0:
			return conn.scard(self._get_ids_key())

		if numNotFilters == 0:
			if numFilters == 1:
				(filterFieldName, filterValue) = self.filters[0]
				return conn.scard(self._get_key_for_index(filterFieldName, filterValue))
			indexKeys = [self._get_key_for_index(filterFieldName, filterValue) for filterFieldName, filterValue in self.filters]

			return len(conn.sinter(indexKeys))

		notIndexKeys = [self._get_key_for_index(filterFieldName, filterValue) for filterFieldName, filterValue in self.notFilters]
		if numFilters == 0:
			return len(conn.sdiff(self._get_ids_key(), *notIndexKeys))

		indexKeys = [self._get_key_for_index(filterFieldName, filterValue) for filterFieldName, filterValue in self.filters]
		
		tempKey = self._getTempKey()
		pipeline = conn.pipeline()
		pipeline.sinterstore(tempKey, *indexKeys)
		pipeline.sdiff(tempKey, *notIndexKeys)
		pipeline.delete(tempKey)
		pks = pipeline.execute()[1] # sdiff

		return len(pks)

	def exists(self, pk):
		'''
			exists - Tests whether a record holding the given primary key exists.

			@param pk - Primary key (see getPk method)

			Example usage: Waiting for an object to be deleted without fetching the object or running a filter. 

			This is a very cheap operation.

			@return <bool> - True if object with given pk exists, otherwise False
		'''
		conn = self._get_connection()
		key = self._get_key_for_id(pk)
		return conn.exists(key)
			

	def getPrimaryKeys(self, sortByAge=False):
		'''
			getPrimaryKeys - Returns all primary keys matching current filterset.

			@param sortByAge <bool> - If False, return will be a set and may not be ordered.
				If True, return will be a list and is guarenteed to represent objects oldest->newest

			@return <set> - A set of all primary keys associated with current filters.
		'''
		conn = self._get_connection()
		# Apply filters, and return object
		numFilters = len(self.filters)
		numNotFilters = len(self.notFilters)

		if numFilters + numNotFilters == 0:
			# No filters, get all.
			conn = self._get_connection()
			matchedKeys = conn.smembers(self._get_ids_key())

		elif numNotFilters == 0:
			# Only Inclusive
			if numFilters == 1:
				# Only one filter, get members of that index key
				(filterFieldName, filterValue) = self.filters[0]
				matchedKeys = conn.smembers(self._get_key_for_index(filterFieldName, filterValue))
			else:
				# Several filters, intersect the index keys
				indexKeys = [self._get_key_for_index(filterFieldName, filterValue) for filterFieldName, filterValue in self.filters]
				matchedKeys = conn.sinter(indexKeys)

		else:
			# Some negative filters present
			notIndexKeys = [self._get_key_for_index(filterFieldName, filterValue) for filterFieldName, filterValue in self.notFilters]
			if numFilters == 0:
				# Only negative, diff against all keys
				matchedKeys = conn.sdiff(self._get_ids_key(), *notIndexKeys)
			else:
				# Negative and positive. Use pipeline, find all positive intersections, and remove negative matches
				indexKeys = [self._get_key_for_index(filterFieldName, filterValue) for filterFieldName, filterValue in self.filters]
				
				tempKey = self._getTempKey()
				pipeline = conn.pipeline()
				pipeline.sinterstore(tempKey, *indexKeys)
				pipeline.sdiff(tempKey, *notIndexKeys)
				pipeline.delete(tempKey)
				matchedKeys = pipeline.execute()[1] # sdiff

		if sortByAge is False:
			return list(matchedKeys)
		else:
			matchedKeys = list(matchedKeys)
			matchedKeys.sort()

			return matchedKeys


	def all(self):
		'''
			all - Get the underlying objects which match the filter criteria.

			Example:   objs = Model.objects.filter(field1='value', field2='value2').all()

			@return - Objects of the Model instance associated with this query.
		'''
		matchedKeys = self.getPrimaryKeys()
		if matchedKeys:
			return self.getMultiple(matchedKeys)

		return IRQueryableList([], mdl=self.mdl)

	def allByAge(self):
		'''
			allByAge - Get the underlying objects which match the filter criteria, ordered oldest -> newest
				If you are doing a queue or just need the head/tail, consider .first() and .last() instead.

			@return - Objects of the Model instance associated with this query, sorted oldest->newest
		'''
		matchedKeys = self.getPrimaryKeys(sortByAge=True)
		if matchedKeys:
			return self.getMultiple(matchedKeys)

		return IRQueryableList([], mdl=self.mdl)

	def allOnlyFields(self, fields):
		'''
			allOnlyFields - Get the objects which match the filter criteria, only fetching given fields.

			@param fields - List of fields to fetch

			@return - Partial objects with only the given fields fetched
		'''
		matchedKeys = self.getPrimaryKeys()
		if matchedKeys:
			return self.getMultipleOnlyFields(matchedKeys, fields)

		return IRQueryableList([], mdl=self.mdl)

	def allOnlyIndexedFields(self):
		'''
			allOnlyIndexedFields - Get the objects which match the filter criteria, only fetching indexed fields.

			@return - Partial objects with only the indexed fields fetched
		'''
		matchedKeys = self.getPrimaryKeys()
		if matchedKeys:
			return self.getMultipleOnlyIndexedFields(matchedKeys)

		return IRQueryableList([], mdl=self.mdl)
		
	
	def first(self):
		'''
			First - Returns the oldest record (lowerst primary key) with current filters.
				This makes an efficient queue, as it only fetches a single object.
		
			@return - Instance of Model object, or None if no items match current filters
		'''
		obj = None

		matchedKeys = self.getPrimaryKeys(sortByAge=True)
		if matchedKeys:
			# Loop so we don't return None when there are items, if item is deleted between getting key and getting obj
			while matchedKeys and obj is None:
				obj = self.get(matchedKeys.pop(0))

		return obj

	def last(self):
		'''
			Last - Returns the newest record (highest primary key) with current filters.
				This makes an efficient queue, as it only fetches a single object.
		
			@return - Instance of Model object, or None if no items match current filters
		'''
		obj = None

		matchedKeys = self.getPrimaryKeys(sortByAge=True)
		if matchedKeys:
			# Loop so we don't return None when there are items, if item is deleted between getting key and getting obj
			while matchedKeys and obj is None:
				obj = self.get(matchedKeys.pop())

		return obj

	def random(self):
		'''
			Random - Returns a random record in current filterset.

			@return - Instance of Model object, or None if no items math current filters
		'''
		matchedKeys = list(self.getPrimaryKeys())
		obj = None
		# Loop so we don't return None when there are items, if item is deleted between getting key and getting obj
		while matchedKeys and not obj:
			key = matchedKeys.pop(random.randint(0, len(matchedKeys)-1))
			obj = self.get(key)

		return obj
		
	
	def delete(self):
		'''
			delete - Deletes all entries matching the filter criteria

		'''
		if self.filters or self.notFilters:
			return self.mdl.deleter.deleteMultiple(self.allOnlyIndexedFields())
		return self.mdl.deleter.destroyModel()

	def get(self, pk):
		'''
			get - Get a single value with the internal primary key.

			@param pk - internal primary key (can be found via .getPk() on an item)
		'''
		conn = self._get_connection()
		key = self._get_key_for_id(pk)
		res = conn.hgetall(key)
		if type(res) != dict or not len(res.keys()):
			return None
		res['_id'] = pk
		return self._redisResultToObj(res)
	
	def getMultiple(self, pks):
		'''
			getMultiple - Gets multiple objects with a single atomic operation

			@param pks - list of internal keys
		'''

		if type(pks) == set:
			pks = list(pks)

		if len(pks) == 1:
			# Optimization to not pipeline on 1 id
			return IRQueryableList([self.get(pks[0])], mdl=self.mdl)

		conn = self._get_connection()
		pipeline = conn.pipeline()
		for pk in pks:
			key = self._get_key_for_id(pk)
			pipeline.hgetall(key)

		res = pipeline.execute()
		
		ret = IRQueryableList(mdl=self.mdl)
		i = 0
		pksLen = len(pks)
		while i < pksLen:
			if res[i] is None:
				ret.append(None)
				i += 1
				continue
			res[i]['_id'] = pks[i]
			obj = self._redisResultToObj(res[i])
			ret.append(obj)
			i += 1
			
		return ret

	def getOnlyFields(self, pk, fields):
		'''
			getOnlyFields - Gets only certain fields from a paticular primary key. For working on entire filter set, see allOnlyFields

			pk - Primary Key
			fields list<str> - List of fields

			return - Partial objects with only fields applied
		'''
		conn = self._get_connection()
		key = self._get_key_for_id(pk)

		res = conn.hmget(key, fields)
		if type(res) != list or not len(res):
			return None

		objDict = {}
		numFields = len(fields)
		i = 0
		anyNotNone = False
		while i < numFields:
			objDict[fields[i]] = res[i]
			if res[i] != None:
				anyNotNone = True
			i += 1

		if anyNotNone is False:
			return None
			
		objDict['_id'] = pk
		return self._redisResultToObj(objDict)

	def getMultipleOnlyFields(self, pks, fields):
		'''
			getMultipleOnlyFields - Gets only certain fields from a list of  primary keys. For working on entire filter set, see allOnlyFields

			pks list<str> - Primary Keys
			fields list<str> - List of fields

			return - List of partial objects with only fields applied
		'''
		if type(pks) == set:
			pks = list(pks)

		if len(pks) == 1:
			return IRQueryableList([self.getOnlyFields(pks[0], fields)], mdl=self.mdl)
		conn = self._get_connection()
		pipeline = conn.pipeline()

		for pk in pks:
			key = self._get_key_for_id(pk)
			pipeline.hmget(key, fields)

		res = pipeline.execute()
		ret = IRQueryableList(mdl=self.mdl)
		pksLen = len(pks)
		i = 0
		numFields = len(fields)
		while i < pksLen:
			objDict = {}
			anyNotNone = False
			thisRes = res[i]
			if thisRes is None or type(thisRes) != list:
				ret.append(None)
				i += 1
				continue

			j = 0
			while j < numFields:
				objDict[fields[j]] = thisRes[j]
				if thisRes[j] != None:
					anyNotNone = True
				j += 1

			if anyNotNone is False:
				ret.append(None)
				i += 1
				continue

			objDict['_id'] = pks[i]
			obj = self._redisResultToObj(objDict)
			ret.append(obj)
			i += 1
			
		return ret

	def getOnlyIndexedFields(self, pk):
		'''
			getOnlyIndexedFields - Get only the indexed fields on an object. This is the minimum to delete.

			@param pk - Primary key

			@return - Object with only indexed fields fetched.
		'''
		return self.getOnlyFields(pk, self.indexedFields)
	
	def getMultipleOnlyIndexedFields(self, pks):
		'''
			getMultipleOnlyIndexedFields - Get only the indexed fields on an object. This is the minimum to delete.

			@param pks - List of primary keys

			@return - List of objects with only indexed fields fetched
		'''
		return self.getMultipleOnlyFields(pks, self.indexedFields)


	def reindex(self):
		'''
			reindex - Reindexes the objects matching current filterset. Use this if you add/remove a field to INDEXED_FIELDS.

			  NOTE - This will NOT remove entries from the old index if you change index type, or change decimalPlaces on a
			    IRFixedPointField.  To correct these indexes, you'll need to run:

			       Model.reset(Model.objects.all())

			If you change the value of "hashIndex" on a field, you need to call #compat_convertHashedIndexes instead.
		'''
		objs = self.all()
		saver = IndexedRedisSave(self.mdl)
		saver.reindex(objs)

	def compat_convertHashedIndexes(self, fetchAll=True):
		'''
			compat_convertHashedIndexes - Reindex fields, used for when you change the propery "hashIndex" on one or more fields.

			For each field, this will delete both the hash and unhashed keys to an object, 
			  and then save a hashed or unhashed value, depending on that field's value for "hashIndex".

			For an IndexedRedisModel class named "MyModel", call as "MyModel.objects.compat_convertHashedIndexes()"

			NOTE: This works one object at a time (regardless of #fetchAll), so that an unhashable object does not trash all data.

			This method is intended to be used while your application is offline,
			  as it doesn't make sense to be changing your model while applications are actively using it.

			@param fetchAll <bool>, Default True - If True, all objects will be fetched first, then converted.
			  This is generally what you want to do, as it is more efficient. If you are memory contrainted,
			  you can set this to "False", and it will fetch one object at a time, convert it, and save it back.

		'''

		saver = IndexedRedisSave(self.mdl)

		if fetchAll is True:
			objs = self.all()
			saver.compat_convertHashedIndexes(objs)
		else:
			didWarnOnce = False

			pks = self.getPrimaryKeys()
			for pk in pks:
				obj = self.get(pk)
				if not obj:
					if didWarnOnce is False:
						sys.stderr.write('WARNING(once)! An object (type=%s , pk=%d) disappered while '  \
							'running compat_convertHashedIndexes! This probably means an application '  \
							'is using the model while converting indexes. This is a very BAD IDEA (tm).')
						
						didWarnOnce = True
					continue
				saver.compat_convertHashedIndexes([obj])



class IndexedRedisSave(IndexedRedisHelper):
	'''
		IndexedRedisSave - Class used to save objects. Used with Model.save is called.
			Except for advanced usage, this is probably for internal only.
	'''

	def save(self, obj, usePipeline=True, forceID=False, conn=None):
		'''
			save - Save an object / objects associated with this model. 
			
			You probably want to just do object.save() instead of this, but to save multiple objects at once in a single transaction, 
			   you can use:
				
				MyModel.saver.save(myObjs)

			@param obj <IndexedRedisModel or list<IndexedRedisModel> - The object to save, or a list of objects to save
			@param usePipeline - Use a pipeline for saving. You should always want this, unless you are calling this function from within an existing pipeline.
			@param forceID - if not False, force ID to this. If obj is list, this is also list. Forcing IDs also forces insert. Up to you to ensure ID will not clash.
			@param conn - A connection or None

			@note - if no ID is specified

			@return - List of pks
		'''
		if conn is None:
			conn = self._get_connection()

		# If we are in a pipeline, we need an external connection to fetch any potential IDs for inserts.
		if usePipeline is True:
			idConn = conn
		else:
			idConn = self._get_new_connection()

		if issubclass(obj.__class__, (list, tuple)):
			objs = obj
		else:
			objs = [obj]

		objsLen = len(objs)

		if forceID is not False:
			# Compat with old poor design.. :(
			if isinstance(forceID, (list, tuple)):
				forceIDs = forceID
			else:
				forceIDs = [forceID]
			isInserts = [] 
			i = 0
			while i < objsLen:
				if forceIDs[i] is not False:
					objs[i]._id = forceIDs[i]
					isInserts.append(True)
				else:
					isInsert = not bool(getattr(obj, '_id', None))
					if isInsert is True:
						objs[i]._id = self._getNextID(idConn)
					isInserts.append(isInsert)
				i += 1
		else:
			isInserts = []
			for obj in objs:
				isInsert = not bool(getattr(obj, '_id', None))
				if isInsert is True:
					obj._id = self._getNextID(idConn)
				isInserts.append(isInsert)
				

		if usePipeline is True:
			pipeline = conn.pipeline()
		else:
			pipeline = conn

		ids = [] # Note ids can be derived with all information above..
		i = 0
		while i < objsLen:
			self._doSave(objs[i], isInserts[i], conn, pipeline)
			ids.append(objs[i]._id)
			i += 1

		if usePipeline is True:
			pipeline.execute()

		return ids

	def saveMultiple(self, objs):
		'''
			saveMultiple - Save a list of objects using a pipeline.

			@param objs < list<IndexedRedisModel> > - List of objects to save
		'''
		# Right now this can be done with existing save function, but I think that is not clear.
		return self.save(objs)
		

	def _doSave(self, obj, isInsert, conn, pipeline=None):
		'''
			_doSave - Internal function to save a single object. Don't call this directly. 
			            Use "save" instead.

			  If a pipeline is provided, the operations (setting values, updating indexes, etc)
			    will be queued into that pipeline.
			  Otherwise, everything will be executed right away.

			  @param obj - Object to save
			  @param isInsert - Bool, if insert or update. Either way, obj._id is expected to be set.
			  @param conn - Redis connection
			  @param pipeline - Optional pipeline, if present the items will be queued onto it. Otherwise, go directly to conn.
		'''

		if pipeline is None:
			pipeline = conn

		newDict = obj.asDict(forStorage=True)
		key = self._get_key_for_id(obj._id)

		if isInsert is True:
			for thisField in self.fields:

				fieldValue = newDict.get(thisField, thisField.getDefaultValue())

				pipeline.hset(key, thisField, fieldValue)

				# Update origData with the new data
				if fieldValue == IR_NULL_STR:
					obj._origData[thisField] = irNull
				else:
					obj._origData[thisField] = getattr(obj, str(thisField))

			self._add_id_to_keys(obj._id, pipeline)

			for indexedField in self.indexedFields:
				self._add_id_to_index(indexedField, obj._id, obj._origData[indexedField], pipeline)
		else:
			updatedFields = obj.getUpdatedFields()
			for thisField, fieldValue in updatedFields.items():
				(oldValue, newValue) = fieldValue

				oldValueForStorage = thisField.toStorage(oldValue)
				newValueForStorage = thisField.toStorage(newValue)

				pipeline.hset(key, thisField, newValueForStorage)

				if thisField in self.indexedFields:
					self._rem_id_from_index(thisField, obj._id, oldValueForStorage, pipeline)
					self._add_id_to_index(thisField, obj._id, newValueForStorage, pipeline)

				# Update origData with the new data
				obj._origData[thisField] = newValue


	def reindex(self, objs, conn=None):
		'''
			reindex - Reindexes a given list of objects. Probably you want to do Model.objects.reindex() instead of this directly.

			@param objs list<IndexedRedisModel> - List of objects to reindex
			@param conn <redis.Redis or None> - Specific Redis connection or None to reuse
		'''
		if conn is None:
			conn = self._get_connection()

		pipeline = conn.pipeline()

		objDicts = [obj.asDict(True, forStorage=True) for obj in objs]

		for indexedFieldName in self.indexedFields:
			for objDict in objDicts:
				self._rem_id_from_index(indexedFieldName, objDict['_id'], objDict[indexedFieldName], pipeline)
				self._add_id_to_index(indexedFieldName, objDict['_id'], objDict[indexedFieldName], pipeline)

		pipeline.execute()

	def compat_convertHashedIndexes(self, objs, conn=None):
		'''
			compat_convertHashedIndexes - Reindex all fields for the provided objects, where the field value is hashed or not.
			If the field is unhashable, do not allow.

			NOTE: This works one object at a time. It is intended to be used while your application is offline,
			  as it doesn't make sense to be changing your model while applications are actively using it.

			@param objs <IndexedRedisModel objects to convert>
			@param conn <redis.Redis or None> - Specific Redis connection or None to reuse.
		'''
		if conn is None:
			conn = self._get_connection()



		# Do one pipeline per object.
		#  XXX: Maybe we should do the whole thing in one pipeline? 

		fields = []        # A list of the indexed fields

		# Iterate now so we do this once instead of per-object.
		for indexedField in self.indexedFields:

			origField = self.fields[indexedField]

			# Check if type supports configurable hashIndex, and if not skip it.
			if 'hashIndex' not in origField.__class__.__new__.__code__.co_varnames:
				continue

			if indexedField.hashIndex is True:
				hashingField = origField

				regField = origField.copy()
				regField.hashIndex = False
			else:
				regField = origField
				# Maybe copy should allow a dict of override params?
				hashingField = origField.copy()
				hashingField.hashIndex = True


			fields.append ( (origField, regField, hashingField) )

		objDicts = [obj.asDict(True, forStorage=True) for obj in objs]

		# Iterate over all values. Remove the possibly stringed index, the possibly hashed index, and then put forth the hashed index.

		for objDict in objDicts:
			pipeline = conn.pipeline()
			pk = objDict['_id']
			for origField, regField, hashingField in fields:
				val = objDict[indexedField]

				# Remove the possibly stringed index
				self._rem_id_from_index(regField, pk, val, pipeline)
				# Remove the possibly hashed index
				self._rem_id_from_index(hashingField, pk, val, pipeline)
				# Add the new (hashed or unhashed) form.
				self._add_id_to_index(origField, pk, val, pipeline)

			# Launch all at once
			pipeline.execute()



class IndexedRedisDelete(IndexedRedisHelper):
	'''
		IndexedRedisDelete - Used for removing objects. Called when Model.delete is used.
			Except for advanced usage, this is probably for internal only.
	'''

	def deleteOne(self, obj, conn=None):
		'''
			deleteOne - Delete one object

			@param obj - object to delete
			@param conn - Connection to reuse, or None

			@return - number of items deleted (0 or 1)
		'''
		if not getattr(obj, '_id', None):
			return 0

		if conn is None:
			conn = self._get_connection()
			pipeline = conn.pipeline()
			executeAfter = True
		else:
			pipeline = conn # In this case, we are inheriting a pipeline
			executeAfter = False
		
		pipeline.delete(self._get_key_for_id(obj._id))
		self._rem_id_from_keys(obj._id, pipeline)
		for indexedFieldName in self.indexedFields:
			self._rem_id_from_index(indexedFieldName, obj._id, obj._origData[indexedFieldName], pipeline)

		obj._id = None

		if executeAfter is True:
			pipeline.execute()

		return 1

	def deleteByPk(self, pk):
		'''
			deleteByPk - Delete object associated with given primary key
		'''
		obj = self.mdl.objects.getOnlyIndexedFields(pk)
		if not obj:
			return 0
		return self.deleteOne(obj)

	def deleteMultiple(self, objs):
		'''
			deleteMultiple - Delete multiple objects

			@param objs - List of objects

			@return - Number of objects deleted
		'''
		conn = self._get_connection()
		pipeline = conn.pipeline()

		numDeleted = 0

		for obj in objs:
			numDeleted += self.deleteOne(obj, pipeline)

		pipeline.execute()

		return numDeleted

	def deleteMultipleByPks(self, pks):
		'''
			deleteMultipleByPks - Delete multiple objects given their primary keys

			@param pks - List of primary keys

			@return - Number of objects deleted
		'''
		if type(pks) == set:
			pks = list(pks)

		if len(pks) == 1:
			return self.deleteByPk(pks[0])

		objs = self.mdl.objects.getMultipleOnlyIndexedFields(pks)
		return self.deleteMultiple(objs)

	def destroyModel(self):
		'''
			destroyModel - Destroy everything related to this model in one swoop.

			    Same effect as Model.reset([]) - Except slightly more efficient.

			    This function is called if you do Model.objects.delete() with no filters set.

			@return - Number of keys deleted. Note, this is NOT number of models deleted, but total keys.
		'''
		conn = self._get_connection()
		pipeline = conn.pipeline()
		pipeline.eval("""
		local matchingKeys = redis.call('KEYS', '%s*')

		for _,key in ipairs(matchingKeys) do
			redis.call('DEL', key)
		end

		return #matchingKeys
		""" %( ''.join([INDEXED_REDIS_PREFIX, self.mdl.KEY_NAME, ':']), ), 0)
		return pipeline.execute()[0]
		
	

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
