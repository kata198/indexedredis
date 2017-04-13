IndexedRedis
============

A redis-backed very very fast ORM-style framework that supports indexes. It performs searches with O(1) efficency!

IndexedRedis supports both "equals" and "not-equals" operators for comparison. It also provides full atomic support for replacing entire datasets (based on model), which is useful for providing a fast frontend for SQL. In that use-case, a task that runs on an interval would fetch/calculate datasets from the SQL backend, and do an atomic replace on the datasets the front-end would query.


Further client-side filtering (like greater-than, contains, etc) is available after the data has been fetched (see "Filter Results" below)

My tests have shown that for using equivalent models between flask/mysql and IndexedRedis, a 600% - 1200% performance increase occurs, yet if you design your storage directly as IndexedRedis models, you are able to achieve much higher gains.

It is compatible with python 2.7 and python 3. It has been tested with python 2.7, 3.4, 3.5.

4.0 Status
----------

**Incomplete -- This document does not contain all updates in the 4.0 series, but due to lack of time this stable code with many improvements over IndexedRedis 3 has been sitting idle for 8 months. So I've released it. There should be plenty of examples in the "tests" directory, and it's completely backwards-compatible with IndexedRedis 3, so feel free to explore for new features!.**

If you want to write additional / better documentation, please email me at kata198 at gmail dot com . 

Automatic and Native Types
--------------------------

Since 4.0, IndexedRedis supports defining fields which will automatically be converted to/from native python types (such as int, float, datetime), as well as anything that can be represented with json (dicts, lists). You just provide the type in its native format, and all the conversion happens behind the scenes. When fetched, the object returned also contains fields in their native types.

IndexedRedis also supports features such as automatically pickling/unpickling fields, compression/decompression, and supports defining your own custom field types through a standard interface.

See "Advanced Fields" section below for more information.


API Reference
-------------

Most, but not all methods are convered in this document.
For full pydoc reference, see:

https://pythonhosted.org/indexedredis/


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
			IRField('track_number', valueType=int), # Convert automatically to/from int
			'duration',
			IRField('releaseDate', valueType=datetime.datetime),  # Convert automatically to/from datetime
			'description',
			'copyright',
			IRField('mp3_data', valueType=None), # Do not perform any conversion on the data.
			IRCompressedField('thumbnail', compressMode='gzip'),      # Compress this field in storage using "bz2" compression
            IRField('tags', valueType=list),
		]

		INDEXED_FIELDS = [ \
					'artist',
					'title',
					'track_number',
		]

		KEY_NAME = 'Songs'


**Model Fields:**

*FIELDS* - REQUIRED. A list of string or IRField objects (or their subclasses) which name the fields that can be used for storage. (see "Advanced Fields" section below)

	 Example: ['Name', 'Description', 'Model', IRFixedPointField('Price', 2), IRField('timestamp', valueType=datetime), IRField('remainingStock', valueType=int)]

*INDEXED_FIELDS* - A list of strings containing the names of fields that will be indexed. Can only filter on indexed fields. Adds insert/delete time. Entries must also be present in FIELDS.

	 Example: ['Name', 'Model']


*KEY_NAME* - REQUIRED. A unique name name that represents this model. Think of it like a table name.

	 Example: 'Items'

*REDIS_CONNECTION_PARAMS* - provides the arguments to pass into "redis.Redis", to construct a redis object.

	 Example: {'host' : '192.168.1.1'}


**Deprecated Fields:**

The following class-level items have been deprecated in 4.0 and may be removed in a future version of IndexedRedis. 


*BINARY_FIELDS* - A list of strings containing the names of fields which will be stored directly as unencoded bytes. This is generally faster and more space-efficient than using BASE64\_FIELDS, and should be used for purely binary data.

	Example: ['picture', 'mp3_data']

!!Deprecated. Use IRRawField  or IRField(..., valueType=None) for binary data. 


*BASE64_FIELDS* - A list of strings containing the names of fields which will be automatically converted to/from base64 for storage. This is one way to store binary data, e.x. audio or pictures.

	Example: ['picture', 'mp3_data']

!!Deprecated. Use IRBase64Field for automatic to/from base64 conversion. You can combine this with IRCompressedField which may decrease storage requirements.

Example:   IRFieldChain( 'myBase64Data', [ IRBase64Field(), IRCompressedField() ] )


Advanced Fields
---------------

IndexedRedis since version 4.0 allows you to pass elements of type IRField (extends str) in the FIELDS element.

Doing so allows you to specify certain properties about the field.


Example:

	FIELDS = [ 'name', IRField('age', valueType=int), 'birthday' ]

**Field Name**

The first argument is the string of the field name.

**Type**

You can have a value automatically cast to a certain type (which saves a step if you need to filter further through the QueryableList results, like age\_\_gt=15)

