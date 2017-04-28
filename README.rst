IndexedRedis
============

A redis-backed very very fast ORM-style framework that supports indexes. It performs searches with O(1) efficency!

You can store and fetch native python types (lists, objects, strings, integers, etc.).

IndexedRedis supports both "equals" and "not-equals" operators for comparison. It also provides full atomic support for replacing entire datasets (based on model), which is useful for providing a fast frontend for SQL. In that use-case, a task that runs on an interval would fetch/calculate datasets from the SQL backend, and do an atomic replace on the datasets the front-end would query.


Further client-side filtering (like greater-than, contains, etc) is available after the data has been fetched (see "Filter Results" below)

My tests have shown that for using equivalent models between flask/mysql and IndexedRedis, a 600% - 1200% performance increase occurs, yet if you design your storage directly as IndexedRedis models, you are able to achieve much higher gains.

It is compatible with python 2.7 and python 3. It has been tested with python 2.7, 3.4, 3.5, 3.6.


5.0 Status
----------

Version 5.0.0 will be backwards incompatible with previous versions by removing some old legacy stuff, and changing some behaviour.

Most of these changes can be made using version 4.1.4 or greater in the 4.1 series, so when 5.0.0 comes around, you can be as close as possible and may not need to update any code.

Details can be found in the 5.0.0 ChangeLog, found here: https://github.com/kata198/indexedredis/blob/5.0branch/Changelog


Automatic and Native Types
--------------------------

Since 4.0, IndexedRedis supports defining fields which will automatically be converted to/from native python types (such as int, float, datetime), as well as anything that can be represented with json (dicts, lists) or objects that support pickling. You just provide the type in its native format, and all the conversion happens behind the scenes. When fetched, the object returned also contains fields in their native types.

IndexedRedis also supports more advanced features such as automatically pickling/unpickling fields, compression/decompression, base64 encoding/decoding, and even defining your own custom field types through a standard interface.

See "Advanced Fields" section below for more information.


API Reference
-------------

Many, but not all methods and types are convered in this document.

For full pydoc reference, see:

https://pythonhosted.org/indexedredis/

or

http://htmlpreview.github.io/?https://github.com/kata198/IndexedRedis/blob/master/doc/IndexedRedis.html?_cache_vers=1

**Below is a quick highlight/overview:**


IndexedRedisModel
-----------------

This is the type you should extend to define your model.


**Example Model:**

	class Song(IndexedRedisModel):

		FIELDS = [ \\

			IRField('artist'),

			IRField('title'),

			IRField('album'),

			IRField('track_number', valueType=int), # Convert automatically to/from int

			IRField('duration', defaultValue='0:00'),

			IRField('releaseDate', valueType=datetime.datetime),  # Convert automatically to/from datetime

			IRField('description'),

			IRField('copyright'),

			IRRawField('mp3_data'), # Don't try to encode/decode data

			IRCompressedField('thumbnail', compressMode='gzip'),      # Compress this field in storage using "gzip" compression

            IRField('tags', valueType=list),

            # "lyrics" will be a utf-8 unicode value on the object, and will be compressed/decompressed to/from storage
            IRFieldChain('lyrics', [ IRUnicodeField(encoding='utf-8'), IRCompressedField() ], defaultValue='No lyrics found' ),

		]


		INDEXED_FIELDS = [ \\
					'artist',

					'title',

					'track_number',

		]

		KEY_NAME = 'Songs'


**Model Attributes:**


*FIELDS* - REQUIRED. A list of string or IRField objects (or their subclasses) which name the fields that can be used for storage. (see "Advanced Fields" section below)

	 Example: [IRField('name'), IRField('description'), IRField('model'), IRFixedPointField('Price', 2), IRField('timestamp', valueType=datetime), IRField('remainingStock', valueType=int)]


*INDEXED_FIELDS* - A list of strings containing the names of fields that will be indexed. Can only filter on indexed fields. Adds insert/delete time. The names listed here must match the name of a field given in FIELDS.

	 Example: ['Name', 'model']


*KEY_NAME* - REQUIRED. A unique name name that represents this model. Think of it like a table name.

	 Example: 'StoreItems'


*REDIS_CONNECTION_PARAMS* - OPTIONAL -  provides the arguments to pass into "redis.Redis", to construct a redis object. Here you should define the host and port.

Since 5.0.0, define this field ONLY for this model to use an alternate connection than the default. See "Connecting To Redis" section below for more info.

If not defined or empty, the default params will be used.


	 Example: {'host' : '192.168.1.1'}


Advanced Fields
---------------

IndexedRedis since version 4.0 allows you to pass elements of type IRField (extends str) in the FIELDS element.

Since 5.0.0, all fields must extend IRField in some way. Those that do not will generate a deprecated warning, and the field will be converted to an IRClassicField (same as IRField, but defaults to empty string instead of irNull).


