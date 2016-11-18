#!/usr/bin/env python

# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestSimpleSetAndGet - GoodTests unit tests validating model validation
#

# vim: set ts=4 sw=4 expandtab

import sys
import IndexedRedis
import subprocess
from IndexedRedis import IndexedRedisModel, IRField, InvalidModelException, validatedModels

# vim: ts=4 sw=4 expandtab

class SimpleSetAndGetModel(IndexedRedisModel):
    
    FIELDS = ['a', 'b', 'c']

    INDEXED_FIELDS = ['a']

    KEY_NAME = 'Test_SimpleSetAndGet'

class TestSimpleSetAndGet(object):


    def __init__(self):
        self.toDelete = []

    def setup_class(self):
        SimpleSetAndGetModel.objects.delete()

    def test_createAndFetch(self):
        myObj = SimpleSetAndGetModel(a='one', b='two', c='three')
        ids = myObj.save()

        assert ids, 'Expected to get ids returned from save, but did not.'
        assert ids[0] == myObj._id , 'Expected id to be set on saved object, but was not.'

        fetchObj = SimpleSetAndGetModel.objects.get(ids[0])
        assert fetchObj, 'Expected to get an object returned for .get on same id as saved.'
        assert fetchObj._id == ids[0], 'ID on fetched object not same as we requested.'

        assert fetchObj.a == 'one', 'Field "a" does not have correct value'
        assert fetchObj.b == 'two', 'Field "b" does not have correct value'
        assert fetchObj.c == 'three', 'Field "c" does not have correct value'

        self.toDelete.append(fetchObj)

        fetchObj.delete()

        fetchObj = SimpleSetAndGetModel.objects.get(ids[0])
        assert not fetchObj, 'Deleted object and was still able to fetch it.'

    def test_filter(self):
        myObj = SimpleSetAndGetModel(a='one', b='two', c='three')
        ids1 = myObj.save()

        assert ids1, 'Failed to save new object.'
        self.toDelete.append(myObj)


        myObj2 = SimpleSetAndGetModel(a='aplus', b='bplus', c='cplus')
        ids2 = myObj2.save()
        self.toDelete.append(myObj2)

        assert ids2, 'Failed to save new object.'

        myObj3 = SimpleSetAndGetModel(a='aplus', b='bminus', c='cplus')
        ids3 = myObj3.save()
        self.toDelete.append(myObj3)

        assert ids3, 'Failed to save new object.'

        getOne = SimpleSetAndGetModel.objects.filter(a='one').all()

        assert len(getOne) == 1, 'Expected to get one object, got %d' %(len(getOne),)
        assert getOne[0]._id == ids1[0] , 'Got wrong object. Expected id=%s, got id=%d' %(ids1[0], getOne[0]._id)
        assert getOne[0].a == 'one', 'Got wrong object, expected a="one" got a="%s"' %(getOne[0].a,)
        assert getOne[0].b == 'two', 'Got wrong object, expected b="two" got b="%s"' %(getOne[0].b,)
        assert getOne[0].c == 'three', 'Got wrong object, expected c="three" got c="%s"' %(getOne[0].c,)

        getTwo = SimpleSetAndGetModel.objects.filter(a='aplus').all()
        
        assert len(getTwo) == 2, 'Expected to get two objects, got %d' %(len(getTwo),)
        assert getTwo[0]._id in (ids2 + ids3), 'Got wrong object. Expected id in %s got id=%d' %(str(ids2 + ids3), getTwo[0]._id)
        assert getTwo[1]._id in (ids2 + ids3), 'Got wrong object. Expected id in %s got id=%d' %(str(ids2 + ids3), getTwo[1]._id)

        assert getTwo[0].a == 'aplus', 'Field wrong on returned object.'

    def teardown_method(self, *args, **kwargs):
        for obj in self.toDelete:
            try:
                obj.delete()
            except:
                sys.stderr.write('Failed to delete object: %s\n' %(str(obj.asDict(True),)))



            
if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py "%s"' %(sys.argv[0],), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