by passing that type as "valueType". (e.x.  IRField('age', valueType=int))

If you use "bool", the values 0 and case insensitive string 'false' will result in False, and 1 or 'true' will result in True.

When using floats, consider using IRFixedPointField, which supports indexing and the same representation regardless of platform (unlike "float"). 

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


**Advanced Types**

An entry in "FIELDS" that is just a string name ( pre 4.0 style ) will be treated same as IRField('myname', valueType=str), and behaves exactly the same, so models are backwards-compatible.

These objects (all importable from IndexedRedis.fields) can all be put in the FIELDS array.


*IRField* - Standard field, takes a name and a "valueType", which is a native python type, or any type you create which implements \_\_new\_\_, taking a signle argument and returning the object. See IndexedRedis/fields/FieldValueTypes for example of how datetime and json are implemented.

When no valueType is defined, str/unicode is the type (same as pre-4.0), and default encoding is used (see set/getDefaultIREncoding functions)


*IRBase64Field* - Converts to and from Base64


*IRCompressedField* - Automatically compresses before storage and decompresses after retrieval. Argument "compressMode" currently supports "zlib" (default) or "bz2".


*IRFixedPointField* - A floating-point with a fixed number of decimal places. This type supports indexing using floats, whereas IRField(...valueType=float) does not, as different platforms have different accuracies, roundings, etc. Takes a parameter, decimalPlaces (default 5), to define the precision after the decimal point.


*IRPickleField* - Automaticly pickles the given object before storage, and unpickles after fetch. Not indexable.

*IRUnicodeField* - Field that takes a parameter, "encoding", to define an encoding to use for this field. Use this to support fields with arbitrary encodings, as IRField will use the default encoding for strings.

*IRRawField* - Field that is not converted in any, to or from Redis. On fetch this will always be "bytes" type (or str in python2). On python3 this is very similar to IRField(...valueType=None), but python2 needs this to store binary data without running into encoding issues.


**Chaining Multiple Types**

You can chain multiple types together using IRFieldChain. Instead of specifying the name on the IRField (or subclass), you specify the name on the IRFieldChain, and list all the types as the second argument (chainedFields). For storage, all operations will be applied left-to-right, and upon fetch the object will be decoded right-to-left.

Example:

	FIELDS = [ \

	...

		IRFieldChain( 'longData', [ IRUnicodeField(encoding='utf-16'), IRCompressedField() ] )
	]

In the above example, you provide "longData" as a string. 

For storage, that string is assumed to be utf-16, and will be compressed (left-to-right)

For fetching, that string is first decompressed, and then encoded using utf-16.


**Hash-Lookups (performance)**


If you want to index/search on very large strings/bytes (such as maybe a genome), IndexedRedis supports hashing the key, i.e. the value will be stored as the value itself, but the key reference used for lookup will be a hash of that string.

This increases performance, saves network traffic, and shrinks storage requirements.


To do this, set the "hashIndex" attribute of an IRField to True.

	FIELDS = [ \

	...
		IRField ( 'genomeStr', hashIndex=True )
	]

and that's it! Filter and fetch and all operations remain the same (i.e. you just use the value directly, same as if "hashIndex" was False), but behind-the-scenes the lookups will all be done with the MD5 hash of the value.


**Converting existing models to/from hashed indexes**


IndexedRedis provides helper methods to automatically convert existing unhashed keys to hashed, and also hashed keys back to unhashed.

To do this, change your IndexedRedisModel accordingly, and then call (for a model class named MyModel):

	MyModel.objects.compat_convertHashedIndexes()

This will delete both the hashed and non-hashed key-value for any IRField which supports the "hashIndex" property.
If you just call "reindex" and you've changed the property "hashIndex" on any field, you'll be left with lingering key-values.

This function, by default (fetchAll=True) will fetch all records of this paticular model, and operate on them one-by-one. This is more efficient, but if memory constraints are an issue, you can pass fetchAll=False, which will fetch one object, convert indexes, save, then fetch next object. This is slower, but uses less memory.

NOTHING should be using the models while this function is being called (it doesn't make sense anyway to change schema whilst using it).



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


Encodings
---------

IndexedRedis will use by default your system default encoding (sys.getdefaultencoding), unless it is ascii (python2) in which case it will default to utf-8.

You may change this via IndexedRedis.setDefaultIREncoding.

Use IRRawField to not perform any encoding/decoding, or use IRUnicodeField to use a different explicit encoding at a per-field level.


Changes
-------

See https://raw.githubusercontent.com/kata198/indexedredis/master/Changelog

Example
-------


See https://raw.githubusercontent.com/kata198/indexedredis/master/test.py


Contact Me
----------

Please e-mail me with any questions, bugs, or even just to tell me that you're using it! kata198@gmail.com
