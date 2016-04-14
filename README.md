IndexedRedis
============

A redis-backed very very fast ORM-style framework that supports indexes. It performs searches with O(1) efficency!

IndexedRedis supports both "equals" and "not-equals" operators for comparison. It also provides full atomic support for replacing entire datasets (based on model), which is useful for providing a fast frontend for SQL. In that use-case, a task that runs on an interval would fetch/calculate datasets from the SQL backend, and do an atomic replace on the datasets the front-end would query.

Further client-side filtering (like greater-than, contains, etc) is available after the data has been fetched (see "Filter Results" below)

My tests have shown that for using equivalent models between flask/mysql and IndexedRedis, a 600% - 1200% performance increase occurs, yet if you design your storage directly as IndexedRedis models, you are able to achieve much higher gains.

It is compatible with python 2.7 and python 3. It has been tested with python 2.7 and 3.4.


API Reference
-------------

Most, but not all methods are documented here.

See:

http://htmlpreview.github.io/?https://github.com/kata198/indexedredis/blob/master/IndexedRedis.html#IndexedRedisQuery 

for full documentation, as a pydoc document.

**Below is a quick highlight/overview:**


IndexedRedisModel
-----------------

This is the model you should extend.


**Example Model:**

	class Song(IndexedRedisModel):
	    
		FIELDS = [ \
				'artist',
				'title',
				'album',
				'track_number',
				'duration',
				'description',
				'copyright',
				'mp3_data',
		]

		INDEXED_FIELDS = [ \
					'artist',
					'title',
					'track_number',
		]

		BINARY_FIELDS = [ 'mp3_data', ]

		KEY_NAME = 'Songs'


**Model Fields:**

*FIELDS* - REQUIRED. A list of strings which name the fields that can be used for storage. (see "Advanced Fields" section below)

	 Example: ['Name', 'Description', 'Model', 'Price']

*INDEXED_FIELDS* - A list of strings containing the names of fields that will be indexed. Can only filter on indexed fields. Adds insert/delete time. Entries must also be present in FIELDS.

	 Example: ['Name', 'Model']

*BINARY_FIELDS* - A list of strings containing the names of fields which will be stored directly as unencoded bytes. This is generally faster and more space-efficient than using BASE64\_FIELDS, and should be used for purely binary data.

	Example: ['picture', 'mp3_data']

*BASE64_FIELDS* - A list of strings containing the names of fields which will be automatically converted to/from base64 for storage. This is one way to store binary data, e.x. audio or pictures.

	Example: ['picture', 'mp3_data']

*KEY_NAME* - REQUIRED. A unique name name that represents this model. Think of it like a table name.

	 Example: 'Items'

*REDIS_CONNECTION_PARAMS* - provides the arguments to pass into "redis.Redis", to construct a redis object.

	 Example: {'host' : '192.168.1.1'}


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

**NULL Values**

    For any type except strings (including the default type, string), a null value is assigned irNull (of type IRNullType).

irNull does not equal empty string, or anything except another irNull. This is to destinguish say, no int assigned vs int(0)

You can check a typed field against the "irNull" variable found in the IndexedRedis or IndexedRedis.fields.

e.x. 

	from IndexedRedis import irNull

..


	# Can be used directly in the model filtering
	notDangerFive = MyModel.objects.filter(dangerLevel__ne=irNull).filter(dangerLevel__ne=5).all()

	# or in results, through Queryable List. Or direct comparison (not shown)
	myResults = MyModel.objects.filter(something='value').all()

	notDangerFive = myResults.filter(dangerLevel__ne=irNull).filter(dangerLevel__ne=5)


**Complex Types**

Please note that not all types are suitable for being stored in an IndexedRedisModel. If you are trying to store a dict, for example, consider just making those items natural fields, or store a foreign key to another object (using \_id), and consider that your model may need to be refactored from relational to soething more flat.


Redis can only store strings, integers, and floats, and everything IndexedRedis stores is a string. 

Consider that these advanced conversions can happen within your model class, as many complex types can be represented by a simple type.

You can technically store any field as a pickle string, and use a getter/setter to do the pickling and unpickling, though I would consider that poor design.

Here is an example of having a datetime object as a member of a model, whilst natively storing a simple type:


	class MyModel(IndexedRedisModel):

	FIELDS = [ 'name', IRField('_timestamp', valueType=int) ]

	def __init__(self, *args, **kwargs):
		if 'timestamp' in kwargs:
			if isinstance(kwargs['timestamp'], datetime):
				kwargs['_timestamp'] = int(kwargs['timestamp'].strftime('%s'))
			else:
				kwargs['_timestamp'] = kwargs['timestamp']

			del kwargs['timestamp']

		IndexedRedis.__init__(self, *args, **kwargs)

	@property
	def timestamp(self):
		if not self._timestamp:
			return None
		return datetime.datetime.fromtimestamp(self._timestamp)

