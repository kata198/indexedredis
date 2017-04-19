#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRUnicodeField - Test the IRUnicodeField
#

# vim: set ts=4 sw=4 st=4 expandtab

import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull
from IndexedRedis.compat_str import tobytes, setDefaultIREncoding, to_unicode
from IndexedRedis.fields import IRUnicodeField, IRField, IRUnicodeField

# vim: ts=4 sw=4 expandtab

class TestIRUnicodeField(object):
    '''
        TestIRUnicodeField - Test some IRUnicodeField stuff
    '''

    KEEP_DATA = False

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.model = None

        setDefaultIREncoding('ascii') # Make sure IRField stuff would normally fail with utf-8 specific codes

        self.prettyPictures = b' \xe2\x9c\x8f \xe2\x9c\x90 \xe2\x9c\x91 \xe2\x9c\x92 \xe2\x9c\x93 \xe2\x9c\x94 \xe2\x9c\x95 \xe2\x9c\x96 \xe2\x9c\x97 \xe2\x9c\x98 \xe2\x9c\x99 \xe2\x9c\x9a \xe2\x9c\x9b \xe2\x9c\x9c \xe2\x9c\x9d \xe2\x9c\x9e \xe2\x9c\x9f \xe2\x9c\xa0 \xe2\x9c\xa1 \xe2\x9c\xa2 \xe2\x9c\xa3 \xe2\x9c\xa4 \xe2\x9c\xa5 \xe2\x9c\xa6 \xe2\x9c\xa7 \xe2\x9c\xa9 \xe2\x9c\xaa \xe2\x9c\xab '

        if testMethod in (self.test_general, ):
            class Model_GeneralUnicode(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRUnicodeField('value', defaultValue=irNull, encoding='utf-8'),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME='TestIRUnicodeField__GeneralUnicode'

            self.model = Model_GeneralUnicode
        elif testMethod == self.test_defaultValue:
            class Model_UnicodeDefaultValue(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRUnicodeField('value', defaultValue=u'qqq', encoding='utf-8'),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRUnicodeField__UnicodeDefaultValue'

            self.model = Model_UnicodeDefaultValue

        # If KEEP_DATA is False (debug flag), then delete all objects before so prior test doesn't interfere
        if self.KEEP_DATA is False and self.model:
            self.model.objects.delete()

    def teardown_method(self, testMethod):
        '''
            teardown_method - Called after every method.

                If self.model is set, will delete all objects relating to that model. To retain objects for debugging, set TestIRField.KEEP_DATA to True.
        '''
        setDefaultIREncoding('utf-8') # Revert back to utf-8 encoding

        if self.model and self.KEEP_DATA is False:
            self.model.objects.delete()


    def test_general(self):
        
        Model = self.model
        prettyPictures = self.prettyPictures
        prettyPicturesUnicode = to_unicode(prettyPictures, encoding='utf-8')

        obj = Model()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected no updated fields when object is first created.\nExpected: %s\nGot:     %s' %(repr([]), repr(updatedFields) )

        assert obj.value == irNull , 'Expected default value of IRUnicodeField to be irNull when defaultValue=irNull'

        obj.name = 'one'

        obj.save()

        assert obj.getUpdatedFields() == {} , 'Expected no updated fields after object is saved'

        obj.value = prettyPictures

        assert obj.value == prettyPicturesUnicode , 'Expected IRUnicodeField value to be some unicode after setting'

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == prettyPicturesUnicode , 'Expected asDict(forStorage=False) to contain IRUnicodeField value as unicode string. Got: %s' %(repr(dictConverted['value']), ) 
        assert dictForStorage['value'] == prettyPictures , 'Expected asDict(forStorage=True) to contain IRUnicodeField that was bytes.\nExpected: %s\nGot:     %s' %(repr(prettyPictures), repr(dictForStorage['value']) )

        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating'

        assert updatedFields['value'][0] == irNull , 'Expected old value to be irNull in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == prettyPicturesUnicode , 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving.'

        fetchObj = Model.objects.filter(name='one').first()


        assert fetchObj , 'Expected to be able to fetch object on name="one" after saving.'

        obj = fetchObj

        assert obj.value == prettyPicturesUnicode , 'Expected value of fetched to be unicode string, %s. Got: %s' %(repr(prettyPicturesUnicode), repr(fetchObj.value), )

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after fetching'

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == prettyPicturesUnicode, 'After fetching, Expected asDict(forStorage=False) to contain IRUnicodeField value as unicode string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == prettyPictures, 'After fetching, Expected asDict(forStorage=True) to contain IRUnicodeField as bytes.\nExpected: %s\nGot:     %s' %(repr(prettyPictures), repr(dictForStorage['value']) )

        obj.value = b'q123'


        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating on fetched object'

        assert updatedFields['value'][0] == prettyPicturesUnicode , 'Expected old value to be b"Hello World" in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] == u'q123' , 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        dictConverted = obj.asDict(forStorage=False, strKeys=True)
        dictForStorage = obj.asDict(forStorage=True, strKeys=True)

        assert dictConverted['value'] == u'q123', 'After fetching, then updating, Expected asDict(forStorage=False) to contain IRUnicodeField value as unicode string. Got: %s' %(dictConverted['value'], )
        assert dictForStorage['value'] == b'q123' , 'After fetching, then updating, Expected asDict(forStorage=True) to contain IRUnicodeField as bytes.\nExpected: %s\nGot:     %s' %(repr(u'q123'), repr(dictForStorage['value']) )

        
        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving'

    def test_defaultValue(self):

        Model = self.model

        obj = Model()

        assert obj.value == u'qqq' , 'Expected defaultValue to be applied to a unicode field.\nExpected: b"woobley"\nGot:     %s' %(repr(obj.value), )

        obj.name = 'test'

        obj.save()

        assert obj.value == u'qqq' , 'Expected defaultValue to remain on a unicode field after saving'

        objFetched = Model.objects.filter(name='test').first()
        assert objFetched , 'Expected to be able to fetch object'

        obj = objFetched

        assert obj.value == u'qqq' , 'Expected defaultValue to remain on a unicode field after fetching'

        obj.value = 'cheesy'

        obj.save()

        objFetched = Model.objects.filter(name='test').first()
        assert objFetched , 'Expected to be able to fetch object'

        obj = objFetched

        assert obj.value == u'cheesy' , 'Expected to be able to change value from default.'


if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
