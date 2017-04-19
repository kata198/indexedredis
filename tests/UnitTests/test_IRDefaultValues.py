#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRDefaultValues - Test default values for fields
#

# vim: set ts=4 sw=4 st=4 expandtab

import datetime

import sys
import IndexedRedis
import subprocess
from IndexedRedis import IndexedRedisModel, IRField, irNull, toggleDeprecatedMessages
from IndexedRedis.fields import IRFieldChain, IRBase64Field, IRUnicodeField, IRClassicField
from IndexedRedis.fields.FieldValueTypes import IRDatetimeValue, IRJsonValue

# vim: ts=4 sw=4 expandtab

class TestIRDefaultValues(object):
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

        if testMethod == self.test_basicDefaults:
            class Model_Basic_Defaults(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRField('someNum', valueType=int, defaultValue=-1),
                    IRField('someStr', valueType=str, defaultValue='unset'),
                    IRField('gblDefault'),
                    IRClassicField('classic')
                ]

                INDEXED_FIELDS = ['name', 'someNum', 'someStr', 'gblDefault', 'classic']

                KEY_NAME='TestIRDefaultValues__basicDefaults_1'

            self.model = Model_Basic_Defaults

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

    def test_basicDefaults(self):
        '''
            test_basicDefaults - Test basic defaultValue functionality
        '''
        
        Model = self.model

        obj = Model()

        self._assert_fieldEquals(obj, 'name', irNull, 'default for IRField without explicit defaultValue', 'irNull')
        self._assert_fieldEquals(obj, 'someNum', -1,  'default for IRField(valueType=int, defaultValue=-1)')
        self._assert_fieldEquals(obj, 'someStr', 'unset',  'default for IRField(valueType=str, defaultValue="unset")')
        self._assert_fieldEquals(obj, 'gblDefault', irNull, 'default for IRField without explicit defaultValue', 'irNull')
        self._assert_fieldEquals(obj, 'classic', "", 'default for IRClassicField', '"" (empty string)')

        assert not obj.getUpdatedFields() , 'Expected no fields to be listed as "updated" when none have been set. Got: %s' %(repr(obj.getUpdatedFields()), )

        obj.name = 'fetch1'
        obj.save()

        self._assert_fieldEquals(obj, 'name', 'fetch1', 'after saving value for IRField')
        self._assert_fieldEquals(obj, 'someNum', -1,  'after saving for IRField(valueType=int, defaultValue=-1)')
        self._assert_fieldEquals(obj, 'someStr', 'unset',  'after saving for IRField(valueType=str, defaultValue="unset")')
        self._assert_fieldEquals(obj, 'gblDefault', irNull, 'after saving for IRField without explicit defaultValue', 'irNull')
        self._assert_fieldEquals(obj, 'classic', "", 'after saving for IRClassicField', '"" (empty string)')


        objFetched = Model.objects.filter(name='fetch1').first()

        assert objFetched , 'Expected to be able to fetch object from name="fetch1"'

        obj = objFetched


        self._assert_fieldEquals(obj, 'name', 'fetch1', 'after fetching value for IRField')
        self._assert_fieldEquals(obj, 'someNum', -1,  'after fetching for IRField(valueType=int, defaultValue=-1)')
        self._assert_fieldEquals(obj, 'someStr', 'unset',  'after fetching for IRField(valueType=str, defaultValue="unset")')
        self._assert_fieldEquals(obj, 'gblDefault', irNull, 'after fetching for IRField without explicit defaultValue', 'irNull')
        self._assert_fieldEquals(obj, 'classic', "", 'after fetching for IRClassicField', '"" (empty string)')

        obj.someNum = 22
        obj.someStr = 'hello goodbye'
        obj.gblDefault = 'zz'
        obj.classic = irNull

        obj.save()

        self._assert_fieldEquals(obj, 'name', 'fetch1', 'after updating value for IRField')
        self._assert_fieldEquals(obj, 'someNum', 22,  'after changing IRField(valueType=int, defaultValue=-1) to non-default value')
        self._assert_fieldEquals(obj, 'someStr', 'hello goodbye',  'after changing  IRField(valueType=str, defaultValue="unset") to non-default value')
        self._assert_fieldEquals(obj, 'gblDefault', 'zz', 'after changing IRField without explicit defaultValue to non-default value')
        self._assert_fieldEquals(obj, 'classic', irNull, 'after changing IRClassicField from default to irNull', 'irNull')

        objFetched = Model.objects.filter(name='fetch1').first()

        assert objFetched , 'Expected to be able to fetch object from name="fetch1"'

        obj = objFetched


        self._assert_fieldEquals(obj, 'name', 'fetch1', 'fetched after updating value for IRField')
        self._assert_fieldEquals(obj, 'someNum', 22,  'fetched after changing IRField(valueType=int, defaultValue=-1) to non-default value')
        self._assert_fieldEquals(obj, 'someStr', 'hello goodbye',  'fetched after changing  IRField(valueType=str, defaultValue="unset") to non-default value')
        self._assert_fieldEquals(obj, 'gblDefault', 'zz', 'fetched after changing IRField without explicit defaultValue to non-default value')
        self._assert_fieldEquals(obj, 'classic', irNull, 'fetched after changing IRClassicField from default to irNull', 'irNull')


if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py "%s" %s' %(sys.argv[0], ' '.join(sys.argv[1:])), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