So you can create it like:

	x = MyModel(name='Something', timestamp=datetime.now())
	x.save()

And access the native \_timestamp field as a complex datetime object just by doing:

	x.timestamp



Model Validation
----------------

The model will be validated the first time an object of that type is instantiated. If there is something invalid in how it is defined, an "InvalidModelException" will be raised.


Usage
-----

Usage is very similar to Django or Flask.

**Query:**

Calling .filter or .filterInline builds a query/filter set. Use one of the *Fetch* methods described below to execute a query.

	objects = SomeModel.objects.filter(param1=val).filter(param2=val).all()

Supported fetch types from the database are equals and not-equals. To use a not-equals expression, append "\_\_ne" to the end of the field name.

	objects = SomeModel.objects.filter(param1=val, param2\_\_ne=val2).all()

All filters are applied on the redis server using hash lookups. All filters of the same type (equals or not equals) are applied in one command to Redis. So applying filters, **no matter how many filters**, is one to two commands total.


**Filter Results / client-side filtering:**

The results from the .all operation is a [QueryableList](https://pypi.python.org/pypi/QueryableList) of all matched objects. The type of each object is the same as the model. You can use a QueryableList same as a normal list, but it can be more powerful than that:

Once you have fetched the results from Redis, the QueryableList allows you to perform further client-side filtering using any means that QueryableList supports (e.x. gt, contains, in). 


Example:

	mathTeachers = People.objects.filter(job='Math Teacher').all()

	experiencedMathTeachers = mathTeachers.filter(experienceYears__gte=10) # Get math teachers with greater than or equal to 10 years experience

	cheeseLovingMathTeachers = matchTeachers.filter(likes__splitcontains=(' ', 'cheese')) # Check a space-separated list field, 'likes', and see if it contains 'cheese'


See https://github.com/kata198/QueryableList for more information.



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

**Get Primary Key:**

Sometimes you may want to reference an individual object, via a foreign-key relationship or just to retrieve faster / unique rather than filtering. 

Every object saved has a unique primary key (unique per the model) which can be retrieved by the "getPk" method. You can then use this value on exists, get, getMultiple, etc methods.


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

	exists - Tests the existance of an object under a given pk


**Model Functions**

Actual objects contain methods including:

	save   - Save this object (create if not exist, otherwise update)

	delete - Delete this object

	getUpdatedFields - See changes since last fetch


**Update Index**

As your model changes, you may need to add a field to the INDEXED\_FIELDS array. If this was an already existing field, you can reindex the models by doing:

	MyModel.objects.reindex()


**Connecting to other Redis instances**

You may want to use the same model on multiple Redis instances. To do so, use the .connect method on IndexedRedisModel.

	AltConnectionMyModel = MyModel.connect({'host' : 'althost', 'db' : 4})

Then, use AltConnectionMyModel just as you would use MyModel.


Binary/Bytes Data Support
-------------------------

IndexedRedis, as of version 2.9.0, has the ability to store and retrieve unencoded (binary) data, e.x. image files, executables, raw device data, etc.


Add the field name to the BINARY\_FIELDS array, and IndexedRedis will retrieve and store directly as binary unencoded data. 

So you may have a model like this:


	class FileObj(IndexedRedis.IndexedRedisModel):

		FIELDS = [ 'filename', 'data', 'description' ]

		INDEXED_FIELDS = [ 'filename' ]

		BINARY_FIELDS  = ['data']



Base64 Encoding Data Support
----------------------------

Since version 2.7.0, IndexedRedis has support for base64 encoding data, by adding the field name to the "BASE64\_FIELDS" array. Use this if you want to keep your data purely text-friendly, but for most cases you should probably use BINARY\_FIELDS.

Simply by adding a field to the "BASE64\_FIELDS" array, IndexedRedis will transparently handle base64-encoding before store, and decoding after retrieval. 

So you may have a model like this:

	class FileObj(IndexedRedis.IndexedRedisModel):

		FIELDS = [ 'filename', 'data', 'description' ]

		INDEXED_FIELDS = [ 'filename' ]

		BASE64_FIELDS  = ['data']


In the "data" field you can dump file contents, like an mp3 or a jpeg, and IndexedRedis will handle all the encoding for you. You will just provide "bytes" data to that field.


Encodings
---------

IndexedRedis will use by default your system default encoding (sys.getdefaultencoding), unless it is ascii (python2) in which case it will default to utf-8.

You may change this via IndexedRedis.setEncoding

Changes
-------

See https://raw.githubusercontent.com/kata198/indexedredis/master/Changelog

Example
-------


See https://raw.githubusercontent.com/kata198/indexedredis/master/test.py


Contact Me
----------

Please e-mail me with any questions, bugs, or even just to tell me that you're using it! kata198@gmail.com
