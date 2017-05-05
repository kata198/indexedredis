#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRForeignMultiLinkField - Test default values for fields
#

# vim: set ts=4 sw=4 st=4 expandtab

# Import and apply the properties (like Redis connection parameters) for this test.
import TestProperties

import base64
import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull
from IndexedRedis.compat_str import tobytes
from IndexedRedis.fields import IRForeignMultiLinkField, IRField, IRForeignMultiLinkField

# vim: ts=4 sw=4 expandtab

class TestIRForeignMultiLinkField(object):
    '''
        TestIRForeignMultiLinkField - Test base64 field
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

            KEY_NAME = 'TestIRForeignMultiLinkField__RefedModel1'

        self.models['RefedModel'] = Model_RefedModel

        class Model_MainModel(IndexedRedisModel):
            
            FIELDS = [
                IRField('name'),
                IRField('value'),
                IRForeignMultiLinkField('other', Model_RefedModel),
            ]

            INDEXED_FIELDS = ['name']

            KEY_NAME='TestIRForeignMultiLinkField__MainModel1'

        self.models['MainModel'] = Model_MainModel

        if testMethod in (self.test_cascadeSave, self.test_cascadeFetch):
            class Model_PreMainModel(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRField('value'),
                    IRForeignMultiLinkField('main', Model_MainModel),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRForeignMultiLinkField__PreMainModel1'

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


    def test_single(self):
        
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        refObj = RefedModel(name='rone', strVal='hello', intVal=1)
        ids = refObj.save(cascadeSave=False)
        assert ids and ids[0]

        mainObj = MainModel(name='one', value='cheese', other=[ids[0]])

        mainObj.save(cascadeSave=False)

        assert len(mainObj.other) == 1 , 'Expected to have a list of one object'

        otherObj = mainObj.other[0]

        assert isinstance(otherObj, RefedModel) , 'Expected access of object to return object'

        fetchedObj = MainModel.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'

        assert isinstance(fetchedObj.other, list) , 'Expected fetch to return a list'

        assert len(fetchedObj.other) == 1 , 'Expected to get one element'

        otherObj = fetchedObj.other[0]

        assert isinstance(otherObj, RefedModel ) , 'After save-and-fetch, expected access of object to return object'


    def test_disconnectAssociation(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        refObj1 = refObj = RefedModel(name='rone', strVal='hello', intVal=1)
        refObj2 = RefedModel(name='rtwo', strVal='goodbye', intVal=2)
        refObj3 = RefedModel(name='rthree', strVal='buh bai', intVal=3)
        
        ids = refObj.save(cascadeSave=False)
        assert ids and ids[0]

        refObj2.save()
        refObj3.save()

        mainObj = MainModel(name='one', value='cheese', other=[ids[0]])

        for nullType in (None, irNull):
            mainObj.other = [ids[0]]
            mainObj.save()
            mainObj = MainModel.objects.filter(name='one').first()

            assert mainObj.other , 'Expected bool(other) to be evaluated as True after setting as an item'

            mainObj = MainModel.objects.filter(name='one').first()
            mainObj.other = nullType
            assert not mainObj.other , 'Expected bool(other) to be False after setting to ' + str(nullType)
            mainObj.save(cascadeSave=False)

            mainObj = MainModel.objects.filter(name='one').first()

            assert not mainObj.other , 'Expected other to be False after saving as ' + str(nullType)


        mainObj.other = [refObj3, refObj1, refObj2._id]

        assert refObj2.hasSameValues(mainObj.other[2]) , 'Expected after setting to an integer, access would fetch.'

        mainObj.save()

        mainObj.other = mainObj.other[ : 1] + mainObj.other[2 : ]

        mainObj.save()

        mainObj = MainModel.objects.filter(name='one').first()

        assert len(mainObj.other) == 2 , 'Expected  only two items after removing middle item in 3-item list. Got:  %s' %(repr(mainObj.other), )

        assert refObj3.hasSameValues(mainObj.other[0]) , 'Expected order to be retained when one item removed from list'
        assert refObj2.hasSameValues(mainObj.other[1]) , 'Expected order to be retained when one item removed from list'


#        mainObj.other = [refObj3, refObj1, refObj2._id]
#        mainObj.save()
#
#        mainObj = MainModel.objects.filter(name='one').first()
#
#        mainObj.other[1] = None
#
#        assert True
#        assert True
        


    def test_cascadeFetch(self):
        
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']
        PreMainModel = self.models['PreMainModel']

        refObj = RefedModel(name='rone', strVal='hello', intVal=1)
        ids = refObj.save(cascadeSave=False)
        assert ids and ids[0]

        mainObj = MainModel(name='one', value='cheese', other=[ids[0]])

        ids = mainObj.save(cascadeSave=False)
        assert ids and ids[0] , 'Failed to save object'

        preMainObj = PreMainModel(name='pone', value='bologna')
        preMainObj.main = [mainObj]

        ids = preMainObj.save(cascadeSave=False)
        assert ids and ids[0], 'Failed to save object'

        objs = PreMainModel.objects.filter(name='pone').all(cascadeFetch=True)

        assert objs and len(objs) == 1 , 'Failed to fetch single PreMainModel object'

        obj = objs[0]

        oga = object.__getattribute__

        assert oga(obj, 'main').isFetched() is True , 'Expected cascadeFetch to fetch sub object. Failed one level down (not marked isFetched)'

        assert oga(obj, 'main').obj and isinstance(oga(obj, 'main').obj[0], MainModel) , 'Expected cascadeFetch to fetch sub object. Failed one level down (object not present)'

        mainObj = oga(obj, 'main').obj[0]

        assert oga(mainObj, 'other').isFetched() is True , 'Expected cascadeFetch to fetch sub object. Failed two levels down (not marked isFetched)'
        assert oga(mainObj, 'other').obj and isinstance(oga(mainObj, 'other').obj[0], RefedModel) , 'Expected cascadeFetch to fetch sub object. Failed to levels down (object not present)'

        assert oga(mainObj, 'other').obj[0].name == 'rone' , 'Missing values on two-level-down fetched object.'

        MainModel.deleter.destroyModel()
        RefedModel.deleter.destroyModel()
        PreMainModel.deleter.destroyModel()

        # Now test that cascadeFetch=False does NOT fetch the subs.
        refObj = RefedModel(name='rone', strVal='hello', intVal=1)
        ids = refObj.save(cascadeSave=False)
        assert ids and ids[0]

        mainObj = MainModel(name='one', value='cheese', other=[ids[0]])

        ids = mainObj.save(cascadeSave=False)
        assert ids and ids[0] , 'Failed to save object'

        preMainObj = PreMainModel(name='pone', value='bologna')
        preMainObj.main = [mainObj]

        ids = preMainObj.save(cascadeSave=False)
        assert ids and ids[0], 'Failed to save object'

        objs = PreMainModel.objects.filter(name='pone').all(cascadeFetch=False)

        assert objs and len(objs) == 1 , 'Failed to fetch objects'

        obj = objs[0]

        assert oga(obj, 'main').isFetched() is False , 'Expected cascadeFetch=False to NOT automatically fetch sub object. isFetched is marked True one level down.'

        # Now try fetching with cascadeFetch=False, then calling Model.cascadeFetch() to perform it

        objs = PreMainModel.objects.filter(name='pone').all(cascadeFetch=False)

        assert objs and len(objs) == 1 , 'Failed to fetch single PreMainModel object'

        obj = objs[0]

        obj.cascadeFetch()

        assert oga(obj, 'main').isFetched() is True , 'Expected Model.cascadeFetch to fetch sub object. Failed one level down (not marked isFetched)'

        assert oga(obj, 'main').obj and isinstance(oga(obj, 'main').obj[0], MainModel) , 'Expected Model.cascadeFetch to fetch sub object. Failed one level down (object not present)'

        mainObj = oga(obj, 'main').obj[0]

        assert oga(mainObj, 'other').isFetched() is True , 'Expected Model.cascadeFetch to fetch sub object. Failed two levels down (not marked isFetched)'
        assert oga(mainObj, 'other').obj and isinstance(oga(mainObj, 'other').obj[0], RefedModel) , 'Expected Model.cascadeFetch to fetch sub object. Failed to levels down (object not present)'

        assert oga(mainObj, 'other').obj[0].name == 'rone' , 'Missing values on two-level-down fetched object.'


    def test_assign(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)
        refObj2 = RefedModel(name='rtwo', strVal='world', intVal=2)

        ids1 = refObj1.save(cascadeSave=False)
        assert ids1 and ids1[0] , 'Failed to save object'

        ids2 = refObj2.save(cascadeSave=False)
        assert ids2 and ids2[0] , 'Failed to save object'

        mainObj = MainModel(name='one', value='cheese', other=[ids1[0]])
        mainObj.other

        

        assert mainObj.other[0].hasSameValues(refObj1) , 'Expected other with id of refObj1 to link to refObj1'

        mainObj.other = [ids1[0], ids2[0]]

        assert mainObj.other[0].hasSameValues(refObj1) , 'Expected other with id of refObj2 to link to refObj2'
        assert mainObj.other[1].hasSameValues(refObj2) , 'Expected other with id of refObj2 to link to refObj2'

        ids = mainObj.save(cascadeSave=False)
        assert ids and ids[0] , 'Failed to save object'

        fetchedObj = mainObj.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'

        mainObj = fetchedObj

        assert object.__getattribute__(mainObj, 'other').isFetched() is False , 'Expected isFetched to be False before fetch'

        mainObj.other


        assert object.__getattribute__(mainObj, 'other').isFetched() is True , 'Expected isFetched to be True after fetch'

        firstRefObj = RefedModel.objects.filter(name='rone').first()

        assert firstRefObj , 'Failed to fetch object'

        mainObj.other = [ firstRefObj ]

        ids = mainObj.save(cascadeSave=False)
        assert ids and ids[0] , 'Failed to save'

        fetchedObj = mainObj.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'

        assert fetchedObj.other == [ firstRefObj ] , 'Expected save using Model object would work properly. Did not fetch correct id after save.'
        
    def test_cascadeSave(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']
        PreMainModel = self.models['PreMainModel']

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)

        mainObj = MainModel(name='one', value='cheese')

        mainObj.other = [refObj1]

        ids = mainObj.save(cascadeSave=True)

        assert ids and ids[0] , 'Failed to save object'

        assert mainObj.other[0]._id , 'Failed to set _id on other'

        obj = MainModel.objects.filter(name='one').first()

        assert obj , 'Failed to fetch object by name'

        assert obj.other , 'Did not cascade save second object and link to parent'

        assert obj.other[0].name == 'rone' , 'Did save values on cascaded object'

        RefedModel.deleter.destroyModel()
        MainModel.deleter.destroyModel()

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)
        refObj2 = RefedModel(name='rtwo', strVal='goodbye', intVal=1)
        mainObj = MainModel(name='one', value='cheese')

        mainObj.other = [ refObj1, refObj2 ]

        preMainObj = PreMainModel(name='pone', value='bologna')

        preMainObj.main = [ mainObj ]

        ids = preMainObj.save(cascadeSave=True)

        assert ids and ids[0] , 'Failed to save object'


        obj = PreMainModel.objects.filter(name='pone').first()

        assert obj , 'Failed to fetch object by name'

        assert obj.main , 'Failed to link one level down'
        assert obj.main[0].name == 'one' , 'Did not save values one level down'

        assert obj.main[0].other , 'Failed to link two levels down'
        assert obj.main[0].other[0].name == 'rone' , 'Failed to save values two levels down or out of order'
        assert obj.main[0].other[1].name == 'rtwo' , 'Failed to save values two levels down or out of order'





if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
