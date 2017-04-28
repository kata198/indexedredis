'''
    TestProperties - Set properties that will be used by the unit tests
'''

REDIS_CONNECTION_PARAMS = { 'host' : '127.0.0.1', 'port' : 6379, 'db' : 0 }

# Use a function to keep namespace clean
def initProperties():

    try:
        from IndexedRedis import setDefaultRedisConnectionParams, getRedisPool
    except:
        raise Exception('Cannot import IndexedRedis. Ensure that it is installed, or use runTests.py to execute using the version in the source dir (non-site install).')

    from redis import Redis


    setDefaultRedisConnectionParams(REDIS_CONNECTION_PARAMS)

    try:
        _pool = getRedisPool(REDIS_CONNECTION_PARAMS)

        r = Redis(connection_pool=_pool)

        r.info()
    except:
        raise Exception('Cannot connect to Redis using: %s. Please set connection info in TestProperties.py and ensure that Redis is running.')

initProperties()
