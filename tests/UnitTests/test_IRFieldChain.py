#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRFieldChain - Test field chaining
#

# vim: set ts=4 sw=4 st=4 expandtab

import base64
import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull
from IndexedRedis.compat_str import tobytes, to_unicode, setDefaultIREncoding
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

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.model = None

        if testMethod in (self.test_base64AndUnicode, ):
            setDefaultIREncoding('ascii')
            class Model_Base64Unicode(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRFieldChain('value', [IRUnicodeField(encoding='utf-8'), IRBase64Field(encoding='utf-8')], defaultValue=irNull),
                    IRFieldChain('value2', [IRUnicodeField(encoding='utf-8'), IRBase64Field(encoding='utf-8')], defaultValue='qqz'),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME='TestIRFieldChain__ModelBase64Unicode'

            self.model = Model_Base64Unicode
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

        if testMethod in (self.test_base64AndUnicode, ):
            setDefaultIREncoding(sys.getdefaultencoding())


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



if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab