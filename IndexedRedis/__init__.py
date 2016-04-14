# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#  IndexedRedis A redis-backed very very fast ORM-style framework that supports indexes, and searches with O(1) efficency.
#    It has syntax similar to Django and Flask and other ORMs, but is itself unique in many ways.



# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

import copy
import codecs
import random
import sys
import uuid
import redis

from base64 import b64encode, b64decode

from .fields import IRField, IRNullType, irNull, IRPickleField, IRCompressedField
from .compat_str import tostr, tobytes, defaultEncoding

from QueryableList import QueryableListObjs

# * imports
__all__ = ('INDEXED_REDIS_PREFIX', 'INDEXED_REDIS_VERSION', 'INDEXED_REDIS_VERSION_STR', 
	'IndexedRedisDelete', 'IndexedRedisHelper', 'IndexedRedisModel', 'IndexedRedisQuery', 'IndexedRedisSave',
	'isIndexedRedisModel', 'setIndexedRedisEncoding', 'getIndexedRedisEncoding', 'InvalidModelException',
	'IRField', 'IRPickleField', 'IRCompressedField', 'IRNullType', 'irNull'
	 )

# Prefix that all IndexedRedis keys will contain, as to not conflict with other stuff.
INDEXED_REDIS_PREFIX = '_ir_|'

# Version as a tuple (major, minor, patchlevel)
INDEXED_REDIS_VERSION = (4, 0, 0)

# Version as a string
INDEXED_REDIS_VERSION_STR = '4.0.0'

# Package version
__version__ = INDEXED_REDIS_VERSION_STR


# COMPAT STUFF
try:
	classproperty
except NameError:
	class classproperty(object):
		def __init__(self, getter):
			self.getter = getter
		def __get__(self, instance, owner):
			return self.getter(owner)



# TODO: make this better
try:
	unicode
except NameError:
	unicode = str


