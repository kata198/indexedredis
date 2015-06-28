# Copyright (c) 2014 Timothy Savannah under LGPL. See LICENSE for more information.
# 

import copy
import sys
import uuid
import redis

# Prefix that all IndexedRedis keys will contain, as to not conflict with other stuff.
INDEXED_REDIS_PREFIX = '_ir_|'

# Version as a tuple (major, minor, patchlevel)
INDEXED_REDIS_VERSION = (2, 3, 1)

# Version as a string
INDEXED_REDIS_VERSION_STR = '2.3.1'

__version__ = INDEXED_REDIS_VERSION_STR

try:
	classproperty
except NameError:
	class classproperty(object):
		def __init__(self, getter):
			self.getter = getter
		def __get__(self, instance, owner):
			return self.getter(owner)
try:
	defaultEncoding = sys.getdefaultencoding()
	if defaultEncoding == 'ascii':
		defaultEncoding = 'utf-8'
except:
	defaultEncoding = 'utf-8'

def setEncoding(encoding):
	'''
		setEncoding - Sets the encoding used by IndexedRedis

		@param encoding - An encoding (like utf-8)
	'''
	global defaultEncoding
	defaultEncoding = encoding

def getEncoding():
	'''
		getEncoding - Get the encoding that IndexedRedis will use
	'''
	global defaultEncoding
	return defaultEncoding

if bytes == str:
	# Python 2
	def tostr(x):
		if isinstance(x, unicode):
			return x.encode(defaultEncoding)
		else:
			return str(x)
else:
	# Python 3
	
	def tostr(x):
		if isinstance(x, bytes) is False:
			return str(x)
		return x.decode(defaultEncoding)


# Changing redis encoding into requested encoding
decodeDict = lambda origDict : {tostr(key) : tostr(origDict[key]) for key in origDict}


