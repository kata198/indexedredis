#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestCopyModel - Copy Model test
#

# vim: set ts=4 sw=4 expandtab

# Import and apply the properties (like Redis connection parameters) for this test.
import TestProperties

import copy
import sys
import subprocess
from IndexedRedis import IndexedRedisModel, IRField, InvalidModelException, validatedModels
from IndexedRedis.fields import IRPickleField

# vim: ts=4 sw=4 expandtab

class TestCopyModel(object):

    KEEP_DATA = False

    def setup_method(self, testMethod):
     
        self.model = None

        if testMethod == self.test_copyModel:
            class TestCopyModel_CopyModel(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRField('num', valueType=int, defaultValue=3),
                ]

                INDEXED_FIELDS = ['num']

                KEY_NAME = 'IRTestCopyModel__CopyModel'
            
            self.model = TestCopyModel_CopyModel

        elif testMethod in (self.test_copyInstance, self.test_deepcopyInstance):
            class TestCopyModel_CopyInstance(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRPickleField('tags'),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'IRTestCopyModel__CopyInstance'

            self.model = TestCopyModel_CopyInstance

        # If KEEP_DATA is False (debug flag), then delete all objects before so prior test doesn't interfere
        if self.KEEP_DATA is False and self.model:
            self.model.deleter.destroyModel()

    def teardown_method(self, testMethod):
        '''
            teardown_method - Called after every method.

                If self.model is set, will delete all objects relating to that model. To retain objects for debugging, set TestIRField.KEEP_DATA to True.
        '''

        if self.model and self.KEEP_DATA is False:
            self.model.deleter.destroyModel()


    def test_copyModel(self):

        Model = self.model

        obj = Model()

        assert obj.num == 3 , 'Checking that original defaultValue=3 is applied'

        ModelCopy = Model.copyModel()

        assert id(Model) != id(ModelCopy) , 'Expected copy of model not to have same id'
        assert Model.__name__ != ModelCopy.__name__ , 'Expected copy of model to have different name'

        assert id(Model.INDEXED_FIELDS) != id(ModelCopy.INDEXED_FIELDS) , 'Expected INDEXED_FIELDS to have different id on copied model'

        assert id(Model.FIELDS) != id(ModelCopy.FIELDS) , 'Expected FIELDS to have different id on copied model'

        assert id(Model.FIELDS[0]) != id(ModelCopy.FIELDS[0]) , 'Expected individual entries in FIELDS to have different id in copy'

        assert ModelCopy.INDEXED_FIELDS == ['num'] , 'Expected INDEXED_FIELDS data to be copied'

        assert ModelCopy.KEY_NAME == Model.KEY_NAME , 'Expected KEY_NAME to be the same between original and copy'

        ModelCopy.FIELDS['num'].defaultValue = 17

        obj2 = ModelCopy()

        assert obj2.num == 17 , 'Expected after changing num.defaultValue to 17 on ModelCopy, that instances of ModelCopy get that default'

        obj = Model()

        assert obj.num == 3 , 'Expected after changing num.defaultValue to 17 on ModelCopy, that instances of Model get the original default'

        
        obj.name = 'm1'
        obj2.name = 'm2'

        ids = obj.save()
        assert ids and ids[0] , 'Failed to save on original model'
        ids = obj2.save()
        assert ids and ids[0] , 'Failed to save on copied model'

        objFetched1 = Model.objects.filter(num=17).first()

        assert objFetched1 , 'Expected to be able to fetch object saved on copy with original'

        objFetched2 = ModelCopy.objects.filter(num=3).first()

        assert objFetched2 , 'Expected to be able to fetch object saved on original with copy'


    def test_copyInstance(self):
 
        Model = self.model

        x = Model(name='one', tags=['one', 'two'])

        xcpy = copy.copy(x)

        assert x.hasSameValues(xcpy) , 'Expected hasSameValues to be True on a copy.copy'

        assert not xcpy._id  , 'Expecteed copy.copy not to be linked to the database'

        linkedCopy = x.copy(True)

        assert linkedCopy.hasSameValues(x) , 'Expected hasSameValues to be True on a copy(True)'
        assert linkedCopy._id == x._id , 'Expected id to be copied with copy(True)'

        assert id(linkedCopy.tags) == id(x.tags) , 'Expected copy(copyValues=False) to retain same reference on a list'

        ids = x.save()
        assert ids and ids[0] , 'Failed to save model'

        fetchedObj = Model.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'


        obj = fetchedObj

        objCopy = copy.copy(fetchedObj)

        assert objCopy.hasSameValues(obj) , 'Expected after fetch copy to have same values as original'

        assert id(obj.tags) == id(objCopy.tags) , 'Expected copy.copy to not deepcopy the values, so a list copied should share same reference.'

    def test_deepcopyInstance(self):
        Model = self.model

        x = Model(name='one', tags=['one', 'two'])

        xcpy = copy.deepcopy(x)

        assert x.hasSameValues(xcpy) , 'Expected hasSameValues to be True on a copy.deepcopy'

        assert not xcpy._id  , 'Expecteed copy.deepcopy not to be linked to the database'

        linkedCopy = x.copy(True, copyValues=True)

        assert linkedCopy.hasSameValues(x) , 'Expected hasSameValues to be True on a copy(True, True)'
        assert linkedCopy._id == x._id , 'Expected id to be copied with copy(True, True)'
        assert id(linkedCopy.tags) != id(x.tags) , 'Expected copy(copyValues=True) to NOT retain same reference on a list'
        assert linkedCopy.tags == x.tags , 'Expected list to contain same values with copy(copyValues=True)'

        ids = x.save()
        assert ids and ids[0] , 'Failed to save model'

        fetchedObj = Model.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'


        obj = fetchedObj

        objCopy = copy.deepcopy(fetchedObj)

        assert objCopy.hasSameValues(obj) , 'Expected after fetch copy to have same values as original'

        assert id(obj.tags) != id(objCopy.tags) , 'Expected copy.deepcopy to deepcopy the values, so a list copied should share same reference.'

            
if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
