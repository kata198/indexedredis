#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRRawField - Test default values for fields
#

# vim: set ts=4 sw=4 st=4 expandtab

import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull
from IndexedRedis.compat_str import tobytes
from IndexedRedis.fields import IRRawField, IRField

# vim: ts=4 sw=4 expandtab

class TestIRRawField(object):
    '''
        TestIRRawField - Test IRRawField
    '''

    KEEP_DATA = False

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.model = None

        if testMethod in (self.test_general, self.test_variousTypes):
            class Model_RawValue(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRRawField('value'),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME='TestIRRawField__ModelRawValue'

            self.model = Model_RawValue

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

        helloWorldRaw = b'\x01Hello World\x01'

        assert updatedFields == {} , 'Expected no updated fields when object is first created.\nExpected: %s\nGot:     %s' %(repr([]), repr(updatedFields) )

        assert obj.value == '', 'Expected default value of IRRawField to be empty string'

        obj.name = 'one'

        obj.save()

        assert obj.getUpdatedFields() == {} , 'Expected no updated fields after object is saved'

        obj.value = u'Goodbye'

        assert obj.value == u'Goodbye' , 'Expected IRRawField value to be u"goodbye" after setting to u"goodbye" (no conversion)'

        obj.value = helloWorldRaw

        assert obj.value == helloWorldRaw , 'Expected IRRawField value to be b"\\x01Hello World\\x01" after setting to "\\x01Hello World\\x01"'

        
        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == helloWorldRaw, 'Expected asDict(forStorage=False) to contain IRRawField value as bytes string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == helloWorldRaw, 'Expected asDict(forStorage=True) to contain IRRawField value as bytes string. \nExpected: %s\nGot:     %s' %(repr(helloWorldRaw), repr(dictForStorage['value']) )

        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating'

        assert updatedFields['value'][0] ==  '', 'Expected old value to be empty string in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == helloWorldRaw , 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving.'

        fetchObj = Model.objects.filter(name='one').first()


        assert fetchObj , 'Expected to be able to fetch object on name="one" after saving.'

        obj = fetchObj

        assert obj.value == helloWorldRaw , 'Expected value of fetched to be converted string (As bytes), %s. Got: %s' %(repr(helloWorldRaw), repr(fetchObj.value), )

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after fetching'

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == helloWorldRaw, 'After fetching, Expected asDict(forStorage=False) to contain IRRawField value as bytes string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == helloWorldRaw, 'After fetching, Expected asDict(forStorage=True) to contain IRRawField value as bytes string. \nExpected: %s\nGot:     %s' %(repr(helloWorldRaw), repr(dictForStorage['value']) )

        obj.value = b'q123'


        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating on fetched object'

        assert updatedFields['value'][0] == helloWorldRaw , 'Expected old value to be %s in updatedFields. Got: %s' %(repr(helloWorldRaw), repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == b'q123' , 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == b'q123', 'After fetching, then updating, Expected asDict(forStorage=False) to contain IRRawField value as bytes string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == b'q123', 'After fetching, then updating, Expected asDict(forStorage=True) to contain IRRawField value as bytes string.\nExpected: %s\nGot:     %s' %(repr(b'q123'), repr(dictForStorage['value']) )

        
        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving'


    def test_variousTypes(self):

        Model = self.model

        obj = Model()

        obj.name = 'two'
        obj.value = 5

        assert obj.value == 5 , 'Expected value when set to int(5) to remain int(5)'


        ids = obj.save()

        assert ids and ids[0] , 'Failed to save with integer value'

        fetchedObj = obj.objects.filter(name='two').first()

        assert fetchedObj , 'Failed to fetch object'

        obj = fetchedObj

        assert obj.value == b'5' , 'Expected value to be raw b"5" from redis'

        obj.value = 'abc'

        ids = obj.save()

        assert ids and ids[0] , 'Failed to save with string value'

        fetchedObj = obj.objects.filter(name='two').first()
        assert fetchedObj , 'Failed to fetch object'

        obj = fetchedObj

        assert obj.value == b'abc' , 'Expected string value to be retrieved as bytes'

        obj.value = 3.14

        ids = obj.save()

        assert ids and ids[0] , 'Failed to save with float value'

        fetchedObj = obj.objects.filter(name='two').first()
        assert fetchedObj , 'Failed to fetch object'

        obj = fetchedObj

        assert type(obj.value) == bytes , 'Expected to fetch saved float as bytes'

        assert obj.value == b'3.14' , 'Expected fetched save float to be b"3.14"'

        assert float(obj.value) == 3.14 , 'Expected float(obj.value) to be as originally saved'

        obj.value = irNull

        ids = obj.save()
        assert ids and ids[0] , 'Failed to save with float value'

        fetchedObj = obj.objects.filter(name='two').first()
        assert fetchedObj , 'Failed to fetch object'

        obj = fetchedObj

        assert obj.value == b'' , 'Expected irNull to be converted to empty string (since no conversion). Got: %s' %( repr(obj.value), )




if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
