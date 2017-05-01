#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRCompressedField - Test for IRCompressedField
#

# vim: set ts=4 sw=4 st=4 expandtab

# Import and apply the properties (like Redis connection parameters) for this test.
import TestProperties

import sys
import subprocess

import zlib
import bz2

from IndexedRedis import IndexedRedisModel, irNull
from IndexedRedis.compat_str import tobytes
from IndexedRedis.fields import IRCompressedField, IRField

# vim: ts=4 sw=4 expandtab

class TestIRCompressedField(object):
    '''
        TestIRCompressedField - Test IRCompressedField
    '''

    KEEP_DATA = False

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.model = None

        if testMethod == self.test_general:
            class Model_GeneralCompressed(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRCompressedField('value', defaultValue=irNull),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME='TestIRCompressedField__GeneralCompressed'

            self.model = Model_GeneralCompressed

        elif testMethod == self.test_compressBz2:
            class Model_CompressBz2(IndexedRedisModel):

                FIELDS = [
                    IRField('name'),
                    IRCompressedField('value', compressMode='bz2', defaultValue=irNull),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRCompressedField__CompressBz2'

            self.model = Model_CompressBz2
        elif testMethod == self.test_compressLzma:
            try:
                class Model_CompressLzma(IndexedRedisModel):
                    FIELDS = [
                        IRField('name'),
                        IRCompressedField('value', compressMode='lzma', defaultValue=irNull),
                    ]

                    INDEXED_FIELDS = ['name']

                    KEY_NAME = 'TestIRCompressedField__CompressLzma'
                self.model = Model_CompressLzma
            except ImportError:
                pass

        elif testMethod == self.test_defaultValue:
            class Model_CompressedDefaultValue(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRCompressedField('value', defaultValue=b'woobley'),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME='TestIRCompressedField__CompressedDefaultValue'

            self.model = Model_CompressedDefaultValue

        elif testMethod == self.test_index:
            class Model_CompressedIndex(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRCompressedField('value')
                ]

                INDEXED_FIELDS = ['name', 'value']

                KEY_NAME = 'TestIRCompressedField__CompressedIndex'

            self.model = Model_CompressedIndex

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

        helloWorldBytes = b'\x01Hello World\x01'
        compressedHelloWorldGzip = zlib.compress(helloWorldBytes, 9)

        assert updatedFields == {} , 'Expected no updated fields when object is first created.\nExpected: %s\nGot:     %s' %(repr({}), repr(updatedFields) )

        assert obj.value == irNull , 'Expected default value of IRCompressedField to be irNull when defaultValue=irNull'

        obj.name = 'one'

        obj.save()

        assert obj.getUpdatedFields() == {} , 'Expected no updated fields after object is saved'

        obj.value = u'Goodbye'

        assert obj.value == u'Goodbye' , 'Expected IRCompressedField value to be "goodbye" after setting to "goodbye". Got: %s' %(repr(obj.value, ))

        obj.value = helloWorldBytes

        assert obj.value == helloWorldBytes , 'Expected IRCompressedField value to be b"\\x01Hello World\\x01" after setting to "\\x01Hello World\\x01"'

        
        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))



        assert dictConverted['value'] == helloWorldBytes, 'Expected asDict(forStorage=False) to contain IRCompressedField value as uncompressed bytes string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == compressedHelloWorldGzip, 'Expected asDict(forStorage=True) to contain IRCompressedField value as compressed string. \nExpected: %s\nGot:     %s' %(repr(compressedHelloWorldGzip), repr(dictForStorage['value']) )

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

        assert obj.value == helloWorldBytes , 'Expected value of fetched to be uncompressed value. Got: %s' %(repr(helloWorldBytes), repr(fetchObj.value), )

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after fetching'

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == helloWorldBytes, 'After fetching, Expected asDict(forStorage=False) to contain IRCompressedField value as uncompressed bytes string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == compressedHelloWorldGzip, 'After fetching, Expected asDict(forStorage=True) to contain IRCompressedField value as compressed bytes string. \nExpected: %s\nGot:     %s' %(repr(compressedHelloWorldGzip), repr(dictForStorage['value']) )

        obj.value = b'q123'

        compressedQ123 = zlib.compress(b'q123', 9)


        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating on fetched object'

        assert updatedFields['value'][0] == helloWorldBytes , 'Expected old value to be %s in updatedFields. Got: %s' %(repr(helloWorldBytes), repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == b'q123' , 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == b'q123', 'After fetching, then updating, Expected asDict(forStorage=False) to contain IRCompressedField value as uncompressed bytes string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == compressedQ123 , 'After fetching, then updating, Expected asDict(forStorage=True) to contain IRCompressedField value as compressed bytes string.\nExpected: %s\nGot:     %s' %(repr(compressedQ123), repr(dictForStorage['value']) )

        
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

    def test_compressBz2(self):

        someStr = "The quick brown fox jumped over the lazy dog.\n" * 5
        someStrBytes = tobytes(someStr)

        someStrBz2 = bz2.compress(tobytes(someStr), 9)

        Model = self.model

        obj = Model()

        obj.name = 'one'

        assert obj.value == irNull , 'Expected default value (irNull) to be taken seriously.'

        obj.value = someStr

        assert obj.value == someStr

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == someStr , 'Expected original string to be retained on forStorage=False dict. Got: %s' %(repr(dictConverted['value']), )

        assert dictForStorage['value'] == someStrBz2 , 'Expected bz2 compressed value to be set on forStorage=True dict.\nExpected: %s\nGot:     %s' %(repr(someStrBz2), repr(dictForStorage['value']) )

        ids = obj.save()

        assert ids and ids[0] , 'Failed to save object with bz2 compression'

        objFetched = Model.objects.filter(name='one').first()

        assert objFetched , 'Failed to fetch object'

        obj = objFetched

        assert obj.value == someStrBytes , 'Expected fetched object to contain the uncompressed value. Got: %s' %(repr(obj.value), )

    def test_index(self):

        Model = self.model

        obj1 = Model(name='one', value='Hello World')
        obj2 = Model(name='two', value='Goodbye World')

        ids = obj1.save()
        assert ids and ids[0] , 'Failed to save model'

        ids = obj2.save()
        assert ids and ids[0] , 'Failed to save model'


        fetchedObjs = Model.objects.filter(value='Hello World').all()

        assert fetchedObjs , 'Failed to fetch on IRCompressedField index'
        assert len(fetchedObjs) == 1 , 'Fetched wrong number of objects.'

        assert fetchedObjs[0].name == 'one' , 'Fetched wrong object'

        obj3 = Model(name='three', value='Hello World')
        
        ids = obj3.save()
        assert ids and ids[0] , 'Failed to save model'

        fetchedObjs = Model.objects.filter(value='Hello World').all()

        assert fetchedObjs , 'Failed to fetch on IRCompressedField index'
        assert len(fetchedObjs) == 2 , 'Fetched wrong number of objects.'

        assert list(sorted( [obj.name for obj in fetchedObjs] ) ) == ['one', 'three'] , 'Fetched wrong objects'

    def test_compressLzma(self):
        if not self.model:
            sys.stderr.write('NOTE: lzma compression is not available in this installation (python2 and missing an external lzma module). Cannot run test_compressLzma.\n')
            return

        
        Model = self.model

        Model.validateModel()

        lzma = Model.FIELDS['value'].getCompressMod()

        someStr = "The quick brown fox jumped over the lazy dog.\n" * 5
        someStrBytes = tobytes(someStr)

        someStrLzma = lzma.compress(tobytes(someStr))


        obj = Model()

        obj.name = 'one'

        assert obj.value == irNull , 'Expected default value (irNull) to be taken seriously.'

        obj.value = someStr

        assert obj.value == someStr

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == someStr , 'Expected original string to be retained on forStorage=False dict. Got: %s' %(repr(dictConverted['value']), )

        assert dictForStorage['value'] == someStrLzma , 'Expected lzma compressed value to be set on forStorage=True dict.\nExpected: %s\nGot:     %s' %(repr(someStrLzma), repr(dictForStorage['value']) )

        ids = obj.save()

        assert ids and ids[0] , 'Failed to save object with lzma compression'

        objFetched = Model.objects.filter(name='one').first()

        assert objFetched , 'Failed to fetch object'

        obj = objFetched

        assert obj.value == someStrBytes , 'Expected fetched object to contain the uncompressed value. Got: %s' %(repr(obj.value), )



if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
