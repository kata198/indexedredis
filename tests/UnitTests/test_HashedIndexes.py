#!/usr/bin/env python

# Copyright (c) 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# test_HashedIndexes - GoodTests unit tests Hashed Indexes
#

# vim: set ts=4 sw=4 expandtab

import datetime

import sys
import IndexedRedis
import subprocess
import re
from IndexedRedis import IndexedRedisModel, IRField, irNull
from IndexedRedis.fields.FieldValueTypes import IRDatetimeValue, IRJsonValue

# vim: ts=4 sw=4 expandtab

# TODO: Add test for nulls and hashed indexes, and various other object types.
#   Right now IRField directly is the only way to get a hashed index, but may open that up.

class TestHashedIndexes(object):
    '''
        TestHashedIndexes - Test some basic IRField stuff
    '''

    KEEP_DATA = False

    def __init__(self):
        self.models = []

        MD5_DIGEST_LENGTH = 32

        self.hashRE = re.compile("^[a-fA-F0-9]{%d}$" %(MD5_DIGEST_LENGTH,))

    
    def _isHashed(self, val):
        return bool(self.hashRE.match(val))


    def teardown_method(self, testMethod):
        if self.KEEP_DATA is False:
            for model in self.models:
                try:
                    model.deleter.destroyModel()
                except Exception as e:
                    sys.stderr.write('Warning: Error deleting all objects belonging to %s (%s):\n%s%s\n' %(model.__class__.__name__, model.KEY_NAME, str(type(e)), str(e)) )

        self.models = []

    def test_simpleIndexedSetAndFetch(self):
        class HashedIndexMdl1(IndexedRedisModel):
            FIELDS = [ IRField('name'), IRField('value', hashIndex=True) ]

            INDEXED_FIELDS = ['name', 'value']

            KEY_NAME = 'Test_HashedIndexMdl1'

        self.models.append(HashedIndexMdl1)

        myObj = HashedIndexMdl1(name='Tim', value='purple')
        ids = myObj.save()

        assert ids, 'Expected to get ids returned from save, but did not.'
        assert ids[0] == myObj._id , 'Expected id to be set on saved object, but was not.'

        # Test that we did hash the index, and the value remains unchanged.
        myObjDictForStorage = myObj.asDict(forStorage=True)
        assert myObjDictForStorage['value'] == myObj.value, 'Expected hashed value for storage to match direct-access on object. Storage=%s%s direct=%s%s' %(str(type(myObjDictForStorage['value'])), str(myObjDictForStorage['value']), str(type(myObj.value)), str(myObj.value))
        
        assert not self._isHashed(myObj.value) , 'Expected value to not be hashed directly on the object.'
        assert not self._isHashed(myObjDictForStorage['value']) , 'Expected value not to be hashed in storage dict'

        # XXX: Remember, has to pass the complex field, not just the type name. 
        #   Maybe the function should support lookups, but it's marked "internal"
        #   so I think better to keep that assumption optimized
