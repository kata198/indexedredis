#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRForeignLinkField - Test default values for fields
#

# vim: set ts=4 sw=4 st=4 expandtab

# Import and apply the properties (like Redis connection parameters) for this test.
import TestProperties

import base64
import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull
from IndexedRedis.compat_str import tobytes
from IndexedRedis.fields import IRForeignLinkField, IRField, IRForeignLinkField

# vim: ts=4 sw=4 expandtab

class TestIRForeignLinkField(object):
    '''
        TestIRForeignLinkField - Test base64 field
    '''

    KEEP_DATA = False

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.models = {}

        class Model_RefedModel(IndexedRedisModel):

            FIELDS = [
                IRField('name'),
                IRField('strVal'),
                IRField('intVal', valueType=int)
            ]

            INDEXED_FIELDS = ['name']

            KEY_NAME = 'TestIRForeignLinkField__RefedModel1'

        self.models['RefedModel'] = Model_RefedModel

        class Model_MainModel(IndexedRedisModel):
            
            FIELDS = [
                IRField('name'),
                IRField('value'),
                IRForeignLinkField('other', Model_RefedModel),
            ]

            INDEXED_FIELDS = ['name']

            KEY_NAME='TestIRForeignLinkField__MainModel1'

        self.models['MainModel'] = Model_MainModel

        if testMethod == self.test_filterOnModel:
            class Model_MainModelIndexed(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRField('value'),
                    IRForeignLinkField('other', Model_RefedModel),
                ]

                INDEXED_FIELDS = ['name', 'other']

                KEY_NAME='TestIRForeignLinkField__MainModelIndexed1'

            self.models['MainModel'] = Model_MainModelIndexed

        if testMethod == self.test_cascadeSave:
            class Model_PreMainModel(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRField('value'),
                    IRForeignLinkField('main', Model_MainModel),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRForeignLinkField__PreMainModel1'

            self.models['PreMainModel'] = Model_PreMainModel


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


    def test_general(self):
        
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        refObj = RefedModel(name='rone', strVal='hello', intVal=1)
        ids = refObj.save()
        assert ids and ids[0]

        mainObj = MainModel(name='one', value='cheese', other=ids[0])

        mainObj.save()

        assert isinstance(mainObj.other, RefedModel) , 'Expected access of object to return object'

        assert mainObj.other__id == ids[0] , 'Expected __id access to return the object\'s id.'

        fetchedObj = MainModel.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'

        assert isinstance(fetchedObj.other, RefedModel) , 'After save-and-fetch, expected access of object to return object'

        assert fetchedObj.other__id == ids[0] , 'After save-and-fetch, expected __id access to return the object\'s id.'



    def test_assign(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)
        refObj2 = RefedModel(name='rtwo', strVal='world', intVal=2)

        ids1 = refObj1.save()
        assert ids1 and ids1[0] , 'Failed to save object'

        ids2 = refObj2.save()
        assert ids2 and ids2[0] , 'Failed to save object'

        mainObj = MainModel(name='one', value='cheese', other=ids1[0])

        assert mainObj.other.hasSameValues(refObj1) , 'Expected other with id of refObj1 to link to refObj1'

        mainObj.other = ids2[0]

        assert mainObj.other.hasSameValues(refObj2) , 'Expected other with id of refObj2 to link to refObj2'

        ids = mainObj.save()
        assert ids and ids[0] , 'Failed to save object'

        fetchedObj = mainObj.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'

        assert fetchedObj.other__id == ids2[0] , 'Expected __id access to return the object\'s id.'


        mainObj = fetchedObj

        firstRefObj = RefedModel.objects.filter(name='rone').first()

        assert firstRefObj , 'Failed to fetch object'

        mainObj.other = firstRefObj

        ids = mainObj.save()
        assert ids and ids[0] , 'Failed to save'

        fetchedObj = mainObj.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'

        assert fetchedObj.other__id == ids1[0] , 'Expected save using Model object would work properly. Did not fetch correct id after save.'
        
    def test_filterOnModel(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)
        refObj2 = RefedModel(name='rtwo', strVal='world', intVal=2)

        ids1 = refObj1.save()
        assert ids1 and ids1[0] , 'Failed to save object'

        ids2 = refObj2.save()
        assert ids2 and ids2[0] , 'Failed to save object'

        mainObj = MainModel(name='one', value='cheese', other=ids1[0])

        assert object.__getattribute__(mainObj, 'other').isFetched() is False , 'Expected object not to be fetched before access'

        assert mainObj.other.hasSameValues(refObj1) , 'Expected other with id of refObj1 to link to refObj1'

        assert object.__getattribute__(mainObj, 'other').isFetched() is True, 'Expected object to be fetched after access'
        mainObj.other = ids2[0]

        assert mainObj.other.hasSameValues(refObj2) , 'Expected other with id of refObj2 to link to refObj2'

        ids = mainObj.save()

        fetchedObjs = MainModel.objects.filter(other=ids2[0]).all()

        assert fetchedObjs and len(fetchedObjs) == 1 , 'Expected to be able to filter on numeric pk'


    def test_cascadeSave(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']
        PreMainModel = self.models['PreMainModel']

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)

        mainObj = MainModel(name='one', value='cheese')

        mainObj.other = refObj1

        ids = mainObj.save(cascadeSave=True)

        assert ids and ids[0] , 'Failed to save object'

        obj = MainModel.objects.filter(name='one').first()

        assert obj , 'Failed to fetch object by name'

        assert obj.other , 'Did not cascade save second object and link to parent'

        assert obj.other.name == 'rone' , 'Did save values on cascaded object'

        RefedModel.deleter.destroyModel()
        MainModel.deleter.destroyModel()

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)
        mainObj = MainModel(name='one', value='cheese')

        mainObj.other = refObj1

        preMainObj = PreMainModel(name='pone', value='bologna')

        preMainObj.main = mainObj

        ids = preMainObj.save(cascadeSave=True)

        assert ids and ids[0] , 'Failed to save object'


        obj = PreMainModel.objects.filter(name='pone').first()

        assert obj , 'Failed to fetch object by name'

        assert obj.main , 'Failed to link one level down'
        assert obj.main.name == 'one' , 'Did not save values one level down'

        assert obj.main.other , 'Failed to link two levels down'
        assert obj.main.other.name == 'rone' , 'Failed to save values two levels down'




if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
