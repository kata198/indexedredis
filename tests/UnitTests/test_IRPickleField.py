#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRPickle - GoodTests unit tests validating IRPickleField
#

# Import and apply the properties (like Redis connection parameters) for this test.
import TestProperties

# vim: set ts=4 sw=4 expandtab


import sys
import subprocess
from IndexedRedis import IndexedRedisModel
from IndexedRedis.fields import IRPickleField, IRField

# vim: ts=4 sw=4 expandtab

class TestIRField(object):
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

        # Models should be given different names and key names so they are validated again.
        if testMethod in (self.test_withStrings, self.test_withList):
            class SimpleIRFieldModel(IndexedRedisModel):

                FIELDS = [ IRField('name'), IRPickleField('data') ]
                INDEXED_FIELDS = ['name']

                KEY_NAME = 'Test_SimpleIRPickleFieldModel'

            self.model = SimpleIRFieldModel

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


    def test_withStrings(self):
        SimpleIRPickleFieldModel = self.model

        myObj = SimpleIRPickleFieldModel(name='test1')

        myObj.save()

        assert not myObj.data , 'Expected undefined data to be False'

        myObj.data = 'hello'

        myObj.save()

        myObjRefetched = SimpleIRPickleFieldModel.objects.filter(name='test1').first()

        assert myObjRefetched.data == 'hello' , 'Expected saved data to be retained'


        myObjRefetched.data = 'goodbye'

        myObjRefetched.save()

        myObj = myObjRefetched

        myObjRefetched = SimpleIRPickleFieldModel.objects.filter(name='test1').first()

        assert myObjRefetched.data == 'goodbye', 'Expected data to be retained'

        myObj2 = SimpleIRPickleFieldModel(name='test2', data='cheese')

        myObj2.save()

        myObj2Refetched = SimpleIRPickleFieldModel.objects.filter(name='test2').first()

        assert myObj2Refetched.data == 'cheese' , 'Expected to be able to specify data in constructor'


        myObj2 = myObj2Refetched

        myObj2.data = ''

        myObj2.save()

        myObj2Refetched = SimpleIRPickleFieldModel.objects.filter(name='test2').first()

        assert not myObj2Refetched.data , 'Expected to be able to remove data on pickled field'


    def test_withList(self):
        '''
            test_withList - Tests using IRPickleField with a list being pickled
        '''
        SimpleIRPickleFieldModel = self.model

        myObj = SimpleIRPickleFieldModel(name='test1')

        myObj.data = ['one', 'two']

        myObj.save()

        myObjRefetched = SimpleIRPickleFieldModel.objects.filter(name='test1').first()

        assert myObjRefetched.data == ['one', 'two'] , 'Expected fetched list data to match what was saved. Got back: %s' %(repr(myObjRefetched.data),)

        myObj = myObjRefetched

        myObj.data.append('three')

        myObj.save()

        assert myObj._origData['data'] == ['one', 'two', 'three'], 'Expected _origData to now contain the latest-saved value, it contains: %s' %(repr(myObj._origData['data']),)

        myObjRefetched = SimpleIRPickleFieldModel.objects.filter(name='test1').first()

        assert myObj.data == ['one', 'two', 'three'] , 'Expected to be able to modify and update a pickled list. Got back: %s' %(repr(myObj.data),)

        bytes_data = b'\x11\x22\x33\x44\xAA\xBB\xCC'
        bytes_data2 = b'\xDD\xEE'

        myObj.data = bytes_data

        myObj.save()

        myObjRefetched = SimpleIRPickleFieldModel.objects.filter(name='test1').first()
        
        assert myObjRefetched.data == bytes_data , 'Expected to be able to save bytes data in IRPickleField'

        myObj = myObjRefetched
        
        myObj.data = bytes_data2
        myObj.save()


        myObjRefetched = SimpleIRPickleFieldModel.objects.filter(name='test1').first()
        
        assert myObjRefetched.data == bytes_data2 , 'Expected to be able to modify bytes data in IRPickleField.\nGot:  \t\t%s\nExpected:\t%s' %(repr(bytes_data2), repr(myObjRefetched.data))

        


if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
