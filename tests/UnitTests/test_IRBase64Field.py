#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRBase64Field - Test default values for fields
#

# vim: set ts=4 sw=4 st=4 expandtab

# Import and apply the properties (like Redis connection parameters) for this test.
import TestProperties

import base64
import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull
from IndexedRedis.compat_str import tobytes
from IndexedRedis.fields import IRBase64Field, IRField

# vim: ts=4 sw=4 expandtab

class TestIRBase64Field(object):
    '''
        TestIRBase64Field - Test base64 field
    '''

    KEEP_DATA = False

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.model = None

        if testMethod == self.test_general:
            class Model_Base64Value(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRBase64Field('value', defaultValue=irNull),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME='TestIRBase64Field__ModelBase64Value'

            self.model = Model_Base64Value
        elif testMethod == self.test_defaultValue:
            class Model_Base64DefaultValue(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRBase64Field('value', defaultValue=b'woobley'),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRBase64Field__ModelBase64DefaultValue'

            self.model = Model_Base64DefaultValue

        elif testMethod == self.test_index:
            class Model_Base64Index(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRBase64Field('value'),
                ]

                INDEXED_FIELDS = ['name', 'value']

                KEY_NAME = 'TestIRBase64Field__ModelBase64Index'

            self.model = Model_Base64Index

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


    def test_general(self):
        
        Model = self.model

        obj = Model()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected no updated fields when object is first created.\nExpected: %s\nGot:     %s' %(repr([]), repr(updatedFields) )

        assert obj.value == irNull , 'Expected default value of IRBase64Field to be irNull when defaultValue=irNull'

        obj.name = 'one'

        obj.save()

        assert obj.getUpdatedFields() == {} , 'Expected no updated fields after object is saved'

        obj.value = 'Hello World'

        assert obj.value == b'Hello World' , 'Expected IRBase64Field value to be "Hello World" after setting to "Hello World"'

        b64Value = base64.b64encode(tobytes(obj.value))

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == b'Hello World', 'Expected asDict(forStorage=False) to contain IRBase64Field value as original string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == b64Value , 'Expected asDict(forStorage=True) to contain IRBase64Field that was base64 encoded.\nExpected: %s\nGot:     %s' %(repr(b64Value), repr(dictForStorage['value']) )

        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating'

        assert updatedFields['value'][0] == irNull , 'Expected old value to be irNull in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == b'Hello World' , 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving.'

        fetchObj = Model.objects.filter(name='one').first()


        assert fetchObj , 'Expected to be able to fetch object on name="one" after saving.'

        obj = fetchObj

        assert obj.value == b'Hello World' , 'Expected value of fetched to be converted string (As bytes), b"Hello World". Got: %s' %(repr(fetchObj.value), )

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after fetching'

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == b'Hello World', 'After fetching, Expected asDict(forStorage=False) to contain IRBase64Field value as original string (as bytes). Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == b64Value , 'After fetching, Expected asDict(forStorage=True) to contain IRBase64Field that was base64 encoded.\nExpected: %s\nGot:     %s' %(repr(b64Value), repr(dictForStorage['value']) )

        obj.value = b'q123'


        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating on fetched object'

        assert updatedFields['value'][0] == b"Hello World" , 'Expected old value to be b"Hello World" in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == b'q123' , 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        b64Value = base64.b64encode(tobytes(obj.value))

        assert dictConverted['value'] == b'q123', 'After fetching, then updating, Expected asDict(forStorage=False) to contain IRBase64Field value as bytes string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == b64Value , 'After fetching, then updating, Expected asDict(forStorage=True) to contain IRBase64Field that was base64 encoded.\nExpected: %s\nGot:     %s' %(repr(b64Value), repr(dictForStorage['value']) )

        
        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving'

        obj = Model(value='popo')

        assert obj.value == b'popo' , 'Expected constructor to work to set values on IRBase64Field'

    def test_defaultValue(self):

        Model = self.model

        obj = Model()

        assert obj.value == b'woobley' , 'Expected defaultValue to be applied to a base64 field.\nExpected: b"woobley"\nGot:     %s' %(repr(obj.value), )

        obj.name = 'test'

        obj.save()

        assert obj.value == b'woobley' , 'Expected defaultValue to remain on a base64 field after saving'

        objFetched = Model.objects.filter(name='test').first()
        assert objFetched , 'Expected to be able to fetch object'

        obj = objFetched

        assert obj.value == b'woobley' , 'Expected defaultValue to remain on a base64 field after fetching'

        obj.value = b'cheesy'

        obj.save()

        objFetched = Model.objects.filter(name='test').first()
        assert objFetched , 'Expected to be able to fetch object'

        obj = objFetched

        assert obj.value == b'cheesy' , 'Expected to be able to change value from default.'

    def test_index(self):

        Model = self.model

        obj = Model()

        otherObj = Model(name='two', value='val2')
        
        ids = otherObj.save()

        assert ids and ids[0] , 'Failed to save object'

        obj.name = 'one'

        ids = obj.save()
        assert ids and ids[0] , 'Failed to save object'


        fetchedObjs = Model.objects.filter(value=irNull).all()

        assert len(fetchedObjs) == 1 , 'Expected to be able to fetch an IRBase64Field with irNull as the index'
        assert fetchedObjs[0].name == 'one' , 'Fetched wrong object'

        assert fetchedObjs[0].value == irNull , 'Expected after fetch for irNull to be retained.'

        emptyStrObj = Model(value='')

        assert emptyStrObj.value == b'' , 'Expected IRBase64Field to translate empty string to b"" '

        emptyStrObj.name = 'emptystr'
        ids = emptyStrObj.save()

        assert ids and ids[0] , 'Failed to save object'

        fetchedObjs = Model.objects.filter(value=irNull).all()

        assert len(fetchedObjs) == 1 , 'Expected for index on IRBase64Field to treat irNull and empty string as different. fetched both on irNull'


        fetchedObjs = Model.objects.filter(value='').all()

        assert len(fetchedObjs) == 1 , 'Expected for index on IRBase64Field to treat irNull and empty string as different. fetched both on empty str'
        

        obj.value = 'val1'
        ids = obj.save()
        assert ids and ids[0] , 'Failed to save object'

        fetchedObjs = Model.objects.filter(value='val2').all()

        assert len(fetchedObjs) == 1 , 'Expected to be able to fetch object using IRBase64Field with a value'
        assert fetchedObjs[0].name == 'two' , 'Fetched wrong object'


if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
