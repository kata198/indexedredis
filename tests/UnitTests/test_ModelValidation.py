#!/usr/bin/env python

# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestModelValidation - GoodTests unit tests validating model validation
#

# vim: set ts=4 sw=4 expandtab

import sys
import IndexedRedis
import subprocess
from IndexedRedis import IndexedRedisModel, IRField, InvalidModelException, validatedModels

# vim: ts=4 sw=4 expandtab

# TODO: More tests
class TestModelValidation(object):

    @staticmethod
    def __assertExceptions(name, testMethod, gotException, gotWrongException, contains):
        assert bool(gotWrongException) is False, '[%s] Got exception for "%s", but was not expected (InvalidModelException). Got: " %s "' %(testMethod, str(gotWrongException))
        assert bool(gotException) is True, '[%s] Did not get InvalidModelException for "%s", but should have.' %(testMethod, name)
        if contains:
            if type(contains) not in (list, tuple):
                contains = [contains]
            for mustContain in contains:
                assert mustContain  in str(gotException), '[%s] Did not get expected message (containing "%s") for InvalidModelException. Got: " %s "' %(testMethod, mustContain, str(gotException),)

    @staticmethod
    def __assertNoExceptions(name, testMethod, gotException, gotWrongException):
        assert bool(gotException) is False, '[%s] Got InvalidModelException for %s but expected model to be valid. Got: " %s "' %(testMethod, name, str(gotException))
        assert bool(gotWrongException) is False, '[%s] Got an Exception for %s but expected model to be valid. Got: " %s "' %(testMethod, name, str(gotWrongException))

    def __testMethods(self, model, name, contains='', shouldHaveException=True):
        # Create two models so we can validate with two methods
        gotException = False
        gotWrongException = False
        testMethod = 'init'

        validatedModels.clear()
        try:
            myObj = model()
        except InvalidModelException as e:
            gotException = e
        except Exception as e:
            gotWrongException = e

        if shouldHaveException is True:
            self.__assertExceptions(name, testMethod, gotException, gotWrongException, contains)
        else:
            self.__assertNoExceptions(name, testMethod, gotException, gotWrongException)
            

        gotException = False
        gotWrongException = False
        testMethod = 'objects'

        validatedModels.clear()
        try:
            myObj = model.objects.first()
        except InvalidModelException as e:
            gotException = e
        except Exception as e:
            gotWrongException = e

        if shouldHaveException is True:
            self.__assertExceptions(name, testMethod, gotException, gotWrongException, contains)
        else:
            self.__assertNoExceptions(name, testMethod, gotException, gotWrongException)


    def test_NoKeyName(self):
        '''
            test_NoKeyName - Test that lack of key name raises InvalidModelException.
        '''

        class NoKeyModel(IndexedRedisModel):
            FIELDS = ['fielda', 'fieldb']

            INDEXED_FIELDS = ['fielda']

        self.__testMethods(NoKeyModel, 'no KEY_NAME defined', 'KEY_NAME', shouldHaveException=True)

    def test_NoFields(self):
        '''
            test_NoFields - Test that lack of FIELDS raises InvalidModelException
        '''
        
        class NoFields(IndexedRedisModel):
            KEY_NAME = 'Test_NoFields'

        self.__testMethods(NoFields, 'No Fields', 'FIELDS', shouldHaveException=True)

    def test_InvalidIndexedField(self):
        '''
            test_InvalidIndexedField - Test that a field in INDEXED_FIELD not in FIELDS does not validate.
        '''

        class InvalidIndexedField(IndexedRedisModel):
            FIELDS = ['a', 'b']
            INDEXED_FIELDS = ['c']
            KEY_NAME = 'Test_InvalidIndexedField'

        self.__testMethods(InvalidIndexedField, 'Invalid Indexed Field', ['INDEXED_FIELDS', 'FIELDS'], shouldHaveException=True)

    def test_ValidModel(self):
        '''
            test_ValidModel - Test that a model passes validation
        '''

        class ValidModel(IndexedRedisModel):
            FIELDS = ['a', 'b']
            INEXED_FIELDS = ['a']

            KEY_NAME='Test_ValidModel'

        self.__testMethods(ValidModel, 'Valid Model', '', shouldHaveException=False)

            
if __name__ == '__main__':
    pipe  = subprocess.Popen('GoodTests.py "%s"' %(sys.argv[0],), shell=True).wait()

# vim: set ts=4 sw=4 expandtab