class IndexedRedisModel(object):
	'''
	   This is the model you should extend.

	Required fields:

	FIELDS is a list of strings, naming "fields" that will be stored
	INDEXED_FIELDS is a list of strings containing the names of fields that should be indexed. Every field added here slows insert performance,
		because redis is fast, consider not indexing every possible field but rather indexing the ones for best performance and filtering thereafter.
	
	NOTE: You may only query fields contained within the "INDEXED_FIELDS" array. It is certainly possible from within this lib to support non-indexed
		searching, but I'd rather that be done in the client to make obvious where the power of this library is.

	KEY_NAME is a field which contains the "base" keyname, unique to this object. (Like "Users" or "Drinks")

		REDIS_CONNECTION_PARAMS provides the arguments to pass into "redis.Redis", to construct a redis object.

	An alternative to supplying REDIS_CONNECTION_PARAMS is to supply a class-level variable `_connection`, which contains the redis instance you would like to use. This variable can be created as a class-level override, or set on the model during __init__. 

		Usage is like normal ORM

		SomeModel.objects.filter(param1=val).filter(param2=val).all()

		obj = SomeModel(...)
		obj.save()

		There is also a powerful method called "reset" which will atomically and locked replace all elements belonging to a model. This is useful for cache-replacement, etc.


		x = [SomeModel(...), SomeModel(..)]

	   SomeModel.reset(x)


	You delete objects by

	someObj.delete()

	and save objects by

	someObj.save()

	'''
	
	# FIELDS - A list of field names, as strings.
	FIELDS = []

	# INDEXED_FIELDS - A list of field names that will be indexed, as strings. Must also be present in FIELDS.
	#  You can only search on indexed fields, but they add time to insertion/deletion
	INDEXED_FIELDS = []

	# KEY_NAME - A string of a unique name which corrosponds to objects of this type.
	KEY_NAME = None

	# REDIS_CONNECTION_PARAMS - A dictionary of parameters to redis.Redis such as host or port. Will be used on all connections.
	REDIS_CONNECTION_PARAMS = {}

	_connection = None

	def __init__(self, *args, **kwargs):
		'''
			__init__ - Set the values on this object. MAKE SURE YOU CALL THE SUPER HERE, or else things will not work.
		'''

		if not self.KEY_NAME:
			raise NotImplementedError('Indexed Redis Model %s must extend KEY_NAME' %(self.__class__.__name__, ))
		if not self.FIELDS:
			raise NotImplementedError('Indexed Redis Model %s must have fields' %(self.__class__.__name__, ))

		self._origData = {}

		for fieldName in self.FIELDS:
			val = tostr(kwargs.get(fieldName, ''))
			setattr(self, fieldName, val)
			self._origData[fieldName] = val

		self._id = kwargs.get('_id', None)
	
	def asDict(self, includeMeta=False):
		'''
			toDict / asDict - Get a dictionary representation of this model.

			@param includeMeta - Include metadata in return. For now, this is only pk stored as "_id"

			@return - Dictionary reprensetation of this object and all fields
		'''
		ret = {}
		for fieldName in self.FIELDS:
			val = getattr(self, fieldName, '')
			ret[fieldName] = tostr(val)

		if includeMeta is True:
			ret['_id'] = getattr(self, '_id', '')
		return ret

	toDict = asDict
	
	def getUpdatedFields(self):
		'''
			getUpdatedFields - See changed fields.
			
			@return - a dictionary of fieldName : tuple(old, new)
		'''
		updatedFields = {}
		for fieldName in self.FIELDS:
			thisVal = tostr(getattr(self, fieldName))
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
		conn = cls._connection or redis.Redis(**cls.REDIS_CONNECTION_PARAMS)

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
		self._connection = getattr(mdl, '_connection', None)

	def _get_new_connection(self):
		'''
			_get_new_connection - Get a new connection
			internal
		'''
		return redis.Redis(**self.mdl.REDIS_CONNECTION_PARAMS)

	def _get_connection(self, existingConn=None):
		'''
			_get_connection - Maybe get a new connection, or reuse if passed in.
				Will share a connection with a model
			internal
		'''
		if existingConn is not None: # Allows one-liners
			return existingConn
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
		conn = self._get_connection(conn)
		conn.sadd(self._get_ids_key(), pk)
	
	def _rem_id_from_keys(self, pk, conn=None):
		'''
			_rem_id_from_keys - Remove primary key from table
			internal
		'''
		conn = self._get_connection(conn)
		conn.srem(self._get_ids_key(), pk)

	def _add_id_to_index(self, indexedField, pk, val, conn=None):
		'''
			_add_id_to_index - Adds an id to an index
			internal
		'''
		conn = self._get_connection(conn)
		conn.sadd(self._get_key_for_index(indexedField, val), pk)

	def _rem_id_from_index(self, indexedField, pk, val, conn=None):
		'''
			_rem_id_from_index - Removes an id from an index
			internal
		'''
		conn = self._get_connection(conn)
		conn.srem(self._get_key_for_index(indexedField, val), pk)
		
	def _get_key_for_index(self, indexedField, val):
		'''
			_get_key_for_index - Returns the key name that would hold the indexes on a value
			Internal - does not validate that indexedFields is actually indexed. Trusts you. Don't let it down.

			@param indexedField - string of field name
			@param val - Value of field

			@return - Key name string
		'''
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':idx:', indexedField, ':', tostr(val)])
		

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

	def _peekNextID(self):
		'''
			_peekNextID - Look at, but don't increment the primary key for this model.
				Internal.

			@return int - next pk
		'''
		conn = self._get_connection()
		return int(conn.get(self._get_next_id_key()) or 0)

	def _getNextID(self):
		'''
			_getNextID - Get (and increment) the next primary key for this model.
				If you don't want to increment, @see _peekNextID .
				Internal.
				This is done automatically on save. No need to call it.

			@return int - next pk
		'''
		conn = self._get_connection()
		return conn.incr(self._get_next_id_key())

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
		return self.mdl(**decodeDict(theDict))



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
			conn = self._get_connection()
			matchedKeys = conn.smembers(self._get_ids_key())

		elif numNotFilters == 0:
			if numFilters == 1:
				(filterFieldName, filterValue) = self.filters[0]
				matchedKeys = conn.smembers(self._get_key_for_index(filterFieldName, filterValue))
			else:
				indexKeys = [self._get_key_for_index(filterFieldName, filterValue) for filterFieldName, filterValue in self.filters]
				matchedKeys = conn.sinter(indexKeys)

		else:
			notIndexKeys = [self._get_key_for_index(filterFieldName, filterValue) for filterFieldName, filterValue in self.notFilters]
			if numFilters == 0:
				matchedKeys = conn.sdiff(self._get_ids_key(), *notIndexKeys)
			else:
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

		return []

	def allByAge(self):
		'''
			allByAge - Get the underlying objects which match the filter criteria, ordered oldest -> newest
				If you are doing a queue or just need the head/tail, consider .first() and .last() instead.

			@return - Objects of the Model instance associated with this query, sorted oldest->newest
		'''
		matchedKeys = self.getPrimaryKeys(sortByAge=True)
		if matchedKeys:
			return self.getMultiple(matchedKeys)

		return []

	def allOnlyFields(self, fields):
		'''
			allOnlyFields - Get the objects which match the filter criteria, only fetching given fields.

			@param fields - List of fields to fetch

			@return - Partial objects with only the given fields fetched
		'''
		matchedKeys = self.getPrimaryKeys()
		if matchedKeys:
			return self.getMultipleOnlyFields(matchedKeys, fields)

		return []

	def allOnlyIndexedFields(self):
		'''
			allOnlyIndexedFields - Get the objects which match the filter criteria, only fetching indexed fields.

			@return - Partial objects with only the indexed fields fetched
		'''
		matchedKeys = self.getPrimaryKeys()
		if matchedKeys:
			return self.getMultipleOnlyIndexedFields(matchedKeys)

		return []
		
	
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
		import random
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
			return [self.get(pks[0])]

		conn = self._get_connection()
		pipeline = conn.pipeline()
		for pk in pks:
			key = self._get_key_for_id(pk)
			pipeline.hgetall(key)

		res = pipeline.execute()
		
		ret = []
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
			return [self.getOnlyFields(pks[0], fields)]
		conn = self._get_connection()
		pipeline = conn.pipeline()

		for pk in pks:
			key = self._get_key_for_id(pk)
			pipeline.hmget(key, fields)

		res = pipeline.execute()
		ret = []
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

			
class IndexedRedisSave(IndexedRedisHelper):
	'''
		IndexedRedisClass - Class used to save objects. Used with Model.save is called.
			Except for advanced usage, this is probably for internal only.
	'''

	def save(self, obj, useMulti=True, forceID=False, conn=None):
		'''
			save - Save an object associated with this model. You probably will just do object.save() instead of this.

			@param obj - The object to save
			@param useMulti - Do multiple at once
			@param forceID - if not False, force ID to this.
			@param conn - A connection or None

			@return - List of pks
		'''
		conn = self._get_connection(conn)

		if isinstance(obj, list) or isinstance(obj, tuple):
			objs = obj
		else:
			objs = [obj]

		isInserts = []
		for obj in objs:
			if forceID is not False:
				isInsert = True
				obj._id = forceID
			else:
				isInsert = not bool(getattr(obj, '_id', None))
				if isInsert:
					obj._id = self._getNextID()
			isInserts.append(isInsert)

		if useMulti is True:
			pipeline = conn.pipeline()
		else:
			pipeline = conn

		ids = []
		i = 0
		objsLen = len(objs)
		while i < objsLen:
			obj = objs[i]
			newDict = obj.toDict()
			isInsert = isInserts[i]

			key = self._get_key_for_id(obj._id)

			if isInsert is True:
				for fieldName in self.fieldNames:
					conn.hset(key, fieldName, newDict.get(fieldName, ''))
				self._add_id_to_keys(obj._id, pipeline)
				for indexedField in self.indexedFields:
					self._add_id_to_index(indexedField, obj._id, newDict[indexedField], pipeline)
			else:
				updatedFields = obj.getUpdatedFields()
				for fieldName, fieldValue in updatedFields.items():
					(oldValue, newValue) = fieldValue
					conn.hset(key, fieldName, newValue)
					if fieldName in self.indexedFields:
						self._rem_id_from_index(fieldName, obj._id, oldValue, pipeline)
						self._add_id_to_index(fieldName, obj._id, newValue, pipeline)
				obj._origData = copy.copy(newDict)
			ids.append(obj._id)
			i += 1

		if useMulti is True:
			pipeline.execute()

		return ids


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
		conn = self._get_connection(conn)
		if not getattr(obj, '_id', None):
			return 0
		
		conn.delete(self._get_key_for_id(obj._id))
		self._rem_id_from_keys(obj._id, conn)
		for fieldName in self.indexedFields:
			self._rem_id_from_index(fieldName, obj._id, obj._origData[fieldName])
		obj._id = None
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
