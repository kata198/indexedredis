#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRFixedPointField - Test default values for fields
#

# vim: set ts=4 sw=4 st=4 expandtab

import copy
import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull
from IndexedRedis.compat_str import tobytes
from IndexedRedis.fields import IRFixedPointField, IRField

# vim: ts=4 sw=4 expandtab

class TestIRFixedPointField(object):
    '''
        TestIRFixedPointField - Test IRFixedPointField
    '''

    KEEP_DATA = False

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.model = None

        if testMethod in (self.test_general, ):
            class Model_FixedPointValue(IndexedRedisModel):
                
                FIELDS = [
                    IRField('name'),
                    IRFixedPointField('value', defaultValue=irNull),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME='TestIRFixedPointField__ModelFixedPointValue'

            self.model = Model_FixedPointValue
        elif testMethod in (self.test_defaultValue, ):
            class Model_FixedPointDefaultValue(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRFixedPointField('value', defaultValue=9.91775),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRFixedPointField__ModelFixedPointDefaultValue'

            self.model = Model_FixedPointDefaultValue

        elif testMethod in (self.test_indexFixedPoint, ):
            class Model_IndexFixedPoint(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRFixedPointField('value', defaultValue=irNull),
                    IRFixedPointField('value2', defaultValue=1.11),
                ]

                INDEXED_FIELDS = ['name', 'value', 'value2']

                KEY_NAME = 'TestIRFixedPointField__IndexFixedPoint'

            self.model = Model_IndexFixedPoint

        elif testMethod == self.test_decimalPlaces:
            class Model_DecimalPlaces(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRFixedPointField('value1', decimalPlaces=1),
                    IRFixedPointField('value4', decimalPlaces=4),
                    IRFixedPointField('value9', decimalPlaces=9),
                    IRFixedPointField('value4MoreDef', decimalPlaces=4, defaultValue=5.123456),
                ]

                INDEXED_FIELDS = ['name', 'value1', 'value4', 'value9']

                KEY_NAME = 'TestIRFixedPointField__DecimalPlaces'

            self.model = Model_DecimalPlaces

        # If KEEP_DATA is False (debug flag), then delete all objects before so prior test doesn't interfere
        if self.KEEP_DATA is False and self.model:
            self.model.reset([])

    @staticmethod
    def asFloatStr(val, decimalPlaces):
        formatStr = "%." + str(decimalPlaces) + "f"

        return formatStr % (val, )

    def teardown_method(self, testMethod):
        '''
            teardown_method - Called after every method.

                If self.model is set, will delete all objects relating to that model. To retain objects for debugging, set TestIRField.KEEP_DATA to True.
        '''

        if self.model and self.KEEP_DATA is False:
            self.model.reset([])


    def test_general(self):
        
        Model = self.model

        obj = Model()

        updatedFields = obj.getUpdatedFields()

        floatVal = 9.17256
        numDecimalPlaces = obj.FIELDS[obj.FIELDS.index('value')].decimalPlaces
        floatStr = self.asFloatStr(floatVal, numDecimalPlaces)


        assert updatedFields == {} , 'Expected no updated fields when object is first created.\nExpected: %s\nGot:     %s' %(repr([]), repr(updatedFields) )

        assert obj.value == irNull , 'Expected default value of IRFixedPointField to be irNull when defaultValue=irNull'

        obj.name = 'one'

        obj.save()

        assert obj.getUpdatedFields() == {} , 'Expected no updated fields after object is saved'


        obj.value = '5.66'

        assert obj.value == 5.66 , 'Expected setting value as string to be converted to float'

        obj.value = floatVal

        assert obj.value == floatVal, 'Expected IRFixedPointField value to be the float value it was set to'

        
        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))


        assert dictConverted['value'] == floatVal, 'Expected asDict(forStorage=False) to contain value as float Got: %s' %( repr(dictConverted['value']), )
        assert dictForStorage['value'] == floatStr, 'Expected asDict(forStorage=True) to contain IRFixedPointField value fixed string \nExpected: %s\nGot:     %s' %(repr(floatStr), repr(dictForStorage['value']) )

        updatedFields = obj.getUpdatedFields()

        assert 'value' in updatedFields , 'Expected "value" to show in updated fields after updating'

        assert updatedFields['value'][0] == irNull , 'Expected old value to be irNull in updatedFields. Got: %s' %(repr(updatedFields['value'][0]), )
        assert updatedFields['value'][1] ==  floatVal, 'Expected converted value to be new value in updatedFields. Got: %s' %(repr(updatedFields['value'][1]), )

        obj.save()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after saving.'

        fetchObj = Model.objects.filter(name='one').first()


        assert fetchObj , 'Expected to be able to fetch object on name="one" after saving.'

        obj = fetchObj

        assert obj.value == floatVal, 'Expected value of fetched to be float value %s. Got: %s' %(repr(floatVal), repr(fetchObj.value), )

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {} , 'Expected updatedFields to be clear after fetching'

        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))

        assert dictConverted['value'] == floatVal, 'After fetching, Expected asDict(forStorage=False) to contain IRFixedPointField value as float Got: %s' %( repr(dictConverted['value']), )
        assert dictForStorage['value'] == floatStr, 'After fetching, Expected asDict(forStorage=True) to contain IRFixedPointField value as fixed string. \nExpected: %s\nGot:     %s' %(repr(floatStr), repr(dictForStorage['value']) )


    def test_defaultValue(self):

        Model = self.model

        obj = Model()

        valField = obj.FIELDS[obj.FIELDS.index('value')]

        numDecimalPlaces = valField.decimalPlaces
        defaultValue = 9.91775
        defaultValueStr = self.asFloatStr(defaultValue, numDecimalPlaces)

        assert valField.defaultValue == defaultValue , 'Expected defaultValue attribute to be set'

        assert obj.value == defaultValue , 'Expected defaultValue to be applied to a IRFixedPointField field.\nExpected: %f\nGot:     %s' %(defaultValue, repr(obj.value), )

        obj.name = 'test'

        ids = obj.save()

        assert ids and ids[0] , 'Failed to save value'

        assert obj.value == defaultValue , 'Expected defaultValue to remain on a fixed point field after saving'

        objFetched = Model.objects.filter(name='test').first()
        assert objFetched , 'Expected to be able to fetch object'

        obj = objFetched

        assert obj.value == defaultValue , 'Expected defaultValue to remain on a fixed point field after fetching'

        floatVal = 3.14
        floatValStr = self.asFloatStr(floatVal, numDecimalPlaces)

        obj.value = floatVal

        ids = obj.save()

        assert ids and ids[0] , 'Failed to save object'

        objFetched = Model.objects.filter(name='test').first()
        assert objFetched , 'Expected to be able to fetch object'

        obj = objFetched

        assert obj.value == floatVal , 'Expected to be able to change value from default.'

    def test_indexFixedPoint(self):

        Model = self.model

        obj = Model()

        obj.name = 'test'

        ids = obj.save()

        assert ids and ids[0] , 'Failed to save object'

        floatVal = 2.61
        numDecimalPlaces = obj.FIELDS[obj.FIELDS.index('value')].decimalPlaces
        floatStr = self.asFloatStr(floatVal, numDecimalPlaces)

        otherFloatVal = 5.66
        otherNumDecimalPlaces = obj.FIELDS[obj.FIELDS.index('value')].decimalPlaces
        otherFloatStr = self.asFloatStr(floatVal, numDecimalPlaces)

        # Add a "distraction" object
        otherObj = Model()
        otherObj.value = floatVal
        otherObj.value2 = otherFloatVal

        otherObj.save()

        objFetched = Model.objects.filter(value=irNull).first()

        assert objFetched , 'Failed to fetch an object with default value (irNull) on a fixed point field'

        d1 = obj.asDict(includeMeta=True, forStorage=False, strKeys=True)
        d2 = objFetched.asDict(includeMeta=True, forStorage=False, strKeys=True)

        assert objFetched == obj , 'Object fetched was not expected object.\nExpected: %s\n\nGot:     %s\n' %( 
                obj.asDict(includeMeta=True, forStorage=False, strKeys=True),
                objFetched.asDict(includeMeta=True, forStorage=False, strKeys=True)
                )

        objFetched = Model.objects.filter(value2=otherFloatVal).first()

        assert objFetched , 'Failed to fetch object using a non-default value on fixed point field'

        assert objFetched == otherObj , 'Object fetched was not expected object.\nExpected: %s\n\nGot:     %s\n' %( 
                otherObj.asDict(includeMeta=True, forStorage=False, strKeys=True),
                objFetched.asDict(includeMeta=True, forStorage=False, strKeys=True)
                )

    def test_decimalPlaces(self):
        
        #IRFixedPointField('value1', decimalPlaces=1),
        #IRFixedPointField('value4', decimalPlaces=4),
        #IRFixedPointField('value9', decimalPlaces=9),
        #IRFixedPointField('value4MoreDef', decimalPlaces=4, defaultValue=5.123456),

        Model = self.model

        obj = Model()

        assert obj.value4MoreDef == 5.1235 , 'Expected when default value has more decimal places than the field supports, for it to be rounded.\nExpected: 5.1235\nGot:     %f' %(obj.value4MoreDef, )

        obj.value1 = '1.41'

        assert obj.value1 == 1.4 , 'Expected "1.41" to be converted to float(1.4) when decimalPlaces=1. Got: %s' %(repr(obj.value1, ))

        obj.value1 = '1.48'

        assert obj.value1 == 1.5 , 'Expected "1.48" to be converted to float(1.48) when decimalPlaces=1. Got: %s' %(repr(obj.value1, ))

        obj = Model(value1='1.48')

        assert obj.value1 == 1.5 , 'Expected "1.48" to be converted to float(1.48) when decimalPlaces=1 (constructor). Got: %s' %(repr(obj.value1, ))


        val = '99145.3362816911682'

        valFloat = float(val)
        rvalFloat1 = round(valFloat, 1)
        floatStr1 = self.asFloatStr(valFloat, 1)
        rvalFloat4 = round(valFloat, 4)
        floatStr4 = self.asFloatStr(valFloat, 4)
        rvalFloat9 = round(valFloat, 9)
        floatStr9 = self.asFloatStr(valFloat, 9)
 
        obj.value1 = valFloat
        obj.value4 = valFloat
        obj.value9 = valFloat


        try:
            dictConverted = obj.asDict(forStorage=False, strKeys=True)
            dictForStorage = obj.asDict(forStorage=True, strKeys=True)
        except Exception as e:
            raise AssertionError('Expected to be able to convert to dict for both storage and non-storage. Got exception: %s %s' %(e.__class__.__name__, str(e)))


        assert dictConverted['value1'] == rvalFloat1 , 'Expected converted value1 to be %f. Got %f. ' %(rvalFloat1, dictConverted['value1'])
        assert dictConverted['value4'] == rvalFloat4 , 'Expected converted value4 to be %f. Got %f. ' %(rvalFloat4, dictConverted['value4'])
        assert dictConverted['value9'] == rvalFloat9 , 'Expected converted value9 to be %f. Got %f. ' %(rvalFloat9, dictConverted['value9'])

        assert dictForStorage['value1'] == floatStr1 , 'Expected storage value1 to be %s. Got %s. ' %( floatStr1, dictForStorage['value1'] )
        assert dictForStorage['value4'] == floatStr4 , 'Expected storage value4 to be %s. Got %s. ' %( floatStr4, dictForStorage['value4'] )
        assert dictForStorage['value9'] == floatStr9 , 'Expected storage value9 to be %s. Got %s. ' %( floatStr9, dictForStorage['value9'] )


        ids = obj.save()

        assert ids and ids[0] , 'Failed to save object'

        objFetched = Model.objects.filter(value1=rvalFloat1).first()
        assert objFetched , 'Failed to fetch object with exact value for value1'
        objFetched = Model.objects.filter(value4=rvalFloat4).first()
        assert objFetched , 'Failed to fetch object with exact value for value4'
        objFetched = Model.objects.filter(value9=rvalFloat9).first()
        assert objFetched , 'Failed to fetch object with exact value for value9'


        obj = objFetched

        assert obj.value1 == rvalFloat1 , 'Expected value1 to be correct after fetching. Expected: %f Got: %f' %(rvalFloat1, obj.value1)
        assert obj.value4 == rvalFloat4 , 'Expected value4 to be correct after fetching. Expected: %f Got: %f' %(rvalFloat4, obj.value4)
        assert obj.value9 == rvalFloat9 , 'Expected value9 to be correct after fetching. Expected: %f Got: %f' %(rvalFloat9, obj.value9)

        objFetched = Model.objects.filter(value1=rvalFloat9).first()
        assert objFetched , 'Expected to be able to fetch using a value of higher precision with same rounded-value as index. Failed on dec=1'
        objFetched = Model.objects.filter(value4=rvalFloat9).first()
        assert objFetched , 'Expected to be able to fetch using a value of higher precision with same rounded-value as index. Failed on dec=4'

        objFetched = Model.objects.filter(value4=val).first()
        assert objFetched , 'Expected to be able to fetch using a string of higher precision with same rounded-value as index.'

        objFetched = Model.objects.filter(value9=rvalFloat4).first()
        assert not objFetched , 'Expected to NOT be able to fetch object using a lower-precision value than the index, where those two are different values.'

        OrigModel = Model.copyModel()

        ## NOTE - model is CHANGED AFTER THIS POINT ##

        index = "%.5f" % (round(float(Model.objects.first().value4), 5), )

        # Increase precision by 1 on value4
        Model.FIELDS[Model.FIELDS.index('value4')].decimalPlaces = 5
        
