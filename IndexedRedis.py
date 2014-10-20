import copy
import redis
import types

INDEXED_REDIS_PREFIX = '_rr_|'

try:
    classproperty
except NameError:
    class classproperty(object):
        def __init__(self, getter):
            self.getter = getter
        def __get__(self, instance, owner):
            return self.getter(owner)

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

		if not self.KEY_NAME:
			raise NotImplementedError('Indexed Redis Model %s must extend KEY_NAME' %(self.__class__.__name__, ))
		if not self.FIELDS:
			raise NotImplementedError('Indexed Redis Model %s must have fields' %(self.__class__.__name__, ))

		self._origData = {}

		for fieldName in self.FIELDS:
			val = str(kwargs.get(fieldName, ''))
			setattr(self, fieldName, val)
			self._origData[fieldName] = val

		self._id = kwargs.get('_id', None)
	
	def toDict(self, includeMeta=False):
		ret = {}
		for fieldName in self.FIELDS:
			val = getattr(self, fieldName, '')
			ret[fieldName] = str(val)

		if includeMeta is True:
			ret['_id'] = getattr(self, '_id', '')
		return ret
	
	def getUpdatedFields(self):
		'''
			Returns dictionary of fieldName : tuple(old, new)
		'''
		updatedFields = {}
		for fieldName in self.FIELDS:
			thisVal = str(getattr(self, fieldName))
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


		
		
class IndexedRedisException(Exception):
	pass
			

class IndexedRedisHelper(object):


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
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':idx:', indexedField, ':', str(val)])
		

	def _get_key_for_id(self, pk):
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':data:', str(pk)])

	def _get_next_id_key(self):
		return ''.join([INDEXED_REDIS_PREFIX, self.keyName, ':next'])

	def peekNextID(self):
		conn = self._get_connection()
		return int(conn.get(self._get_next_id_key()) or 0)

	def getNextID(self):
		conn = self._get_connection()
		return conn.incr(self._get_next_id_key())

class IndexedRedisQuery(IndexedRedisHelper):
	
	def __init__(self, *args, **kwargs):
		IndexedRedisHelper.__init__(self, *args)

		self.filters = [] # Filters are ordered for optimization

	def _dictToObj(self, theDict):
		return self.mdl(**theDict)

	def filter(self, **kwargs):
		# Only support Equals for now
		for key, value in kwargs.iteritems():
			if key not in self.indexedFields:
				raise ValueError('Field "' + key + '" is not in INDEXED_FIELDS array. Filtering is only supported on indexed fields.')
			self.filters.append( (key, value) )

		return self #chaining
		

	def count(self):
		conn = self._get_connection()
		# Apply filters, and return object
		if len(self.filters) == 0:
			return conn.scard(self._get_ids_key())

		if len(self.filters) == 1:
			(filterFieldName, filterValue) = self.filters[0]
			return conn.scard(self._get_key_for_index(filterFieldName, filterValue))

		indexKeys = [self._get_key_for_index(filterFieldName, filterValue) for filterFieldName, filterValue in self.filters]

		pks = conn.sinter(indexKeys)
		return len(pks)
		

	def all(self):
		conn = self._get_connection()
		# Apply filters, and return object
		if len(self.filters) == 0:
			allKeys = conn.smembers(self._get_ids_key())
			return self.getMultiple(allKeys)

		if len(self.filters) == 1:
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
		

	def get(self, pk, conn=None):
		conn = self._get_connection(conn)
		key = self._get_key_for_id(pk)
		res = conn.hgetall(key)
		if type(res) != dict or not len(res.keys()):
			return None
		res['_id'] = pk
		return self._dictToObj(res)
	
	def getMultiple(self, pks):

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

		for i in xrange(len(pks)):
			if res[i] is None:
				ret.append(None)
				continue
			res[i]['_id'] = pks[i]
			obj = self._dictToObj(res[i])
			ret.append(obj)
			
		return ret
			
class IndexedRedisSave(IndexedRedisHelper):

	def save(self, obj, useMulti=True, forceID=False, conn=None):
		conn = self._get_connection(conn)

		if type(obj) in (types.ListType, types.TupleType):
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

		for i in xrange(len(objs)):
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
				for fieldName, fieldValue in updatedFields.iteritems():
					(oldValue, newValue) = fieldValue
					conn.hset(key, fieldName, newValue)
					if fieldName in self.indexedFields:
						self._rem_id_from_index(indexedField, obj._id, oldValue, pipeline)
						self._add_id_to_index(indexedField, obj._id, newValue, pipeline)
				obj._origData = copy.copy(newDict)
			ids.append(obj._id)

		if useMulti is True:
			pipeline.execute()

		return ids


class IndexedRedisDelete(IndexedRedisHelper):

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