#        indexValue = myObj.objects._get_key_for_index('value', myObj.value)
        indexValue = myObj.objects._get_key_for_index(HashedIndexMdl1.FIELDS[1], myObj.value)
        assert ':' in indexValue , 'Expected indexed value to have a colon. Got: "%s"' %(indexValue,)

        hashValue = indexValue[indexValue.rfind(':')+1:]
        assert self._isHashed(hashValue) , 'Expected hashIndex=True value to have a hashed index. Got: "%s"' %(hashValue,)

        # Remainder is general test copied from elsewhere, just to ensure it works with hashed index
        myObj2 = HashedIndexMdl1(name='Joe', value='blue')
        ids2 = myObj2.save()

        assert ids2, 'Expected to get ids returned from save, but did not.'
        assert ids2[0] == myObj2._id , 'Expected id to be set on saved object, but was not.'

        fetchObj = HashedIndexMdl1.objects.get(ids[0])
        assert fetchObj, 'Expected to get an object returned for .get on same id as saved.'
        assert fetchObj._id == ids[0], 'ID on fetched object not same as we requested.'

        assert fetchObj.name == 'Tim', 'Field "name" does not have correct value. Expected "%s", got "%s"' %('Tim', str(fetchObj.name))
        assert fetchObj.value == 'purple', 'Field "value" does not have correct value'

        fetchObjs2 = HashedIndexMdl1.objects.filter(value='blue').all()

        assert len(fetchObjs2) == 1, 'Expected to get one object back for value="blue", got %d' %(len(fetchObjs2),)
        assert (fetchObjs2[0].name == 'Joe' and fetchObjs2[0].value == 'blue'), 'Got wrong values back on filter'

        assert fetchObj.delete() == 1, 'Expected delete on fetched object to return 1'

        fetchObj = HashedIndexMdl1.objects.get(ids[0])
        assert fetchObj is None, 'Expected object to not be present after deleting, but it was.'


    def test_compat_reindexHashed(self):
        '''
            Test that the compat method does rehash correctly
        '''

        class HashedIdxMdlForReindex(IndexedRedisModel):
            FIELDS = [ IRField('name'), IRField('value', hashIndex=True) ]

            INDEXED_FIELDS = ['name', 'value']

            KEY_NAME = 'Test_HashedIndexMdlForReindex'

        class UnHashedIdxMdlForReindex(IndexedRedisModel):
            FIELDS = [ IRField('name'), IRField('value', hashIndex=False) ]

            INDEXED_FIELDS = ['name', 'value']

            KEY_NAME = 'Test_HashedIndexMdlForReindex'

        self.models.append(HashedIdxMdlForReindex)
        self.models.append(UnHashedIdxMdlForReindex)

        # Test both with fetchAll=True and fetchAll=False (i.e. fetch all beforehand, fetch one-at-a-time.
        for fetchAll in (True, False):
            prefixStr = "compat_convertHashedIndexes(fetchAll=%s)" %(str(fetchAll), )

            HashedIdxMdlForReindex.objects.delete()
            UnHashedIdxMdlForReindex.objects.delete()

            # Start with same model but one has hash, one does not.
            #  First, save the value as a hash
            myObj = HashedIdxMdlForReindex(name='Tim', value='purple')
            ids = myObj.save()

            otherObj = HashedIdxMdlForReindex(name='George', value='nurple')

            assert ids , 'Failed to save myObj'

            filterResults = HashedIdxMdlForReindex.objects.filter(value='purple').all()
            assert len(filterResults) == 1 , prefixStr + 'Expected to get object off filter, but did not'

            filterResults = UnHashedIdxMdlForReindex.objects.filter(value='purple').all()
            assert len(filterResults) == 0, prefixStr + 'Expected to not get objects without using hash filter'

            filterResults = UnHashedIdxMdlForReindex.objects.filter(name='Tim').all()
            assert len(filterResults) == 1, prefixStr + 'Expected to be able to filter using either model on field that does not change.'

            filterResults = HashedIdxMdlForReindex.objects.filter(name='Tim').all()
            assert len(filterResults) == 1, prefixStr + 'Expected to be able to filter using either model on field that does not change.'

            # Now, reindex using the unhashed model. This should flip everythng.
            UnHashedIdxMdlForReindex.objects.compat_convertHashedIndexes(fetchAll)

            filterResults = UnHashedIdxMdlForReindex.objects.filter(value='purple').all()
            assert len(filterResults) == 1, prefixStr + 'Expected to get object after reindexing without hash'

            filterResults = HashedIdxMdlForReindex.objects.filter(value='purple').all()
            assert len(filterResults) == 0, prefixStr + 'Expected to not get object using hash search without hashed index'

            filterResults = UnHashedIdxMdlForReindex.objects.filter(name='Tim').all()
            assert len(filterResults) == 1, prefixStr + 'Expected to be able to filter using either model on field that does not change.'

            filterResults = HashedIdxMdlForReindex.objects.filter(name='Tim').all()
            assert len(filterResults) == 1, prefixStr + 'Expected to be able to filter using either model on field that does not change.'


            # Now, flip back to hashed and perform same tests

            HashedIdxMdlForReindex.objects.compat_convertHashedIndexes(fetchAll)

            filterResults = UnHashedIdxMdlForReindex.objects.filter(value='purple').all()
            assert len(filterResults) == 0, prefixStr + 'Expected to not get object after reindexing with hash'

            filterResults = HashedIdxMdlForReindex.objects.filter(value='purple').all()
            assert len(filterResults) == 1, prefixStr + 'Expected to get object using hash search with hashed index'

            filterResults = UnHashedIdxMdlForReindex.objects.filter(name='Tim').all()
            assert len(filterResults) == 1, prefixStr + 'Expected to be able to filter using either model on field that does not change.'

            filterResults = HashedIdxMdlForReindex.objects.filter(name='Tim').all()
            assert len(filterResults) == 1, prefixStr + 'Expected to be able to filter using either model on field that does not change.'


if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py "%s"' %(sys.argv[0],), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
