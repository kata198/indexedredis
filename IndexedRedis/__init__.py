#Copyright (c) Timothy Savannah under LGPL, All Rights Reserved. See LICENSE for more information

import copy
import sys
import uuid
import redis

INDEXED_REDIS_PREFIX = '_ir_|'

INDEXED_REDIS_VERSION = (2, 0, 0)
INDEXED_REDIS_VERSION_STR = '2.0.0'

try:
	classproperty
except NameError:
	class classproperty(object):
		def __init__(self, getter):
			self.getter = getter
		def __get__(self, instance, owner):
			return self.getter(owner)


if bytes == str:
	# Python 2, no additional decoding necessary.
	tostr = str
	decodeDict = lambda x : x
else:
	# Python 3, additional decoding necessary
	try:
		defaultEncoding = sys.getdefaultencoding()
	except:
		defaultEncoding = 'utf-8'
	
	def tostr(x):
		if isinstance(x, bytes) is False:
			return str(x)
		return x.decode(defaultEncoding)
	def decodeDict(theDict):
		res2 = {}
		for key, val in theDict.items():
			res2[tostr(key)] = tostr(val)
		return res2
		

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
	
	FIELDS = []
	INDEXED_FIELDS = []

	KEY_NAME = None

	REDIS_CONNECTION_PARAMS = {}

	_connection = None

	def __init__(self, *args, **kwargs):
		'''
			__init__ - Set the values on this object. MAKE SURE YOU CALL THE SUPER HERE, or else things will not work.

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
	
	def toDict(self, includeMeta=False):
		ret = {}
		for fieldName in self.FIELDS:
			val = getattr(self, fieldName, '')
			ret[fieldName] = tostr(val)

		if includeMeta is True:
			ret['_id'] = getattr(self, '_id', '')
		return ret

	asDict = toDict
	
	def getUpdatedFields(self):
		'''
			Returns dictionary of fieldName : tuple(old, new)
		'''
		updatedFields = {}
		for fieldName in self.FIELDS:
			thisVal = tostr(getattr(self, fieldName))
			if self._origData[fieldName] != thisVal:
				updatedFields[fieldName] = (self._origData[fieldName], thisVal)
		return updatedFields

	@classproperty
	def objects(cls):
		return IndexedRedisQuery(cls)

	@classproperty
	def saver(cls):
		return IndexedRedisSave(cls)

	@classproperty
	def deleter(cls):
		return IndexedRedisDelete(cls)

	def save(self):
		saver = IndexedRedisSave(self.__class__)
		return saver.save(self)
	
	def delete(self):
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
		IndexedRedisHelper - internal helper class
	'''


	def __init__(self, mdl):
		self.mdl = mdl
		self.keyName = self.mdl.KEY_NAME
		self.fieldNames = self.mdl.FIELDS
		self.indexedFields = self.mdl.INDEXED_FIELDS
		self._connection = getattr(mdl, '_connection', None)

	def _get_new_connection(self):
		return redis.Redis(**self.mdl.REDIS_CONNECTION_PARAMS)

	def _get_connection(self, existingConn=None):
		if existingConn is not None: # Allows one-liners
			return existingConn
		if self._connection is None:
			self._connection = self._get_new_connection() 
		return self._connection

	def _get_ids_key(self):
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName + ':keys'])

	def _add_id_to_keys(self, pk, conn=None):
		conn = self._get_connection(conn)
		conn.sadd(self._get_ids_key(), pk)
	
	def _rem_id_from_keys(self, pk, conn=None):
		conn = self._get_connection(conn)
		conn.srem(self._get_ids_key(), pk)

	def _add_id_to_index(self, indexedField, pk, val, conn=None):
		conn = self._get_connection(conn)
		conn.sadd(self._get_key_for_index(indexedField, val), pk)

	def _rem_id_from_index(self, indexedField, pk, val, conn=None):
		conn = self._get_connection(conn)
		conn.srem(self._get_key_for_index(indexedField, val), pk)
		
	def _get_key_for_index(self, indexedField, val):
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':idx:', indexedField, ':', tostr(val)])
		

	def _get_key_for_id(self, pk):
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':data:', tostr(pk)])

	def _get_next_id_key(self):
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':next'])

	def peekNextID(self):
		conn = self._get_connection()
		return int(conn.get(self._get_next_id_key()) or 0)

	def getNextID(self):
		conn = self._get_connection()
		return conn.incr(self._get_next_id_key())

	def _getTempKey(self):
		return self._get_ids_key() + '__' + uuid.uuid4().__str__()

class IndexedRedisQuery(IndexedRedisHelper):
	'''
		IndexedRedisQuery - The query object. This is the return of "Model.objects.filter"
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
			

	def all(self):
		'''
			all - Get the underlying objects which match the filter criteria.

			Example:   objs = Model.objects.filter(field1='value', field2='value2').all()

			@return - Objects of the Model instance associated with this query.
		'''
		conn = self._get_connection()
		# Apply filters, and return object
		numFilters = len(self.filters)
		numNotFilters = len(self.notFilters)

		if numFilters + numNotFilters == 0:
			allKeys = conn.smembers(self._get_ids_key())
			return self.getMultiple(allKeys)

		if numNotFilters == 0:
			if numFilters == 1:
				(filterFieldName, filterValue) = self.filters[0]
				matchedKeys = conn.smembers(self._get_key_for_index(filterFieldName, filterValue))
				if len(matchedKeys) == 0:
					return []
				return self.getMultiple(matchedKeys)

			indexKeys = [self._get_key_for_index(filterFieldName, filterValue) for filterFieldName, filterValue in self.filters]
			matchedKeys = conn.sinter(indexKeys)
			if len(matchedKeys) == 0:
				return []

			return self.getMultiple(matchedKeys)

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


		if len(matchedKeys) == 0:
			return []
		return self.getMultiple(matchedKeys)
		

	def get(self, pk, conn=None):
		'''
			get - Get a single value with the internal primary key.

			@param pk - internal primary key (can be found via .getPk() on an item)
		'''
		conn = self._get_connection(conn)
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
			self.get(pk, pipeline)

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
			
class IndexedRedisSave(IndexedRedisHelper):
	'''
		IndexedRedisClass - Class used to save objects. Used with Model.save is called.
	'''

	def save(self, obj, useMulti=True, forceID=False, conn=None):
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
					obj._id = self.getNextID()
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
						self._rem_id_from_index(indexedField, obj._id, oldValue, pipeline)
						self._add_id_to_index(indexedField, obj._id, newValue, pipeline)
				obj._origData = copy.copy(newDict)
			ids.append(obj._id)
			i += 1

		if useMulti is True:
			pipeline.execute()

		return ids


class IndexedRedisDelete(IndexedRedisHelper):
	'''
		IndexedRedisDelete - Used for removing objects. Called when Model.delete is used
	'''

	def deleteOne(self, obj, conn=None):
		conn = self._get_connection(conn)
		if not getattr(obj, '_id', None):
			return 0
		
		conn.delete(self._get_key_for_id(obj._id))
		self._rem_id_from_keys(obj._id, conn)
		for fieldName in self.indexedFields:
			self._rem_id_from_index(fieldName, obj._id, obj._origData[fieldName])
		obj._id = None
		return 1
	
	def deleteMultiple(self, objs):
		conn = self._get_connection()
		pipeline = conn.pipeline()

		numDeleted = 0

		for obj in objs:
			numDeleted += self.deleteOne(obj, pipeline)

		return numDeleted
	
		
# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