# Changing redis encoding into requested encoding
decodeDict = lambda origDict : {tostr(key) : tostr(origDict[key]) for key in origDict}

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


            **Required Fields:**

            *FIELDS* - REQUIRED. a list of strings which name the fields that can be used for storage.

                    Example: ['Name', 'Description', 'Model', 'Price']


            *INDEXED_FIELDS* -  a list of strings containing the names of fields that will be indexed. Can only filter on indexed fields. Adds insert/delete time. Contents must also be in FIELDS.

                    Example: ['Name', 'Model']

            *BASE64_FIELDS* - A list of strings which name the fields that will be stored as base64-encoded strings. All entries must also be present in FIELDS.

                    Example: ['data', 'blob']

	    *BINARY_FIELDS* - A list of strings which name the fields that will be stored as unencoded binary data. All entries must also be present in FIELDS. 


            *KEY_NAME* - REQUIRED. A unique name name that represents this model. Think of it like a table name. 

                    Example: 'Items'

            *REDIS_CONNECTION_PARAMS* - provides the arguments to pass into "redis.Redis", to construct a redis object.

            Usage
            -----

            Usage is very similar to Django or Flask.

            **Query:**

            Calling .filter or .filterInline builds a query/filter set. Use one of the *Fetch* methods described below to execute a query.

                   objects = SomeModel.objects.filter(param1=val).filter(param2=val).all()

            **Save:**

                   obj = SomeModel(field1='value', field2='value')
                   obj.save()

            **Delete Using Filters:**

                   SomeModel.objects.filter(name='Bad Man').delete()

            **Delete Individual Objects:**

                   obj.delete()

            **Atomic Dataset Replacement:**

            There is also a powerful method called "reset" which will **atomically** replace all elements belonging to a model. This is useful for cache-replacement, etc.

                   lst = [SomeModel(...), SomeModel(..)]

                   SomeModel.reset(lst)

            For example, you could have a SQL backend and a cron job that does complex queries (or just fetches the same models) and does an atomic replace every 5 minutes to get massive performance boosts in your application.


            Filter objects by SomeModel.objects.filter(key=val, key2=val2) and get objects with .all

            Example: SomeModel.objects.filter(name='Tim', colour='purple').filter(number=5).all()


            **Fetch Functions**:

            Building filtersets do not actually fetch any data until one of these are called (see API for a complete list). All of these functions act on current filterset.

            Example: matchingObjects = SomeModel.objects.filter(...).all()

                   all    - Return all objects matching this filter

                   allOnlyFields - Takes a list of fields and only fetches those fields, using current filterset

                   delete - Delete objects matching this filter

                   count  - Get the count of objects matching this filter

                   first  - Get the oldest record with current filters

                   last   - Get the newest record with current filters

                   random - Get a random element with current filters

                   getPrimaryKeys - Gets primary keys associated with current filters


            **Filter Functions**

            These functions add filters to the current set. "filter" returns a copy, "filterInline" acts on that object.

                   filter - Add additional filters, returning a copy of the filter object (moreFiltered = filtered.filter(key2=val2))

                   filterInline - Add additional filters to current filter object. 


            **Global Fetch functions**

            These functions are available on SomeModel.objects and don't use any filters (they get specific objects):

                   get - Get a single object by pk

                   getMultiple - Get multiple objects by a list of pks


            **Model Functions**

            Actual objects contain methods including:

                   save   - Save this object (create if not exist, otherwise update)

                   delete - Delete this object

                   getUpdatedFields - See changes since last fetch


            Advanced Fields
	    ---------------

	    IndexedRedis since version 4.0 allows you to pass elements of type IRField (extends str) in the FIELDS element.

	    Doing so allows you to specify certain properties about the field.


	    Example:

		FIELDS = [ 'name', IRField('age', valueType=int), 'birthday' ]

	   **Field Name**

	   The first argument is the string of the field name.

	    **Type**

	    You can have a value automatically cast to a certain type (which saves a step if you need to filter further through the QueryableList results, like age__gt=15)

	    by passing that type as "valueType". (e.x.  IRField('age', valueType=int))

	    If you use "bool", the values 0 and case insensitive string 'false' will result in False, and 1 or 'true' will result in True.

	    Be careful using floats, different hosts will have different floating point representations for the same value. Don't expect

	    floats to work cross-platform. Use a fixed point number as the string type ( like myFixedPoint = '%2.5f' %( 10.12345 ) )

	    ** Null Values **

            For any type except strings (including the default type, string), a null value is assigned irNull (of type IRNullType).

	    irNull does not equal empty string, or anything except another irNull. This is to destinguish say, no int assigned vs int(0)

	    You can check a typed field against the "irNull" variable found in the IndexedRedis or IndexedRedis.fields.

	    from IndexedRedis import irNull
	    ..
	    e.x. notDangerFive = myResults.filter(dangerLevel__ne=irNull).filter(dangerLevel__ne=5)

	    or even

	    notDangerFive = MyModel.objects.filter(dangerLevel__ne=irNull).filter(dangerLevel__ne=5).all()


            Encodings
            ---------

            IndexedRedis will use by default your system default encoding (sys.getdefaultencoding), unless it is ascii (python2) in which case it will default to utf-8.

            You may change this via IndexedRedis.setEncoding

	'''
	
	# FIELDS - A list of field names, as strings.
	FIELDS = []

	# INDEXED_FIELDS - A list of field names that will be indexed, as strings. Must also be present in FIELDS.
	#  You can only search on indexed fields, but they add time to insertion/deletion
	INDEXED_FIELDS = []

	# BASE64 FIELDS - Fields in this list (must also be present in FIELDS) are encoded into base64 before sending and decoded upon retriving.
	BASE64_FIELDS = []

	# BINARY_FIELDS - Fields that are not encoded in any way
	BINARY_FIELDS = []
	
	# KEY_NAME - A string of a unique name which corrosponds to objects of this type.
	KEY_NAME = None

	# REDIS_CONNECTION_PARAMS - A dictionary of parameters to redis.Redis such as host or port. Will be used on all connections.
	REDIS_CONNECTION_PARAMS = {}

	# Internal property to check inheritance
	_is_ir_model = True

	def __init__(self, *args, **kwargs):
		'''
			__init__ - Set the values on this object. MAKE SURE YOU CALL THE SUPER HERE, or else things will not work.
		'''
		self.validateModel()

		self._origData = {}

		# Convert all field arrays to sets
		self.FIELDS = set(self.FIELDS)
		self.BASE64_FIELDS = set(self.BASE64_FIELDS)
		self.BINARY_FIELDS = set(self.BINARY_FIELDS)

		for fieldName in self.FIELDS:
			if fieldName in self.BASE64_FIELDS or fieldName in self.BINARY_FIELDS:
				val = tobytes(kwargs.get(fieldName, b''))
			elif not issubclass(fieldName.__class__, IRField):
				val = tostr(kwargs.get(fieldName, ''))
			else:
				val = fieldName.convert(kwargs.get(fieldName, ''))
			setattr(self, fieldName, val)
			self._origData[fieldName] = val

		self._convertFieldValues()

		self._id = kwargs.get('_id', None)
	
	def asDict(self, includeMeta=False, convertValueTypes=True):
		'''
			toDict / asDict - Get a dictionary representation of this model.

			@param includeMeta - Include metadata in return. For now, this is only pk stored as "_id"
			@param convertValueTypes <bool> - default True. If False, fields with fieldValue defined will be converted to that type.
				Use True when saving, etc, as native type is always either str or bytes.

			@return - Dictionary reprensetation of this object and all fields
		'''
		ret = {}
		for fieldName in self.FIELDS:
			val = getattr(self, fieldName, '')
			if fieldName in self.BASE64_FIELDS or fieldName in self.BINARY_FIELDS:
				ret[fieldName] = tobytes(val)
			else:
				ret[fieldName] = getattr(fieldName, 'toStorage', tostr)(val)
			if convertValueTypes is True and issubclass(fieldName.__class__, IRField) and fieldName.valueType:
				ret[fieldName] = type(val)(fieldName.convert(ret[fieldName]))

		if includeMeta is True:
			ret['_id'] = getattr(self, '_id', '')
		return ret

	toDict = asDict

	def hasUnsavedChanges(self):
		'''
			hasUnsavedChanges - Check if any unsaved changes are present in this model, or if it has never been saved.

			@return <bool> - True if any fields have changed since last fetch, or if never saved. Otherwise, False
		'''
		if not self._id or not self._origData:
			return True

		for fieldName in self.FIELDS:
			if fieldName in self.BASE64_FIELDS or fieldName in self.BINARY_FIELDS:
				currentVal = tobytes(getattr(self, fieldName))
			else:
				currentVal = getattr(fieldName, 'toStorage', tostr)(getattr(self, fieldName))

			if self._origData.get(fieldName, '') != currentVal:
				return True
		return False
	
	def getUpdatedFields(self):
		'''
			getUpdatedFields - See changed fields.
			
			@return - a dictionary of fieldName : tuple(old, new)
		'''
		updatedFields = {}
		for fieldName in self.FIELDS:
			if fieldName in self.BASE64_FIELDS or fieldName in self.BINARY_FIELDS:
				thisVal = tobytes(getattr(self, fieldName))
			else:
				thisVal = getattr(fieldName, 'toStorage', tostr)(getattr(self, fieldName))
			if self._origData[fieldName] != thisVal:
				updatedFields[fieldName] = (self._origData[fieldName], thisVal)
		return updatedFields

	@classproperty
	def objects(cls):
		'''
			objects - Start filtering
		'''
		return IndexedRedisQuery(cls)

	@classproperty
	def saver(cls):
		return IndexedRedisSave(cls)

	@classproperty
	def deleter(cls):
		'''
			deleter - Get access to IndexedRedisDelete for this model.
			@see IndexedRedisDelete.
			Usually you'll probably just do Model.objects.filter(...).delete()
		'''
		return IndexedRedisDelete(cls)

	def save(self):
		'''
			save - Save this object
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
	def reset(cls, newValues):
		conn = redis.Redis(**cls.REDIS_CONNECTION_PARAMS)

		transaction = conn.pipeline()
		transaction.eval("""
		local matchingKeys = redis.call('KEYS', '%s*')

		for _,key in ipairs(matchingKeys) do
			redis.call('DEL', key)
		end
		""" %( ''.join([INDEXED_REDIS_PREFIX, cls.KEY_NAME, ':']), ), 0)
		saver = IndexedRedisSave(cls)
		nextID = 1
		for newValue in newValues:
			saver.save(newValue, False, nextID, transaction)
			nextID += 1
		transaction.set(saver._get_next_id_key(), nextID)
		transaction.execute()

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
		myDict = self.asDict(True)
		_id = myDict.pop('_id', 'None')
		myPointerLoc = "0x%x" %(id(self),)
		if not _id or _id == 'None':
			return '<%s obj (Not in DB) at %s>' %(myClassName, myPointerLoc)
		elif self.hasUnsavedChanges():
			return '<%s obj _id=%s (Unsaved Changes) at %s>' %(myClassName, tostr(_id), myPointerLoc)
		return '<%s obj _id=%s at %s>' %(myClassName, tostr(_id), myPointerLoc)

	def __repr__(self):
		'''
                    __repr__ - Returns a string of the constructor/params to recreate this object.
                        Example: objCopy = eval(repr(obj))

                        @return - String of python init call to recreate this object
		'''
		myDict = self.asDict(True)
		myClassName = self.__class__.__name__

		ret = [myClassName, '(']
		# Only show id if saved
		_id = myDict.pop('_id', '')
		if _id:
			ret += ['_id="', tostr(_id), '", ']

		# TODO: Note, trying to fit the type in here, but it's not perfect and may need to change when nullables are figured out
		convertMethods = { fieldName : (hasattr(fieldName, 'convert') and fieldName.convert or (lambda x : x)) for fieldName in self.FIELDS}

		key = None
		for key, value in myDict.items():
			if key not in self.BINARY_FIELDS:
				if value != None:
					val = convertMethods[key](value)
				if isinstance(val, IRNullType):
					val = 'IRNullType()'
				elif isinstance(val, (str, bytes, unicode)):
					val = "'%s'" %(tostr(val),)
				else:
					val = tostr(val)
				ret += [key, '=', val, ', ']
			else:
				ret += [key, '=', repr(value), ', ']
		if key is not None or not _id:
			# At least one iteration, so strip trailing comma
			ret.pop()
		ret.append(')')

		return ''.join(ret)


	def copy(self, copyPrimaryKey=False):
		'''
                    copy - Copies this object.

                    @param copyPrimaryKey <bool> default False - If True, any changes to the copy will save over-top the existing entry in Redis.
                        If False, only the data is copied, and nothing is saved.
		'''
		return self.__class__(**self.asDict(copyPrimaryKey, convertValueTypes=False))

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
                reload - Reload this object from the database.

                    @raises KeyError - if this object has not been saved (no primary key)

                    @return - True if any updates occured, False if data remained the same.
		'''
		_id = self._id
		if not _id:
			raise KeyError('Object has never been saved! Cannot reload.')

		currentData = self.asDict(False, convertValueTypes=False)
		newData = self.objects.get(_id)
		newData.pop('_id', '')
		if currentData == newData:
			return []

		updatedFieldNames = []
		for fieldName, value in newData.items():
			if currentData[fieldName] != value:
				setattr(self, fieldName, value)
				updatedFieldNames.append(fieldName)

		return updatedFieldNames
                    

	def __getstate__(self):
		'''
                pickle uses this
		'''
		return self.asDict(True, convertValueTypes=False)

	def __setstate__(self, stateDict):
		'''
                pickle uses this
		'''
		for key, value in stateDict.items():
			setattr(self, key, value)


	def _decodeBase64Fields(self):
		'''
			_decodeBase64Fields - private method, do not call . Used for decoding base64 fields after fetch
		'''
		for fieldName in self.__class__.BASE64_FIELDS:
			fieldValue = b64decode(getattr(self, fieldName))
			setattr(self, fieldName, fieldValue)


	def _convertFieldValues(self):
		for field in self.FIELDS:
			if issubclass(field.__class__, IRField):
				setattr(self, field, field.convert(getattr(self, field)))


	@classmethod
	def validateModel(model):
		'''
			validateModel - Class method that validates a given model is implemented correctly. Will only be validated once, on first model instantiation.

			@param model - Implicit of own class

			@return - True

			@raises - InvalidModelException if there is a problem with the model, and the message contains relevant information.
		'''
		global validatedModels
		keyName = model.KEY_NAME
		if not keyName:
			raise InvalidModelException('"%s" has no KEY_NAME defined.' %(str(model.__name__), ) )
		if keyName in validatedModels:
			return True

		failedValidationStr = '"%s" Failed Model Validation:' %(str(model.__name__), ) 
		
		fieldSet = set(model.FIELDS)
		indexedFieldSet = set(model.INDEXED_FIELDS)
		base64FieldSet = set(model.BASE64_FIELDS)
		binaryFieldSet = set(model.BINARY_FIELDS)

		if not fieldSet:
			raise InvalidModelException('%s No fields defined. Please populate the FIELDS array with a list of field names' %(failedValidationStr,))

		for fieldName in fieldSet:
			if fieldName == '_id':
				raise InvalidModelException('%s You cannot have a field named _id, it is reserved for the primary key.' %(failedValidationStr,))
			try:
				codecs.ascii_encode(fieldName)
			except UnicodeDecodeError as e:
				raise InvalidModelException('%s All field names must be ascii-encodable. "%s" was not. Error was: %s' %(failedValidationStr, tostr(fieldName), str(e)))

			if isinstance(fieldName, (IRPickleField, IRCompressedField)) and fieldName in indexedFieldSet:
				raise InvalidModelException('%s Field Type %s - (%s) cannot be indexed.' %(failedValidationStr, str(fieldName.__class__.__name__), tostr(fieldName)))
				

		if bool(indexedFieldSet - fieldSet):
			raise InvalidModelException('%s All INDEXED_FIELDS must also be present in FIELDS. %s exist only in INDEXED_FIELDS' %(failedValidationStr, str(list(indexedFieldSet - fieldSet)), ) )
		
		if bool(base64FieldSet - fieldSet):
			raise InvalidModelException('%s All BASE64_FIELDS must also be present in FIELDS. %s exist only in BASE64_FIELDS' %(failedValidationStr, str(list(base64FieldSet - fieldSet)), ) )
		if bool(base64FieldSet.intersection(indexedFieldSet)):
			raise InvalidModelException('%s You cannot index on a base64-encoded field.' %(failedValidationStr,))
		if bool(binaryFieldSet - fieldSet):
			raise InvalidModelException('%s All BINARY_FIELDS must also be present in FIELDS. %s exist only in BINARY_FIELDS' %(failedValidationStr, str(list(binaryFieldSet - fieldSet)), ) )
		if bool(binaryFieldSet.intersection(indexedFieldSet)):
			raise InvalidModelException('%s You cannot index on a binary field.' %(failedValidationStr,))

		validatedModels.add(keyName)
		return True

	@classmethod
	def connect(cls, redisConnectionParams):
		'''
			connect - Create a class of this model which will use an alternate connection than the one specified by REDIS_CONNECTION_PARAMS on this model.

			@param redisConnectionParams <dict> - Dictionary of arguments to redis.Redis, same as REDIS_CONNECTION_PARAMS.

			@return - A class that can be used in all the same ways as the existing IndexedRedisModel, but that connects to a different instance.
		'''
		if not isinstance(redisConnectionParams, dict):
			raise ValueError('redisConnectionParams must be a dictionary!')

		class ConnectedIndexedRedisModel(cls):
			REDIS_CONNECTION_PARAMS = redisConnectionParams
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
		self.fieldNames = self.mdl.FIELDS
		self.indexedFields = self.mdl.INDEXED_FIELDS
		self.base64Fields = self.mdl.BASE64_FIELDS
		self.binaryFields = self.mdl.BINARY_FIELDS

		self._connection = None

	def _get_new_connection(self):
		'''
			_get_new_connection - Get a new connection
			internal
		'''
		return redis.Redis(**self.mdl.REDIS_CONNECTION_PARAMS)

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

			@return - Key name string
		'''
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':idx:', indexedField, ':', getattr(indexedField, 'toStorage', tostr)(val)])
		

	def _get_key_for_id(self, pk):
		'''
			_get_key_for_id - Returns the key name that holds all the data for an object
			Internal

			@param pk - primary key

			@return - Key name string
		'''
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':data:', tostr(pk)])

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
		return tostr(conn.get(self._get_next_id_key()) or 0)

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
		return tostr(conn.incr(self._get_next_id_key()))

	def _getTempKey(self):
		'''
			_getTempKey - Generates a temporary key for intermediate storage
		'''
		return self._get_ids_key() + '__' + uuid.uuid4().__str__()

