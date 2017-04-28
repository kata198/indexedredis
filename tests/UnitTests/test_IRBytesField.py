#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRBytesField - Test default values for fields
#

# vim: set ts=4 sw=4 st=4 expandtab

# Import and apply the properties (like Redis connection parameters) for this test.
import TestProperties

import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull, getDefaultIREncoding, setDefaultIREncoding
from IndexedRedis.compat_str import tobytes
from IndexedRedis.fields import IRBytesField, IRField

# vim: ts=4 sw=4 expandtab

class TestIRBytesField(object):
    '''
        TestIRBytesField - Test IRBytesField
    '''

    KEEP_DATA = False

    def setup_class(self):
        self.defaultIREncoding = getDefaultIREncoding()

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.model = None


        if testMethod in (self.test_general, ):
            class Model_BytesValue(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRBytesField('value', defaultValue=irNull),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME='TestIRBytesField__ModelBytesValue'

            self.model = Model_BytesValue
        elif testMethod in (self.test_defaultValue, ):
            class Model_BytesDefaultValue(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRBytesField('value', defaultValue=b'woobley'),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRBytesField__ModelBytesDefaultValue'

            self.model = Model_BytesDefaultValue

        elif testMethod in (self.test_indexBytes, ):
            class Model_IndexBytes(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRBytesField('value', defaultValue=irNull),
                    IRBytesField('value2', defaultValue=b'xxx'),
                ]

                INDEXED_FIELDS = ['name', 'value', 'value2']

                KEY_NAME = 'TestIRBytesField__IndexBytes'

            self.model = Model_IndexBytes

        elif testMethod == self.test_bytesEncoding:
            setDefaultIREncoding('ascii')
            class Model_BytesEncoding(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRBytesField('value', encoding='utf-8'),
                ]

                INDEXED_FIELDS = ['name', 'value']

                KEY_NAME = 'TestIRBytesField__BytesEncoding'

            self.model = Model_BytesEncoding

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

        setDefaultIREncoding(self.defaultIREncoding)


    def test_general(self):
        
        Model = self.model

        obj = Model()

        updatedFields = obj.getUpdatedFields()

        helloWorldBytes = b'\x01Hello World\x01'

        assert updatedFields == {} , 'Expected no updated fields when object is first created.\nExpected: %s\nGot:     %s' %(repr([]), repr(updatedFields) )

        assert obj.value == irNull , 'Expected default value of IRBytesField to be irNull when defaultValue=irNull'

        obj.name = 'one'

        obj.save()

        assert obj.getUpdatedFields() == {} , 'Expected no updated fields after object is saved'

        obj.value = u'Goodbye'

        assert obj.value == b'Goodbye' , 'Expected IRBytesField value to be b"goodbye" after setting to "goodbye" (converted to bytes)'

        obj.value = helloWorldBytes

        assert obj.value == helloWorldBytes , 'Expected IRBytesField value to be b"\\x01Hello World\\x01" after setting to "\\x01Hello World\\x01"'

        
        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == helloWorldBytes, 'Expected asDict(forStorage=False) to contain IRBytesField value as bytes string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == helloWorldBytes, 'Expected asDict(forStorage=True) to contain IRBytesField value as bytes string. \nExpected: %s\nGot:     %s' %(repr(helloWorldBytes), repr(dictForStorage['value']) )

        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating'

        assert updatedFields['value'][0] == irNull , 'Expected old value to be irNull in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == helloWorldBytes , 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving.'

        fetchObj = Model.objects.filter(name='one').first()


        assert fetchObj , 'Expected to be able to fetch object on name="one" after saving.'

        obj = fetchObj

        assert obj.value == helloWorldBytes , 'Expected value of fetched to be converted string (As bytes), %s. Got: %s' %(repr(helloWorldBytes), repr(fetchObj.value), )

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after fetching'

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == helloWorldBytes, 'After fetching, Expected asDict(forStorage=False) to contain IRBytesField value as bytes string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == helloWorldBytes, 'After fetching, Expected asDict(forStorage=True) to contain IRBytesField value as bytes string. \nExpected: %s\nGot:     %s' %(repr(helloWorldBytes), repr(dictForStorage['value']) )

        obj.value = b'q123'


        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating on fetched object'

        assert updatedFields['value'][0] == helloWorldBytes , 'Expected old value to be %s in updatedFields. Got: %s' %(repr(helloWorldBytes), repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == b'q123' , 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == b'q123', 'After fetching, then updating, Expected asDict(forStorage=False) to contain IRBytesField value as bytes string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == b'q123', 'After fetching, then updating, Expected asDict(forStorage=True) to contain IRBytesField value as bytes string.\nExpected: %s\nGot:     %s' %(repr(b'q123'), repr(dictForStorage['value']) )

        
        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving'

    def test_defaultValue(self):

        Model = self.model

        obj = Model()

        assert obj.value == b'woobley' , 'Expected defaultValue to be applied to a bytes field.\nExpected: b"woobley"\nGot:     %s' %(repr(obj.value), )

        obj.name = 'test'

        obj.save()

        assert obj.value == b'woobley' , 'Expected defaultValue to remain on a bytes field after saving'

        objFetched = Model.objects.filter(name='test').first()
        assert objFetched , 'Expected to be able to fetch object'

        obj = objFetched

        assert obj.value == b'woobley' , 'Expected defaultValue to remain on a bytes field after fetching'

        obj.value = b'cheesy'

        obj.save()

        objFetched = Model.objects.filter(name='test').first()
        assert objFetched , 'Expected to be able to fetch object'

        obj = objFetched

        assert obj.value == b'cheesy' , 'Expected to be able to change value from default.'

    def test_indexBytes(self):

        Model = self.model

        obj = Model()

        obj.name = 'test'

        ids = obj.save()

        assert ids and ids[0] , 'Failed to save object'

        # Add a "distraction" object
        otherObj = Model()
        otherObj.value = 'qqq'
        otherObj.value2 = 'zzz'

        otherObj.save()

        objFetched = Model.objects.filter(value=irNull).first()

        assert objFetched , 'Failed to fetch an object with default value (irNull) on a bytes field'

        d1 = obj.asDict(includeMeta=True, forStorage=False, strKeys=True)
        d2 = objFetched.asDict(includeMeta=True, forStorage=False, strKeys=True)

        assert objFetched == obj , 'Object fetched was not expected object.\nExpected: %s\n\nGot:     %s\n' %( 
                obj.asDict(includeMeta=True, forStorage=False, strKeys=True),
                objFetched.asDict(includeMeta=True, forStorage=False, strKeys=True)
                )

        objFetched = Model.objects.filter(value2=b'zzz').first()

        assert objFetched , 'Failed to fetch object using a non-default value on bytes field'

        assert objFetched == otherObj , 'Object fetched was not expected object.\nExpected: %s\n\nGot:     %s\n' %( 
                otherObj.asDict(includeMeta=True, forStorage=False, strKeys=True),
                objFetched.asDict(includeMeta=True, forStorage=False, strKeys=True)
                )

        objFetched = Model.objects.filter(value=b'qqq').first()

        assert objFetched , 'Failed to fetch object using a non-default value on bytes field'

        assert objFetched == otherObj , 'Object fetched was not expected object.\nExpected: %s\n\nGot:     %s\n' %( 
                otherObj.asDict(includeMeta=True, forStorage=False, strKeys=True),
                objFetched.asDict(includeMeta=True, forStorage=False, strKeys=True)
                )

    def test_bytesEncoding(self):

        Model = self.model

        obj = Model()

        obj.name = 'one'

        prettyPicturesUtf8Bytes = b' \xe2\x9c\x8f \xe2\x9c\x90 \xe2\x9c\x91 \xe2\x9c\x92 \xe2\x9c\x93 \xe2\x9c\x94 \xe2\x9c\x95 \xe2\x9c\x96 \xe2\x9c\x97 \xe2\x9c\x98 \xe2\x9c\x99 \xe2\x9c\x9a \xe2\x9c\x9b \xe2\x9c\x9c \xe2\x9c\x9d \xe2\x9c\x9e \xe2\x9c\x9f \xe2\x9c\xa0 \xe2\x9c\xa1 \xe2\x9c\xa2 \xe2\x9c\xa3 \xe2\x9c\xa4 \xe2\x9c\xa5 \xe2\x9c\xa6 \xe2\x9c\xa7 \xe2\x9c\xa9 \xe2\x9c\xaa \xe2\x9c\xab '

        prettyPicturesUtf8 = prettyPicturesUtf8Bytes.decode('utf-8')


        obj.value = prettyPicturesUtf8

        assert obj.value == prettyPicturesUtf8Bytes , 'Expected utf-8 string to be converted to bytes after setting'

        ids = obj.save()

        assert ids and ids[0] , 'Failed to save object'

        fetchedObj = Model.objects.filter(value=prettyPicturesUtf8Bytes).first()

        assert fetchedObj , 'Failed to fetch object by bytes value'


        fetchedObj = Model.objects.filter(value=prettyPicturesUtf8).first()

        assert fetchedObj , 'Failed to fetch object by unicode value'

        obj = fetchedObj

        assert obj.value == prettyPicturesUtf8Bytes , 'Expected after fetch that data is bytes version of utf-8 string'



if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
