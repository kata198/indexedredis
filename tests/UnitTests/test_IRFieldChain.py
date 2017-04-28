#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRFieldChain - Test field chaining
#

# Import and apply the properties (like Redis connection parameters) for this test.
import TestProperties

# vim: set ts=4 sw=4 st=4 expandtab

import base64
import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull, InvalidModelException
from IndexedRedis.compat_str import tobytes, to_unicode, getDefaultIREncoding, setDefaultIREncoding
from IndexedRedis.fields import IRBase64Field, IRField, IRUnicodeField, IRPickleField, IRCompressedField, IRFieldChain

# vim: ts=4 sw=4 expandtab
class TestObj(object):

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __hash__(self):
        return hash( str(hash(self.a)) + '_' + str(hash(self.b)) )

    def __eq__(self, other):
        if type(other) != type(self):
            return False

        return bool(self.a == other.a and self.b == other.b)

    def __ne__(self, other):
        if type(other) != type(self):
            return True

        return bool(self.a != other.a or self.b != other.b)

    def __repr__(self):
        return 'TestObj( a=%s , b=%s )' %(repr(self.a), repr(self.b) )

    __str__ = __repr__


class TestIRFieldChain(object):
    '''
        TestIRFieldChain - Test field chaining
    '''

    KEEP_DATA = False

    def setup_class(self):
        self.defaultIREncoding = getDefaultIREncoding()

        self.utf16DataBytes = b'\xff\xfe\x01\xd8\x0f\xdc\x01\xd8-\xdc\x01\xd8;\xdc\x01\xd8+\xdc'
        self.utf16Data = self.utf16DataBytes.decode('utf-16')

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.model = None

        if testMethod == self.test_base64AndUnicode:
            setDefaultIREncoding('ascii') # Ensure we are using the "encoding" value provided in the field
            class Model_Base64Unicode(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRFieldChain('value', [IRUnicodeField(encoding='utf-8'), IRBase64Field(encoding='utf-8')], defaultValue=irNull),
                    IRFieldChain('value2', [IRUnicodeField(encoding='utf-8'), IRBase64Field(encoding='utf-8')], defaultValue='qqz'),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRFieldChain__ModelBase64Unicode'

            self.model = Model_Base64Unicode
        elif testMethod == self.test_utf16Compression:
            setDefaultIREncoding('ascii') # Ensure we are using the "encoding" value provided in the field

            class Model_Utf16Compression(IndexedRedisModel):

                FIELDS = [
                    IRField('name'),
                    IRFieldChain('value', [IRUnicodeField(encoding='utf-16'), IRCompressedField()]),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRFieldChain__Utf16Compression'

            self.model = Model_Utf16Compression
            
        elif testMethod == self.test_compressPickle:
            class Model_CompressPickle(IndexedRedisModel):

                FIELDS = [
                    IRField('name'),
                    IRFieldChain('value', [IRPickleField(), IRCompressedField()]),
                    IRFieldChain('value2', [IRPickleField(), IRCompressedField()], defaultValue=['a', 'b', 'c'])
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRFieldChain__ModelCompressPickle'

            self.model = Model_CompressPickle
        elif testMethod == self.test_intBase64:
            class Model_IntBase64(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRFieldChain('value', [IRField(valueType=int), IRBase64Field ] ),
                    IRFieldChain('value2', [IRField(valueType=int), IRBase64Field ], defaultValue=-1 )
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRFieldChain__IntBase64'

            self.model = Model_IntBase64
        elif testMethod == self.test_index:
            class Model_ChainIndex(IndexedRedisModel):

                FIELDS = [
                    IRField('name'),
                    IRFieldChain('value', [IRField(valueType=str), IRBase64Field()]),
                ]

                INDEXED_FIELDS = ['name', 'value']

                KEY_NAME = 'TestIRFieldChain__ModelChainIndex'

            self.model = Model_ChainIndex

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

        # Reset encoding back to original, some tests may change it.
        setDefaultIREncoding(self.defaultIREncoding)


    def test_base64AndUnicode(self):
        Model = self.model

        obj = Model()
    
        prettyPictures = b' \xe2\x9c\x8f \xe2\x9c\x90 \xe2\x9c\x91 \xe2\x9c\x92 \xe2\x9c\x93 \xe2\x9c\x94 \xe2\x9c\x95 \xe2\x9c\x96 \xe2\x9c\x97 \xe2\x9c\x98 \xe2\x9c\x99 \xe2\x9c\x9a \xe2\x9c\x9b \xe2\x9c\x9c \xe2\x9c\x9d \xe2\x9c\x9e \xe2\x9c\x9f \xe2\x9c\xa0 \xe2\x9c\xa1 \xe2\x9c\xa2 \xe2\x9c\xa3 \xe2\x9c\xa4 \xe2\x9c\xa5 \xe2\x9c\xa6 \xe2\x9c\xa7 \xe2\x9c\xa9 \xe2\x9c\xaa \xe2\x9c\xab '
        prettyPicturesUnicode = to_unicode(prettyPictures, encoding='utf-8')

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected no updated fields when object is first created.\nExpected: %s\nGot:     %s' %(repr([]), repr(updatedFields) )

        assert obj.value == irNull , 'Expected default value of IRFieldChain to be irNull when defaultValue=irNull. Got: %s' %(obj.value, )
        assert obj.value2 == 'qqz' , 'Expected default value of IRFieldChain to be "qqz" when defaultValue="qqz". Got: %s' %(obj.value2, )

        obj.name = 'one'

        obj.save()


        updatedFields = obj.getUpdatedFields()
        assert updatedFields == {} , 'Expected no updated fields after object is saved. Got: %s' %(repr(updatedFields), )


        obj.value = prettyPicturesUnicode
        assert obj.value == prettyPicturesUnicode , 'Expected IRFieldChain value to unicode of prettyPictures when set to unicode value'

        obj.value = prettyPictures
        assert obj.value == prettyPicturesUnicode , 'Expected IRFieldChain value to unicode of prettyPictures when set to bytes value'

        b64Value = base64.b64encode(tobytes(obj.value, encoding='utf-8'))

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to a dict, both not-for-storage and for-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == prettyPicturesUnicode, 'Expected asDict(forStorage=False) to contain IRFieldChain value as unicode str.. Got: %s' %(repr(dictConverted['value']), )
        assert dictForStorage['value'] == b64Value , 'Expected asDict(forStorage=True) to contain IRFieldChain that was base64 encoded.\nExpected: %s\nGot:     %s' %(repr(b64Value), repr(dictForStorage['value']) )

        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating'

        assert updatedFields['value'][0] == irNull , 'Expected old value to be irNull in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == prettyPicturesUnicode, 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving.'

        fetchObj = Model.objects.filter(name='one').first()


        assert fetchObj , 'Expected to be able to fetch object on name="one" after saving.'

        obj = fetchObj

        assert obj.value == prettyPicturesUnicode , 'Expected value of fetched to be unicode string. Got: <%s> %s' %(type(fetchObj.value).__name__, repr(fetchObj.value), )

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after fetching'

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to a dict, both not-for-storage and for-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == prettyPicturesUnicode, 'After fetching, Expected asDict(forStorage=False) to contain IRFieldChain value as unicode string.  Got: %s' %(repr(dictConverted['value']), )
        assert dictForStorage['value'] == b64Value , 'After fetching, Expected asDict(forStorage=True) to contain IRFieldChain that was base64 encoded.\nExpected: %s\nGot:     %s' %(repr(b64Value), repr(dictForStorage['value']) )

        obj.value = b'q123'


        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating on fetched object'

        assert updatedFields['value'][0] == prettyPicturesUnicode , 'Expected old value to be prettyPictures as unicode in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == u'q123' , 'Expected converted value to be new value in updatedFields as unicode. Got: %s' %(repr(updatedFields['value'][1]), )

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to a dict, both not-for-storage and for-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        b64Value = base64.b64encode(tobytes(obj.value))

        assert dictConverted['value'] == u'q123', 'After fetching, then updating, Expected asDict(forStorage=False) to contain IRFieldChain value as unicode string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == b64Value , 'After fetching, then updating, Expected asDict(forStorage=True) to contain IRFieldChain that was base64 encoded.\nExpected: %s\nGot:     %s' %(repr(b64Value), repr(dictForStorage['value']) )

        
        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving'

    def test_compressPickle(self):
        Model = self.model

        obj = Model()


        testObj1 = TestObj(19, 'cheese')
        testObj2 = TestObj(-4.77, 99)

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected no updated fields when object is first created.\nExpected: %s\nGot:     %s' %(repr([]), repr(updatedFields) )

        assert obj.value == irNull , 'Expected default value of IRFieldChain to be irNull when defaultValue=irNull. Got: %s' %(obj.value, )
        assert obj.value2 == ['a', 'b', 'c'] , 'Expected default value of IRFieldChain to be ["a", "b", "c"] when defaultValue= ["a", "b", "c"]. Got: %s' %(obj.value2, )

        obj.name = 'one'

        obj.save()


        updatedFields = obj.getUpdatedFields()
        assert updatedFields == {} , 'Expected no updated fields after object is saved. Got: %s' %(repr(updatedFields), )


        obj.value = testObj1
        assert obj.value == testObj1, 'Expected IRFieldChain value to retain after setting'

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to a dict, both not-for-storage and for-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == testObj1, 'Expected asDict(forStorage=False) to contain IRFieldChain value as testObj1 Got: %s' %(repr(dictConverted['value']), )
        # Note, just testing that it changed.. if we can fetch and convert it assume it was converted correctly.
        assert dictForStorage['value'] != testObj1, 'Expected asDict(forStorage=True) to be converted in some way.'

        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating'

        assert updatedFields['value'][0] == irNull , 'Expected old value to be irNull in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == testObj1, 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving.'

        fetchObj = Model.objects.filter(name='one').first()


        assert fetchObj , 'Expected to be able to fetch object on name="one" after saving.'

        obj = fetchObj

        assert obj.value == testObj1, 'Expected value of fetched to be testObj1. Got: <%s> %s' %(type(fetchObj.value).__name__, repr(fetchObj.value), )

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after fetching'

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to a dict, both not-for-storage and for-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == testObj1, 'After fetching, Expected asDict(forStorage=False) to contain IRFieldChain value as object.  Got: %s' %(repr(dictConverted['value']), )
        assert dictForStorage['value'] != testObj1 , 'After fetching, Expected asDict(forStorage=True) to contain IRFieldChain that was encoded in some way.'

        obj.value = testObj2


        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating on fetched object'

        assert updatedFields['value'][0] == testObj1, 'Expected old value to be testObj1 in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == testObj2 , 'Expected new value to be testObj2 in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to a dict, both not-for-storage and for-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == testObj2, 'After fetching, then updating, Expected asDict(forStorage=False) to contain IRFieldChain value as testObj2. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] not in (testObj1, testObj2), 'After fetching, then updating, Expected asDict(forStorage=True) to contain a converted value.'

        
        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving'

    def test_intBase64(self):
        
        Model = self.model

        obj = Model()

        assert obj.value == irNull , 'Expected default value to be irNull on chain when defaultValue=irNull. Got: <%s> %s' %(obj.value.__class__.__name__, repr(obj.value), )
        assert obj.value2 == -1 , 'Expected default value to be -1 on chain when defaultValue=-1. Got: <%s> %s' %(obj.value.__class__.__name__, repr(obj.value), )

        obj.name = 'one'

        obj.save()

        objFetched = Model.objects.filter(name='one').first()

        assert objFetched , 'Expected to be able to fetch on indexed field'

        obj = objFetched

        assert obj.value == irNull , 'After fetch-and-save, expected default value to be irNull on chain when defaultValue=irNull. Got: <%s> %s' %(obj.value.__class__.__name__, repr(obj.value), )
        assert obj.value2 == -1 , 'After fetch-and-save, expected default value to be -1 on chain when defaultValue=-1. Got: <%s> %s' %(obj.value.__class__.__name__, repr(obj.value), )


        obj.value = '14'

        assert obj.value == 14 , 'Expected value to be conveted to int after setting'

        forStorageDict = obj.asDict(forStorage=True)


        b64Value = base64.b64encode(b'14')

        assert forStorageDict['value'] == b64Value , 'Expected value to be base64 encoded in forStorage representation'

        obj.save()

        objFetched = Model.objects.filter(name='one').first()

        assert objFetched , 'Expected to be able to fetch on indexed field'

        obj = objFetched

        assert obj.value == 14 , 'Expected value to be set to 14 after fetching. Got: <%s> %s' %(obj.value.__class__.__name__, repr(obj.value))

    def test_utf16Compression(self):

        Model = self.model

        obj = Model()

        assert obj.value == irNull , 'Expected default value to be retained'

        obj.name = 'one'

        obj.save()

        obj.value = self.utf16DataBytes

        assert obj.value == self.utf16Data , 'Expected bytes data to be converted to unicode after setting on object'

        ids = obj.save()

        assert ids and ids[0] , 'Failed to save object'

        fetchedObjs = Model.objects.all()

        assert len(fetchedObjs) == 1 , 'Expected there to be one object saved, got: %d' %(len(fetchedObjs), )

        obj = fetchedObjs[0]

        assert obj.value == self.utf16Data , 'Expected data to be the utf-16 string after fetching'


    def test_index(self):

        Model = self.model

        obj1 = Model(name='one')

        obj1.value = 'Hello World'

        obj2 = Model(name='two')

        obj2.value = 'Goodbye World'

        ids = obj1.save()
        assert ids and ids[0] , 'Failed to save object'

        ids = obj2.save()
        assert ids and ids[0] , 'Failed to save object'

        objFetched = Model.objects.filter(value='Hello World').all()

        assert len(objFetched) == 1 , 'Failed to fetch one object. Got: %d' %(int(objFetched), )

        assert objFetched[0].name == 'one' , 'Fetched wrong object'

        # TODO: Clean up and test more

        class BadModel1(IndexedRedisModel):
            
            FIELDS = [
                IRField('name'),
                IRFieldChain('value', [IRPickleField(), IRCompressedField()])
            ]

            INDEXED_FIELDS = ['name', 'value']

            KEY_NAME = 'TestIRFieldChain__BadModel1'

        gotInvalidModelException = False
        try:
            BadModel1.validateModel()
        except InvalidModelException:
            gotInvalidModelException = True

        assert gotInvalidModelException , 'Expected to get an invalid model exception trying to index on an IRFieldChain which contains a non-indexable field'


        class AutoHashIndexModel1(IndexedRedisModel):
            FIELDS = [
                IRField('name'),
                IRFieldChain('value', [IRField(), IRBase64Field()] ),
            ]

            INDEXED_FIELDS = ['name', 'value']

            KEY_NAME = 'TestIRFieldChain__AutoHashIndexModel1'

        gotInvalidModelException = False
        ie = None
        try:
            AutoHashIndexModel1.validateModel()
        except InvalidModelException as _ie:
            gotInvalidModelException = True
            ie = _ie

        assert not gotInvalidModelException , 'Expected to be able to index on a field chain containing two indexable IRField types. ' + str(ie)

        assert AutoHashIndexModel1.FIELDS['value'].hashIndex is True , 'Expected hashIndex to be automatically set to True when an IRCompressedField is right-most, as it forces hashIndex=True'


if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