Doing so allows you to specify certain properties about the field.


Example:

	FIELDS = [ IRField('name'), IRField('age', valueType=int), IRField('birthday', valueType=datetime.datetime) ]

**Field Name**

The first argument is the string of the field name.

**Type**

You can have a value automatically cast to a certain type (which saves a step if you need to filter further through the QueryableList results, like age\_\_gt=15)

by passing that type as "valueType". (e.x.  IRField('age', valueType=int))

If you use "bool", the values 0 and case insensitive string 'false' will result in False, and 1 or 'true' will result in True.

When using floats, consider using IRFixedPointField, which supports indexing and the same representation regardless of platform (unlike "float"). 

floats to work cross-platform. Use a fixed point number as the string type ( like myFixedPoint = '%2.5f' %( 10.12345 ) )

IRField supports "valueType", most other field types deal with a specific type and thus don't have such a parameter.

**NULL Values**

Null values are represented by a static singleton, called "irNull" (of type IRNullType).

For all types except IRClassicField (which has a default of empty string) the default (when unset) value of the field is irNull. This can be changed by passing "defaultValue=somethingElse" to the IRField constructor.

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


**defaultValue**

All fields (except IRClassicField) support a parameter, given when constructing the IRField object, "defaultValue".

For all fields (except IRClassicField), the value of this parameter defaults to "irNull" (see below). For an IRClassicField, the default remains empty string and cannot be changed (to be compatible with plain-string fields pre-5.0.0).


**Advanced Types**

The following are the possible field types, for use within the FIELDS array:


**IRField** - Standard field, takes a name and a "valueType", which is a native python type, or any type you create which implements \_\_new\_\_, taking a signle argument and returning the object. See IndexedRedis/fields/FieldValueTypes for example of how datetime and json are implemented.

When no valueType is defined, str/unicode is the type (same as pre-4.0), and default encoding is used (see set/getDefaultIREncoding functions)

Indexable unless type is a json type or float (use IRFixedPointField to index on floats)


**IRBase64Field** - Converts to and from Base64.

Indexable.


**IRCompressedField** - Automatically compresses before storage and decompresses after retrieval. Argument "compressMode" currently supports "zlib" (default) or "bz2".

Indexsble.


**IRFixedPointField** - A floating-point with a fixed number of decimal places. This type supports indexing using floats, whereas IRField(...valueType=float) does not, as different platforms have different accuracies, roundings, etc. Takes a parameter, decimalPlaces (default 5), to define the precision after the decimal point.

Indexable.


**IRPickleField** - Automaticly pickles the given object before storage, and unpickles after fetch.

Not indexable because different representation between python2 and 3, and potentially system-dependent changes repr


**IRUnicodeField** - Field that takes a parameter, "encoding", to define an encoding to use for this field. Use this to support fields with arbitrary encodings, as IRField will use the default encoding for strings.

Indexable


**IRBytesField** - Field that forces the data to be "bytes", python2 and python3 compatible. If you need python3 only, you can use IRField(valueType=bytes). For no encoding/decoding at all, see IRRawField

Indexable


**IRClassicField** - Field that imitates the behaviour of a plain-string entry in FIELDS pre-5.0.0. This field has a default of empty string, and is always encoded/decoded using the defaultIREncoding

Indexable


**IRRawField** - Field that is not converted in any, to or from Redis. On fetch this will always be "bytes" type (or str in python2). On python3 this is very similar to IRField(...valueType=None), but python2 needs this to store binary data without running into encoding issues.

Not indexable - No decoding


**IRFieldChain** - Chains multiple field types together. Use this, for example, to compress the base64-representation of a value, or to compress utf-16 data. See section below for more details.

Indexable if all chained fields are indexable.


**Chaining Multiple Types**


"Chaining" allows you to apply multiple types on a single field. Say, for example, that you have some utf-16 data that you want to be compressed for storage:

Example:


	FIELDS = [ \

	...

		IRFieldChain( 'longData', [ IRUnicodeField(encoding='utf-16'), IRCompressedField() ] )

	]


An IRFieldChain works similar to a regular IRField, the first parameter is the field name, it has an optional "defaultValue" parameter.

The difference is that the second parameter, *chainedFields*, takes a list of other field types.

When storing, the value is passed through each type in this list, left-to-right.

When fetched, the value retrieved is passed backwards through these chainedFields, right-to-left.

The output of the leftmost (first) element is what defines the type of data that will be found on the object when accessed.

So in the above example, "myObj.longData" would be a utf-16 string. When going to the database, that utf-16 string will be decoded and then compressed for storage. When fetched, it will be decompressed and then converted back into utf-16.


You can specify a defaultValue on an IRFieldChain by providing "defaultValue=X" as an argument to the constructor. If you provide "defaultValue" on any of the fields in the chain list, however, it will be ignored.


