indexedredis
============

A redis-backed very very fast ORM-style framework that supports indexes (similar to SQL).

Requires a Redis server of at least version 2.6.0, and python-redis [ available at https://pypi.python.org/pypi/redis ]

IndexedRedis supports both “equals” and "not-equals" operators for comparison. It also provides full atomic support for replacing entire datasets (based on model), which is useful for providing a fast frontend for SQL. In that use-case, a task that runs on an interval would fetch/calculate datasets from the SQL backend, and do an atomic replace on the datasets the front-end would query.

If you have ever used Flask or Django you will recognize strong similarities in the filtering interface. 

My tests have shown that for using equivalent models between flask/mysql and IndexedRedis, a 600% - 1200% performance increase occurs. For actually redesigning the system to prefetch and .reset (as mentioned above), response time went from ~3.5s per page load to ~20ms [ 17500% faster ].

It is compatible with python 2.7 and python 3. It has been tested with python 2.7 and 3.4.


IndexedRedisModel
-----------------

	This is the model you should extend.

	Required fields:

	*FIELDS* is a list of strings, which name the fields that can be used for storage.

		 Example: ['Name', 'Description', 'Model', 'Price']

	*INDEXED_FIELDS* is a list of strings containing the names of fields that should be indexed. Every field listed here adds insert performance. To filter on a field, it must be in the INDEXED_FIELDS list.

		 Example: ['Name', 'Price']

	*KEY_NAME* is the name that represents this model. Think of it like a table name.

		 Example 'Items'

	*REDIS_CONNECTION_PARAMS* provides the arguments to pass into "redis.Redis", to construct a redis object.

		 Example: {'host' : '192.168.1.1'}

	An alternative to supplying REDIS_CONNECTION_PARAMS is to supply a class-level variable `_connection`, which contains the redis instance you would like to use. This variable can be created as a class-level override, or set on the model during __init__. 


Usage is like normal ORM

	SomeModel.objects.filter(param1=val).filter(param2=val).all()

	obj = SomeModel(...)
	obj.save()

There is also a powerful method called "reset" which will atomically and locked replace all elements belonging to a model. This is useful for cache-replacement, etc.

	x = [SomeModel(...), SomeModel(..)]

	SomeModel.reset(x)


Filter objects by SomeModel.objects.filter(key=val, key2=val2) and get objects with .all

or for all objects, use SomeModel.objects. (e.x: SomeModel.objects.all() or SomeModel.objects.first())

No objects are fetched until .all() is called. Methods that you can call from a filter include:

	all    - Return all objects matching this filter

	delete - Delete objects matching this filter

	count  - Get the count of objects matching this filter

	first  - Get the oldest record with current filters

	last   - Get the newest record with current filters

	random - Get a random element with current filters

	getPrimaryKeys - Gets primary keys associated with current filters

	filter - Add additional filters, returning a copy of the filter object (moreFiltered = filtered.filter(key2=val2))

	filterInline - Add additional filters to current filter object. 


On SomeModel.objects you can additionally use the following methods:

	get - Get a single object by pk

	getMultiple - Get multiple objects by a list of pks

	filter - Start filtering


Actual objects contain methods including

	save   - Save this object (create if not exist, otherwise update)

	delete - Delete this object

	getUpdatedFields - See changes since last fetch


Other methods and usages are not documented here, see source code or example file for some other usage.


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