class IndexedRedisQuery(IndexedRedisHelper):
	'''
		IndexedRedisQuery - The query object. This is the return of "Model.objects" and "Model.objects.filter"
	'''
	
	def __init__(self, *args, **kwargs):
		IndexedRedisHelper.__init__(self, *args)

		self.filters = [] # Filters are ordered for optimization
		self.notFilters = []


	def _dictToObj(self, theDict):
		binaryFields = self.mdl.BINARY_FIELDS
		if not binaryFields:
			obj = self.mdl(**decodeDict(theDict))
		else:
			binaryItems = {}
			nonBinaryItems = {}
			for key, value in theDict.items():
				key = tostr(key)
				if key in binaryFields:
					binaryItems[key] = value
				else:
					nonBinaryItems[key] = value
			obj = self.mdl(**decodeDict(nonBinaryItems))
			for key, value in binaryItems.items():
				setattr(obj, key, value)
				obj._origData[key] = value
		obj._decodeBase64Fields()
#		self.mdl._convertFieldValues(obj) # Trying this in __init__ see how that goes
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
		selfCopy = copy.deepcopy(self)
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
			return matchedKeys
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

		return QueryableListObjs([])

	def allByAge(self):
		'''
			allByAge - Get the underlying objects which match the filter criteria, ordered oldest -> newest
				If you are doing a queue or just need the head/tail, consider .first() and .last() instead.

			@return - Objects of the Model instance associated with this query, sorted oldest->newest
		'''
		matchedKeys = self.getPrimaryKeys(sortByAge=True)
		if matchedKeys:
			return self.getMultiple(matchedKeys)

		return QueryableListObjs([])

	def allOnlyFields(self, fields):
		'''
			allOnlyFields - Get the objects which match the filter criteria, only fetching given fields.

			@param fields - List of fields to fetch

			@return - Partial objects with only the given fields fetched
		'''
		matchedKeys = self.getPrimaryKeys()
		if matchedKeys:
			return self.getMultipleOnlyFields(matchedKeys, fields)

		return QueryableListObjs([])

	def allOnlyIndexedFields(self):
		'''
			allOnlyIndexedFields - Get the objects which match the filter criteria, only fetching indexed fields.

			@return - Partial objects with only the indexed fields fetched
		'''
		matchedKeys = self.getPrimaryKeys()
		if matchedKeys:
			return self.getMultipleOnlyIndexedFields(matchedKeys)

		return QueryableListObjs([])
		
	
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
		return self.mdl.deleter.deleteMultiple(self.allOnlyIndexedFields())

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
		return self._dictToObj(res)
	
	def getMultiple(self, pks):
		'''
			getMultiple - Gets multiple objects with a single atomic operation

			@param pks - list of internal keys
		'''

		if type(pks) == set:
			pks = list(pks)

		if len(pks) == 1:
			# Optimization to not pipeline on 1 id
			return QueryableListObjs([self.get(pks[0])])

		conn = self._get_connection()
		pipeline = conn.pipeline()
		for pk in pks:
			key = self._get_key_for_id(pk)
			pipeline.hgetall(key)

		res = pipeline.execute()
		
		ret = QueryableListObjs()
		i = 0
		pksLen = len(pks)
		while i < pksLen:
			if res[i] is None:
				ret.append(None)
				i += 1
				continue
			res[i]['_id'] = pks[i]
			obj = self._dictToObj(res[i])
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
		return self._dictToObj(objDict)

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
			return QueryableListObjs([self.getOnlyFields(pks[0], fields)])
		conn = self._get_connection()
		pipeline = conn.pipeline()

		for pk in pks:
			key = self._get_key_for_id(pk)
			pipeline.hmget(key, fields)

		res = pipeline.execute()
		ret = QueryableListObjs()
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
			obj = self._dictToObj(objDict)
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
			reindex - Reindexes the objects matching current filterset. Use this if you add/remove a field to INDEXED_FIELDS
		'''
		objs = self.all()
		saver = IndexedRedisSave(self.mdl)
		saver.reindex(objs)


class IndexedRedisSave(IndexedRedisHelper):
	'''
		IndexedRedisClass - Class used to save objects. Used with Model.save is called.
			Except for advanced usage, this is probably for internal only.
	'''

	def save(self, obj, usePipeline=True, forceID=False, conn=None):
		'''
			save - Save an object associated with this model. **Interal Function!!** You probably want to just do object.save() instead of this.

			@param obj - The object to save
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

		if isinstance(obj, list) or isinstance(obj, tuple):
			objs = obj
		else:
			objs = [obj]

		objsLen = len(objs)

		if forceID is not False:
			# Compat with old poor design.. :(
			if isinstance(forceID, tuple) or isinstance(forceID, list):
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


	def _doSave(self, obj, isInsert, conn, pipeline=None):
		if pipeline is None:
			pipeline = conn

		newDict = obj.asDict(convertValueTypes=False)
		key = self._get_key_for_id(obj._id)

		if isInsert is True:
			for fieldName in self.fieldNames:
				fieldValue = newDict.get(fieldName, '')
				if fieldName in self.base64Fields:
					fieldValue = b64encode(tobytes(fieldValue))

				conn.hset(key, fieldName, fieldValue)

			self._add_id_to_keys(obj._id, pipeline)

			for indexedField in self.indexedFields:
				self._add_id_to_index(indexedField, obj._id, newDict[indexedField], pipeline)
		else:
			updatedFields = obj.getUpdatedFields()
			for fieldName, fieldValue in updatedFields.items():
				(oldValue, newValue) = fieldValue

				if fieldName in self.base64Fields:
					newValue = b64encode(tobytes(newValue))

				conn.hset(key, fieldName, newValue)

				if fieldName in self.indexedFields:
					self._rem_id_from_index(fieldName, obj._id, oldValue, pipeline)
					self._add_id_to_index(fieldName, obj._id, newValue, pipeline)

			obj._origData = copy.copy(newDict)

	def reindex(self, objs, conn=None):
		'''
			reindex - Reindexes a given list of objects. Probably you want to do Model.objects.reindex() instead of this directly.

			@param objs list<IndexedRedisModel> - List of objects to reindex
			@param conn <redis.Redis or None> - Specific Redis connection or None to reuse
		'''
		if conn is None:
			conn = self._get_connection()

		pipeline = conn.pipeline()

		objDicts = [obj.asDict(True, convertValueTypes=False) for obj in objs]

		for fieldName in self.indexedFields:
			for objDict in objDicts:
				self._rem_id_from_index(fieldName, objDict['_id'], objDict[fieldName], pipeline)
				self._add_id_to_index(fieldName, objDict['_id'], objDict[fieldName], pipeline)

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
		for fieldName in self.indexedFields:
			self._rem_id_from_index(fieldName, obj._id, obj._origData[fieldName], pipeline)
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
		
	

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