**Hash-Lookups (performance)**


If you want to index/search on very large strings/bytes (such as maybe a genome), IndexedRedis supports hashing the key, i.e. the value will be stored as the value itself, but the key reference used for lookup will be a hash of that string.

This increases performance, saves network traffic, and shrinks storage requirements.


To do this, set the "hashIndex" attribute of an IRField to True.

	FIELDS = [ \\

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


Connecting to Redis
-------------------

Your connection to Redis should be defined by calling "setDefaultRedisConnectionParams" with a dict of { 'host' : 'hostname', 'port' : 6379, 'db' : 0 }.

The default connection will connect to host at 127.0.0.1, port at 6379, and db at 0. If you don't define any of these fields explicitly, the default will be used.


These default params will be used for all models, UNLESS you define REDIS\_CONNECTION\_PARAMS on a model to something non-empty, then that model will connect using those params.

If you need the same model to connect to different Redis instances, you can call "MyModel.connectAlt" (where MyModel is your model class) and pass a dict of alternate connection parameters. That function will return a copy of the class that will use the alternate provided connection.


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

    allByAge - Return the objects matching this filter, in order from oldest to newest

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


Client-Side Filtering/Methods
-----------------------------

After you retrieve a bunch of objects from redis (by calling .all(), for example), you get an IRQueryableList of the fetched objects.

This is a smart list, which wraps QueryableList (https://github.com/kata198/QueryableList) and thus allows further filtering using a multitude of more advanced filtering (contains, case-insensitive comparisons, split-filters, etc). See the QueryableList docs for all the available operations.

These operations will act on the objects AFTER FETCH, but are useful because sometimes you need to filter beyond simple equals or not equals, which are the current limits of the Redis backend.

You can chain like:

	# Fetch from Redis all objects where field1 is equal to "something".

	#  Then, client side, filter where csvData is not null AND when split by comma contains "someItem" as an element.

	#  Then, still client side, filter where ( status is in "pending" or "saved" ) OR lastUpdated is less-than or equal to 700 seconds ago.

	#    (Keep in mind to make sure lastUpdated is an IRField(..valueType=int) or float, else you'll be comparing string)


	myObjects = MyModel.objects.filter(field1='something').all().filter(csvData__isnull=False, csvData__splitcontains=("," , "someItem")).filterOr(status__in=('pending', 'saved'), lastUpdated__lte(time.time() - 700))


Some other methods on an IRQueryableList are:

	* **getModel** - Return the model associated with these objects

	* **delete** - Delete all the objects in this list.

		NOTE: It is more efficent to do

			MyModel.objects.filter(...).delete()

		Than to do:

			MyModel.objects.filter(...).all().delete()

		because the latter actually fetches the full objects, then deletes them, whereas the first just deletes the matched items.

		However, sometimes you may want to do additional filtering client-side before deleting, and this supports that.
	
	* **save** - Save all the objects in this list. If these are all existing objects, then only the fields which changed since fetch will be updated.

	* **reload** - Reloads all the objects in this list, inline. This will fetch the most current data from Redis, and apply them on top of the items.

		The return of this function will be a list with the same indexes as the IRQueryableList. The items will be either a KeyError exception (if the item was deleted on the Redis-side), or a dict of fields that were updated, key as the field name, and value as a tuple of (old value, new value)

	* **refetch** - Fetch again all the objects in this list, and return as a new IRQueryableList. Note, this does NOT perform the filter again, but fetches each of the items based on its internal primary key


Sorting
-------

After fetching results, you can sort them by calling .sort_by on the IRQueryableList.

Example:

	myObjs = MyModel.objects.filter(blah='something').all().sort_by('startDate')



Encodings
---------

IndexedRedis will use by default your system default encoding (sys.getdefaultencoding), unless it is ascii in which case it will default to utf-8.

You may change this via IndexedRedis.setDefaultIREncoding.

To get the current default encoding, use IndexedRedis.getDefaultIREncoding


To use a different encoding on a per-field basis, use IRUnicodeField or IRBytesField which both take an "encoding" parameter when constructing, which allows you to have your data follow that encoding.


Backwards-Incompatible Changes
------------------------------

IndexedRedis 5.0.0 introduces several backwards-incompatible changes. See Changelog for details.

https://github.com/kata198/indexedredis/blob/5.0branch/Changelog

Changes
-------

See https://raw.githubusercontent.com/kata198/indexedredis/master/Changelog

Examples
--------


See https://raw.githubusercontent.com/kata198/indexedredis/master/example.py

Also check out

https://github.com/kata198/indexedredis/tree/master/tests/simple

Contact Me
----------

Please e-mail me with any questions, bugs, or even just to tell me that you're using it! kata198@gmail.com
