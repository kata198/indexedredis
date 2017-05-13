#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestDiffModels - Test diffing models
#

# vim: set ts=4 sw=4 st=4 expandtab

# Import and apply the properties (like Redis connection parameters) for this test.
import TestProperties

import base64
import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull
from IndexedRedis.compat_str import tobytes
from IndexedRedis.fields import IRField, IRPickleField

# vim: ts=4 sw=4 expandtab

class TestDiffModels(object):
    '''
        TestDiffModels - Test IndexedRedisModel.diff
    '''

    KEEP_DATA = False

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.models = {}


        class Model_General(IndexedRedisModel):
            
            FIELDS = [
                IRField('name'),
                IRField('intVal', valueType=int),
                IRPickleField('pickledData'),
            ]

            INDEXED_FIELDS = ['name']

            KEY_NAME = 'TestDiffModels__Model_General1'

        self.models['GeneralModel'] = Model_General

        class Model_GeneralSub(Model_General):

            KEY_NAME = 'TestDiffModels__Model_GeneralSub1'

        self.models['GeneralSubModel'] = Model_GeneralSub

        class Model_SameFieldsGeneral(IndexedRedisModel):
            
            FIELDS = [
                IRField('name'),
                IRField('intVal', valueType=int),
                IRPickleField('pickledData'),
            ]

            INDEXED_FIELDS = ['name']

            KEY_NAME = 'TestDiffModels__Model_SameFieldsGeneral1'

        self.models['GeneralSameFieldsModel'] = Model_SameFieldsGeneral

        class Model_DifferentFields1(IndexedRedisModel):
            
            FIELDS = [
                IRField('name'),
                IRField('blargie', valueType=int),
                IRField('cheese', valueType=bool),
            ]

            INDEXED_FIELDS = ['name']

            KEY_NAME = 'TestDiffModels__Model_DifferentFields1'

        self.models['DifferentFieldsModel1'] = Model_DifferentFields1

        class Model_DifferentFieldProperty1(IndexedRedisModel):
            
            FIELDS = [
                IRField('name'),
                IRField('intVal', valueType=bool),
                IRPickleField('pickledData'),
            ]

            INDEXED_FIELDS = ['name']

            KEY_NAME = 'TestDiffModels__Model_DifferentFieldProperty1'

        self.models['DifferentFieldsProperty1'] = Model_DifferentFieldProperty1


        # If KEEP_DATA is False (debug flag), then delete all objects before so prior test doesn't interfere
        if self.KEEP_DATA is False and self.models:
            for model in self.models.values():
                model.deleter.destroyModel()

    def teardown_method(self, testMethod):
        '''
            teardown_method - Called after every method.

                If self.model is set, will delete all objects relating to that model. To retain objects for debugging, set TestIRField.KEEP_DATA to True.
        '''

        if self.KEEP_DATA is False and self.models:
            for model in self.models.values():
                model.deleter.destroyModel()



    def test_sameModelDiff(self):
        
        GeneralModel = self.models['GeneralModel']

        pickleableData = ['one', 'two', 'three']

        obj1 = GeneralModel(name='myname', intVal=5, pickledData=pickleableData)

        obj2 = GeneralModel()
        obj2.name = 'myname'
        obj2.intVal = 5
        obj2.pickledData = pickleableData

        diffResults = obj1.diff(obj2)
        assert diffResults == {} , 'Expected two unsaved objects, same values to return blank diff result.\nGot: %s' %(repr(diffResults), )

        try:
            diffResults = IndexedRedisModel.diff(obj1, obj2)
        except Exception as e:
            raise AssertionError('Got exception trying to invoke diff via static ( IndxedRedisModel.diff(obj1, obj2) ).\n%s:   %s' %( e.__class__.__name__, str(e)) )

        assert diffResults == {} ,  'Expected two unsaved objects, same values to return blank diff result (using static invocation).\nGot: %s' %(repr(diffResults), )

        diffResults = obj1.diff(obj2, includeMeta=True)
        assert diffResults == {} , 'Expected with includeMeta=True two unsaved objects have no differences.\nGot: %s' %(repr(diffResults), )

        obj2.intVal = 12

        diffResults = obj1.diff(obj2)

        assert 'intVal' in diffResults , 'Expected after changing intVal, it would show up in diff results.'
        assert list(diffResults.keys()) == ['intVal'] , 'Expected only "intVal" to show up in keys.\nGot: %s' %(repr(list(diffResults.keys())), )
        assert diffResults['intVal'] == (5, 12) , 'Expected diffResults["intVal"] to contain (before, after).\nGot: %s' %(repr(diffResults['intVal']), )

        assert IndexedRedisModel.diff(obj1, obj2) == diffResults , 'Expected static invocation to return same results as instance call'

        ids = obj1.save()
        assert ids and ids[0] , 'Failed to save object'
        ids = obj2.save()
        assert ids and ids[0] , 'Failed to save object'

        diffResults = obj1.diff(obj2, includeMeta=True)

        diffResultsKeys = list(diffResults.keys())
        assert len(diffResultsKeys) == 2 , 'Expected to have two items in diff'
        assert '_id' in diffResultsKeys , 'Expected after save includeMeta=True to include "_id" in diffs'
        assert 'intVal' in diffResultsKeys , 'Expected after save for "intVal" to be in diffs.'

        expectedIds = ( obj1.getPk(), obj2.getPk() )
        assert diffResults['_id'] == expectedIds , 'Expected "_id" to contain first and second id.\n\nExpected: %s\n\nGot:     %s\n' %(repr(expectedIds), repr(diffResultsKeys['_id'])) 

        expectedIntVals = (5, 12)
        assert diffResults['intVal'] == expectedIntVals , 'Expected "intVal" to contain the first and second intVals.\n\nExpected: %s\n\nGot:     %s\n' %( repr(expectedIntVals), repr(diffResults['intVal']) )

        diffResults = obj2.diff(obj1)

        assert diffResults['intVal'] == (12, 5) , 'Expected comparing obj2 to obj1 switches order.'

        obj1.name = 'Becky'

        diffResults = obj1.diff(obj2)

        assert 'name' in diffResults , 'Expected after changing "name" for it to show up in diffs'

        assert diffResults['name'] == ('Becky', 'myname') , 'Expected changing "name" to show up in diffs'
        assert diffResults['intVal'] == expectedIntVals , 'Expected "intVal" to contain the first and second intVals.\n\nExpected: %s\n\nGot:     %s\n' %( repr(expectedIntVals), repr(diffResults['intVal']) )


    # TODO: Do other tests ( inherited model, different model, etc )


if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
