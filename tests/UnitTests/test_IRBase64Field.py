#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRBase64Field - Test default values for fields
#

# vim: set ts=4 sw=4 st=4 expandtab

import base64
import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull
from IndexedRedis.compat_str import tobytes
from IndexedRedis.fields import IRBase64Field, IRField

# vim: ts=4 sw=4 expandtab

class TestIRBase64Field(object):
    '''
        TestIRField - Test some basic IRField stuff
    '''

    KEEP_DATA = False

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.model = None

        if testMethod in (self.test_general, ):
            class Model_Base64Value(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRBase64Field('value', defaultValue=irNull),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME='TestIRBase64Field__ModelBase64Value'

            self.model = Model_Base64Value

        # If KEEP_DATA is False (debug flag), then delete all objects before so prior test doesn't interfere
        if self.KEEP_DATA is False and self.model:
            self.model.objects.delete()

    def teardown_method(self, testMethod):
        '''
            teardown_method - Called after every method.

                If self.model is set, will delete all objects relating to that model. To retain objects for debugging, set TestIRField.KEEP_DATA to True.
        '''

        if self.model and self.KEEP_DATA is False:
            self.model.objects.delete()


    @staticmethod
    def _assert_fieldEquals(obj, fieldName, expectedValue, whatExpectedStr='', expectedValueReadable=None):
        val = getattr(obj, fieldName)

        if expectedValueReadable is None:
            expectedValueReadable = repr(expectedValue)

        assert val == expectedValue , 'Expected %s to be %s. Got <%s> %s' %(whatExpectedStr or fieldName, expectedValueReadable, val.__class__.__name__, repr(val))


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

        assert obj.value == 'Hello World' , 'Expected IRBase64Field value to be "Hello World" after setting to "Hello World"'

        b64Value = base64.b64encode(tobytes(obj.value))

        dictConverted = obj.asDict(forStorage=False, strKeys=True)
        dictForStorage = obj.asDict(forStorage=True, strKeys=True)

        assert dictConverted['value'] == 'Hello World', 'Expected asDict(forStorage=False) to contain IRBase64Field value as original string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == b64Value , 'Expected asDict(forStorage=True) to contain IRBase64Field that was base64 encoded.\nExpected: %s\nGot:     %s' %(repr(b64Value), repr(dictForStorage['value']) )

        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating'

        assert updatedFields['value'][0] == irNull , 'Expected old value to be irNull in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == 'Hello World' , 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving.'

        fetchObj = Model.objects.filter(name='one').first()


        assert fetchObj , 'Expected to be able to fetch object on name="one" after saving.'

        obj = fetchObj

        assert obj.value == b'Hello World' , 'Expected value of fetched to be converted string (As bytes), b"Hello World". Got: %s' %(repr(fetchObj.value), )

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after fetching'

        dictConverted = obj.asDict(forStorage=False, strKeys=True)
        dictForStorage = obj.asDict(forStorage=True, strKeys=True)

        assert dictConverted['value'] == b'Hello World', 'After fetching, Expected asDict(forStorage=False) to contain IRBase64Field value as original string (as bytes). Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == b64Value , 'After fetching, Expected asDict(forStorage=True) to contain IRBase64Field that was base64 encoded.\nExpected: %s\nGot:     %s' %(repr(b64Value), repr(dictForStorage['value']) )

        obj.value = b'q123'


        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating on fetched object'

        assert updatedFields['value'][0] == b"Hello World" , 'Expected old value to be b"Hello World" in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == b'q123' , 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        dictConverted = obj.asDict(forStorage=False, strKeys=True)
        dictForStorage = obj.asDict(forStorage=True, strKeys=True)

        b64Value = base64.b64encode(tobytes(obj.value))

        assert dictConverted['value'] == b'q123', 'After fetching, then updating, Expected asDict(forStorage=False) to contain IRBase64Field value as bytes string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == b64Value , 'After fetching, then updating, Expected asDict(forStorage=True) to contain IRBase64Field that was base64 encoded.\nExpected: %s\nGot:     %s' %(repr(b64Value), repr(dictForStorage['value']) )

        
        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving'



if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py "%s" %s' %(sys.argv[0], ' '.join(sys.argv[1:])), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