#        obj = Model.objects.first()

        forStorageDict = obj.asDict(forStorage=True)

        floatStr5 = self.asFloatStr(rvalFloat4, 5)
        assert forStorageDict['value4'] == floatStr5 , 'TEST expected that increasing decimal places on model field would take affect. It did not?'

        # Should not work as different fixed point representation:
        objFetched = Model.objects.filter(value4=val).first()
        assert not objFetched , 'Expected NOT to still be able to fetch on index of higher precision, when value changes, after decimalPlaces was increased since save'

        objFetched = Model.objects.filter(value4=rvalFloat4).first()
        assert not objFetched , 'Expected NOT to still be able to fetch an index of former precision, when value rounds to the same float but DIFFERENT fixed-point (different final-2 places) after decimalPlaces was increased since save'

        objFetched = Model.objects.filter(value4=rvalFloat9).first()
        assert not objFetched ,'Expected NOT to still be able to fetch an index of former precision, when value rounds to the same float but DIFFERENT fixed-point (extra 0s) after decimalPlaces was increased since save'

        # NOTE: Reindex will leave this field indexed on two different values for the field that changed -
        #   So we must use reset instead of Model.objects.reindex()
        Model.reset(Model.objects.all())

        # Now index is .33630 - because it was originally rounded out 4 from val, no longer will match round(val, 5) which is .33628

        newVal = '99145.3363012'

        objFetched = Model.objects.filter(value4=99145.33630).first()
        assert objFetched , 'After reindex, expected to be able to fetch on new index'

        objFetched = OrigModel.objects.filter(value4=99145.3363).first()
        assert not objFetched , 'After reindex, expected NOT to be able to fetch on the old index'


if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
