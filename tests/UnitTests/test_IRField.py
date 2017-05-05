#!/usr/bin/env python

# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRField - GoodTests unit tests validating model validation
#

# Import and apply the properties (like Redis connection parameters) for this test.
import TestProperties

# vim: set ts=4 sw=4 expandtab

import datetime

import sys
import subprocess

from IndexedRedis import IndexedRedisModel, IRField, irNull, toggleDeprecatedMessages
from IndexedRedis.fields.FieldValueTypes import IRDatetimeValue, IRJsonValue

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
        if testMethod in (self.test_simpleIRFieldSaveAndFetch, self.test_updatedFieldsAfterSave):
            class SimpleIRFieldModel(IndexedRedisModel):

                FIELDS = [ IRField('name', valueType=str), IRField('favColour') ]
                INDEXED_FIELDS = ['name', 'favColour']

                KEY_NAME = 'Test_SimpleIRFieldModel'

            self.model = SimpleIRFieldModel
        elif testMethod == self.test_emptyStrNotNull:
            class SimpleIRFieldModel_WithClassicField(IndexedRedisModel):
                FIELDS = [ IRField('name', valueType=str), IRField('favColour'), 'strField' ]
                INDEXED_FIELDS = ['name', 'favColour']

                KEY_NAME = 'Test_SimpleIRFieldModel_WithClassicField'

            self.model = SimpleIRFieldModel_WithClassicField

            toggleDeprecatedMessages(False)

        elif testMethod == self.test_noneFieldValue:
            class SimpleIRFieldModel_NoneField(IndexedRedisModel):
                FIELDS = [ IRField('name'), IRField('nonefield', valueType=None)]
                INDEXED_FIELDS = ['name']

                KEY_NAME = 'Test_SimpleIRFieldModel_NoneField'

            self.model = SimpleIRFieldModel_NoneField
        elif testMethod in (self.test_intFieldValue, self.test_intFieldNulls):
            class SimpleIRFieldModel_Number(IndexedRedisModel):
                FIELDS = [ IRField('name'), IRField('number', valueType=int)]
                INDEXED_FIELDS = ['name', 'number']

                KEY_NAME = 'Test_SimpleIRFieldModel_Number'

            self.model = SimpleIRFieldModel_Number
        elif testMethod == self.test_datetimeFieldValue:
            class SimpleIRFieldModel_Timestamp(IndexedRedisModel):
                FIELDS = [ IRField('name'), IRField('timestamp', valueType=IRDatetimeValue) ]
                INDEXED_FIELDS = ['name', 'timestamp']

                KEY_NAME = 'Test_SimpleIRFieldModel_Timestamp'

            self.model = SimpleIRFieldModel_Timestamp
        elif testMethod == self.test_jsonFieldValue:
            class SimpleIRFieldModel_Json(IndexedRedisModel):
                FIELDS = [ IRField('name'), IRField('jsonData', valueType=IRJsonValue) ]
                INDEXED_FIELDS = ['name']

                KEY_NAME = 'Test_SimpleIRFieldModel_Json'

            self.model = SimpleIRFieldModel_Json

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

        if testMethod == self.test_emptyStrNotNull:
            toggleDeprecatedMessages(True)

    def test_simpleIRFieldSaveAndFetch(self):
        '''
            test_simpleIRFieldSaveAndFetch - Test that basic IRField's (default type or str type) have same behaviour as a string of field name (pre-IRField)
        '''
        SimpleIRFieldModel = self.model

        myObj = SimpleIRFieldModel(name='Tim', favColour='purple')
        ids = myObj.save()

        assert ids, 'Expected to get ids returned from save, but did not.'
        assert ids[0] == myObj._id , 'Expected id to be set on saved object, but was not.'

        myObj2 = SimpleIRFieldModel(name='Joe', favColour='blue')

        assert myObj2.hasUnsavedChanges() is True , 'Expected unsaved object to have unsaved changes'

        ids2 = myObj2.save()

        assert myObj2.hasUnsavedChanges() is False , 'Expected saved object to not have unsaved changes'

        assert ids2, 'Expected to get ids returned from save, but did not.'
        assert ids2[0] == myObj2._id , 'Expected id to be set on saved object, but was not.'

        fetchObj = SimpleIRFieldModel.objects.get(ids[0])
        assert fetchObj, 'Expected to get an object returned for .get on same id as saved.'
        assert fetchObj._id == ids[0], 'ID on fetched object not same as we requested.'

        assert fetchObj.name == 'Tim', 'Field "name" does not have correct value. Expected "%s", got "%s"' %('Tim', str(fetchObj.name))
        assert fetchObj.favColour == 'purple', 'Field "favColour" does not have correct value'

        fetchObjs2 = SimpleIRFieldModel.objects.filter(favColour='blue').all()

        assert len(fetchObjs2) == 1, 'Expected to get one object back for favColour="blue", got %d' %(len(fetchObjs2),)
        assert (fetchObjs2[0].name == 'Joe' and fetchObjs2[0].favColour == 'blue'), 'Got wrong values back on filter'

        assert fetchObj.delete() == 1, 'Expected delete on fetched object to return 1'

        fetchObj = SimpleIRFieldModel.objects.get(ids[0])
        assert fetchObj is None, 'Expected object to not be present after deleting, but it was.'

    def test_emptyStrNotNull(self):
        '''
            Test that empty str values are not null. Other methods will test that irNull is used when applicable.
        '''
        SimpleIRFieldModel = self.model

        myObj = SimpleIRFieldModel(name='Tim')

        assert myObj.strField != irNull, 'Expected empty classic string field value to not be assigned irNull'
        assert myObj.favColour is irNull, 'Expected empty IRField value to be irNull'

        ids = myObj.save()
        assert ids, 'Expected to get ids returned from save, but did not.'
        assert ids[0] == myObj._id , 'Expected id to be set on saved object, but was not.'

        fetchObj = SimpleIRFieldModel.objects.get(ids[0])
        assert fetchObj, 'Expected to get an object returned for .get on same id as saved.'
        assert fetchObj._id == ids[0], 'ID on fetched object not same as we requested.'

        assert fetchObj.strField != irNull, 'Expected empty classic string field value on fetch to not be assigned irNull'
        assert fetchObj.favColour == irNull, 'Expected IRField not being set to still be irNull'


    def test_noneFieldValue(self):
        '''
            test_noneFieldValue - Use "None" as a type. Expect the field to not be changed.

            This test may be slightly different on python2 vs python3 due to differences in bytes/str type, but should pass on both.
        '''

        SimpleIRFieldModel = self.model

        myObj = SimpleIRFieldModel(name='Tim', nonefield='purple')
        ids = myObj.save()

        assert (type(myObj.nonefield) == str and myObj.nonefield == 'purple'), 'Expected no change for field value on object init, but was changed to %s%s' %(str(type(myObj.nonefield)), repr(myObj.nonefield))

        assert ids, 'Expected to get ids returned from save, but did not.'
        assert ids[0] == myObj._id , 'Expected id to be set on saved object, but was not.'

        myObj2 = SimpleIRFieldModel(name='Joe', nonefield=b'blue')
        ids2 = myObj2.save()

        assert (type(myObj2.nonefield) == bytes and myObj2.nonefield == b'blue'), 'Expected no change for field value on object init, but was changed to %s%s' %(str(type(myObj2.nonefield)), repr(myObj2.nonefield))

        assert ids2, 'Expected to get ids returned from save, but did not.'
        assert ids2[0] == myObj2._id , 'Expected id to be set on saved object, but was not.'

        fetchObj = SimpleIRFieldModel.objects.get(ids[0])

        assert (type(fetchObj.nonefield) == bytes and fetchObj.nonefield == b'purple'), 'Expected field to be returned as bytes (not converted) for nonefield, but was changed to %s%s' %(str(type(fetchObj.nonefield)), repr(fetchObj.nonefield))

        assert fetchObj, 'Expected to get an object returned for .get on same id as saved.'
        assert fetchObj._id == ids[0], 'ID on fetched object not same as we requested.'

        assert fetchObj.name == 'Tim', 'Field "name" does not have correct value. Expected "%s", got "%s"' %('Tim', str(fetchObj.name))
        assert fetchObj.nonefield == b'purple', 'Field "favColour" does not have correct value'


    def test_intFieldValue(self):
        '''
            test_intFieldValue - Test an IRField with "int" as its valueType

        '''
        SimpleIRFieldModel = self.model

        myObj = SimpleIRFieldModel(name='Tim', number=41)
        ids = myObj.save()

        assert (type(myObj.number) == int and myObj.number == 41), 'Expected no change for field value on object init, but was changed to %s%s' %(str(type(myObj.number)), repr(myObj.number))

        assert ids, 'Expected to get ids returned from save, but did not.'
        assert ids[0] == myObj._id , 'Expected id to be set on saved object, but was not.'

        myObj2 = SimpleIRFieldModel(name='Joe', number=44)
        ids2 = myObj2.save()

        assert ids2, 'Expected to get ids returned from save, but did not.'
        assert ids2[0] == myObj2._id , 'Expected id to be set on saved object, but was not.'

        myObj3 = SimpleIRFieldModel(name='Jim', number=44)
        ids3 = myObj3.save()

        assert ids3, 'Expected to get ids returned from save, but did not.'
        assert ids3[0] == myObj3._id , 'Expected id to be set on saved object, but was not.'

        fetchObj = SimpleIRFieldModel.objects.get(ids[0])

        assert type(fetchObj.number) == int, 'Expected field to be returned as bytes (not converted) for number, but was changed to %s%s' %(str(type(fetchObj.number)), repr(fetchObj.number))

        assert fetchObj, 'Expected to get an object returned for .get on same id as saved.'
        assert fetchObj._id == ids[0], 'ID on fetched object not same as we requested.'

        assert fetchObj.name == 'Tim', 'Field "name" does not have correct value. Expected "%s", got "%s"' %('Tim', str(fetchObj.name))
        assert fetchObj.number is 41, 'Field "number" has incorrect value. Expected 41, got: %s' %(repr(fetchObj.number),)

        multipleObjs = SimpleIRFieldModel.objects.filter(number=44).all()

        assert len(multipleObjs) == 2, 'Expected to get two objects for number=44. Got: %d' %(len(multipleObjs),)

        assert ((multipleObjs[0].name == 'Joe' and multipleObjs[1].name == 'Jim') or (multipleObjs[0].name == 'Jim' and multipleObjs[1].name == 'Joe')), 'Expected to get "Joe" and "Jim" objects, but got: %s' %(str([x.name for x in multipleObjs]),)

        SimpleIRFieldModel.objects.filter(number=44).delete()
   
        multipleObjs = SimpleIRFieldModel.objects.filter(number=44).all()

        assert len(multipleObjs) == 0, 'Expected after deleting all with number=44 to get no objects. Got: %d' %(len(multipleObjs),)


        myObj4 = SimpleIRFieldModel(name='Billy')

        assert myObj4.number == irNull, 'Expected unset integer to equal irNull'
        assert myObj4.number != 0, 'Expected unset integer to not equal 0.'
        
        ids4 = myObj4.save()
        assert ids4, 'Expected to get ids returned from save with null value, but did not.'
        assert ids4[0] == myObj4._id , 'Expected id to be set on saved object with null value, but was not.'

        fetchObj4 = SimpleIRFieldModel.objects.get(ids4[0])

        assert fetchObj4._id == myObj4._id , 'Expected fetched object to have same ID as requested.'

        assert fetchObj4.number == irNull, 'Expected unset integer on fetched object to be irNull'
        assert fetchObj4.number != 0, 'Expected unset integer on fetched object to not equal 0'

        fetchObj4.number = 14

        ids4_2 = fetchObj4.save()

        assert ids4_2[0] == ids4[0] , 'Expected update save to not create a new object.'

        fetchObj4_2 = SimpleIRFieldModel.objects.get(ids4[0])
        assert fetchObj4_2.number != irNull , 'Expected once set integer to no longer equal irNull'
        assert fetchObj4_2.number == 14, 'Expected value not saved'
        
    def test_intFieldNulls(self):
        SimpleIRFieldModel = self.model

        myObj = SimpleIRFieldModel(name='Nully')
        ids = myObj.save()

        assert (myObj.number == irNull), 'Expected int field never being set to be irNull'

        assert ids, 'Expected to get ids returned from save, but did not.'
        assert ids[0] == myObj._id , 'Expected id to be set on saved object, but was not.'

        fetchObj = SimpleIRFieldModel(name='Nully')
        assert fetchObj.number == irNull, 'Expected fetched object never have int field set to be irNull'

        myObj.number = 15
        myObj.save()

        assert myObj.number != irNull, 'Expected number not to be null after being set'

        assert myObj.asDict()['number'] != irNull, 'Expected number to not be null after being set'

        fetchObj = SimpleIRFieldModel.objects.filter(name='Nully').all()[0]
        
        assert fetchObj.number == 15, 'Expected number to be set'

        fetchObj.number = irNull
        fetchObj.save()

        fetchObj2 = SimpleIRFieldModel(name='Nully')

        assert fetchObj2.number == irNull, 'Expected after clearing number field it became null'

    def test_datetimeFieldValue(self):
        '''
            test_datetimeFieldValue - Test using an IRDatetimeValue with an IRField.
        '''
        SimpleIRFieldModel = self.model

        myDate = datetime.datetime(1986, 5, 14, 12, 35, 16)

        myObj = SimpleIRFieldModel(name='Tim', timestamp=myDate)

        assert issubclass(myObj.timestamp.__class__, datetime.datetime), 'Expected timestamp to be retained as a datetime.datetime object on init, but was %s%s' %(str(type(myObj.timestamp)), repr(myObj.timestamp))

        ids = myObj.save()

        assert ids, 'Expected to get ids returned from save, but did not.'
        assert ids[0] == myObj._id , 'Expected id to be set on saved object, but was not.'

        myObj2 = SimpleIRFieldModel(name='Joe', timestamp=datetime.datetime(1988, 2, 13, 14, 15, 16))
        ids2 = myObj2.save()

        assert ids2, 'Expected to get ids returned from save, but did not.'
        assert ids2[0] == myObj2._id , 'Expected id to be set on saved object, but was not.'

        fetchObj = SimpleIRFieldModel.objects.get(ids[0])
        assert fetchObj, 'Expected to get an object returned for .get on same id as saved.'
        assert fetchObj._id == ids[0], 'ID on fetched object not same as we requested.'


        assert fetchObj.name == 'Tim', 'Field "name" does not have correct value. Expected "%s", got "%s"' %('Tim', str(fetchObj.name))

        assert issubclass(fetchObj.timestamp.__class__, datetime.datetime), 'Expected timestamp to be a datetime.datetime object after fetch, but was %s%s' %(str(type(fetchObj.timestamp)), repr(fetchObj.timestamp))
        assert fetchObj.timestamp == myDate, 'Expected timestamp retrieved to match original datetime object, but it did not. %s != %s' %(repr(fetchObj.timestamp), repr(myDate))


        fetchedObjs = SimpleIRFieldModel.objects.filter(timestamp=myDate).all()

        assert len(fetchedObjs) == 1, 'Expected to fetch one object for timestamp, got %d' %(len(fetchedObjs),)

        obj = fetchedObjs[0]
        assert obj.name == 'Tim', 'Got wrong fetched object in return.'
        assert obj._id == ids[0] , 'ID is different on fetched object. Expected %d got %s' %(ids[0], str(obj._id))

        assert issubclass(obj.timestamp.__class__, datetime.datetime), 'Expected timestamp to be a datetime.datetime object after fetch, but was %s%s' %(str(type(obj.timestamp)), repr(obj.timestamp))
        assert obj.timestamp == myDate, 'Expected timestamp retrieved to match original datetime object, but it did not. %s != %s' %(repr(obj.timestamp), repr(myDate))

        newDate = datetime.datetime(1987, 3, 13, 1, 1, 1)

        obj.timestamp = newDate
        obj.save()

        fetchedObjs = SimpleIRFieldModel.objects.filter(timestamp=myDate).all()

        assert len(fetchedObjs) == 0, 'Expected to fetch no objects filtering on old date, after date was updated. Got %d: %s' %(len(fetchedObjs), repr([x.asDict() for x in fetchedObjs]))

        fetchedObjs = SimpleIRFieldModel.objects.filter(timestamp=newDate).all()

        assert len(fetchedObjs) == 1, 'Expected to fetch 1 object with new date after updating. Got %s: %s' %(len(fetchedObjs), repr([x.asDict() for x in fetchedObjs]))
        assert fetchedObjs[0].name == 'Tim' and fetchedObjs[0].timestamp == newDate , 'Got wrong values from fetched object after update.'

        noTimestampObj = SimpleIRFieldModel(name='Billy')

        assert noTimestampObj.timestamp == irNull, 'Expected object created with empty timestamp field to have timestamp be assigned irNull'

        ids = noTimestampObj.save()

        assert ids and ids[0] == noTimestampObj._id , 'Did not set ids properly on saved object with a null field'

        fetchedObjs = SimpleIRFieldModel.objects.filter(name='Billy').all()

        assert len(fetchedObjs) == 1, 'Expected to only get one object with name="Billy", but got %d' %(len(fetchedObjs),)

        fetchedObj = fetchedObjs[0]

        assert fetchedObj.timestamp == irNull, 'Expected fetched object with empty timestamp field to have timestamp be assigned irNull'

        fetchedObjs = SimpleIRFieldModel.objects.filter(timestamp=irNull).all()

        assert len(fetchedObjs) == 1 and fetchedObjs[0]._id == ids[0], 'Expected to be able to fetch using irNull as a filter value'


    def test_jsonFieldValue(self):
        SimpleIRFieldModel = self.model

        myData = { "one" : "two",
            "sub" : {
                "level2" : {
                    "val" : 5,
                    "cheese" : "cheddar",
                }
            }
        }

        myObj = SimpleIRFieldModel(name='Tim', jsonData=myData)

        assert issubclass(myObj.jsonData.__class__, dict), 'Expected jsonData to be retained as a dict object on init, but was %s%s' %(str(type(myObj.jsonData)), repr(myObj.jsonData))

        ids = myObj.save()

        assert ids, 'Expected to get ids returned from save, but did not.'
        assert ids[0] == myObj._id , 'Expected id to be set on saved object, but was not.'

        myObj2 = SimpleIRFieldModel(name='Joe', jsonData={'basic' : 'yes'})
        ids2 = myObj2.save()

        assert ids2, 'Expected to get ids returned from save, but did not.'
        assert ids2[0] == myObj2._id , 'Expected id to be set on saved object, but was not.'

        fetchObj = SimpleIRFieldModel.objects.get(ids[0])
        assert fetchObj, 'Expected to get an object returned for .get on same id as saved.'
        assert fetchObj._id == ids[0], 'ID on fetched object not same as we requested.'

        assert fetchObj.name == 'Tim', 'Field "name" does not have correct value. Expected "%s", got "%s"' %('Tim', str(fetchObj.name))

        assert issubclass(fetchObj.jsonData.__class__, dict), 'Expected jsonData to be a dict object after fetch, but was %s%s' %(str(type(fetchObj.jsonData)), repr(fetchObj.jsonData))
        
        fetchedData = fetchObj.jsonData

        assert fetchedData.get('one', '') == 'two', 'jsonData has corrupted values. "one" field should have equaled "two", but equaled: %s' %(fetchedData.get('one', 'None'),)

        try:
            assert fetchedData['sub']['level2']['val'] == 5, 'Got wrong value, expected "val" to retain integer 5, but got: %s%s' %(str(type(fetchedData['sub']['level2']['val'])), repr(fetchedData['sub']['level2']['val']))
        except KeyError as e:
            raise AssertionError('Got key error accessing sub->level2->val: %s' %(str(e),))

        emptyJsonObj = SimpleIRFieldModel(name='Billy')

        assert emptyJsonObj.jsonData == irNull, 'Expected object with no value assigned for jsonData to be irNull'
        
        emptyJsonObj.save()

        emptyFetchObj = SimpleIRFieldModel.objects.get(emptyJsonObj._id)

        assert emptyFetchObj.name == 'Billy' , 'Fetched wrong object'
        assert emptyFetchObj.jsonData == irNull, 'Expected fetched json object with no vlaue assigned to be irNull'

        blankJsonObj = SimpleIRFieldModel(name='Billy', jsonData={})
       
        assert blankJsonObj.jsonData != irNull, 'Expected empty dict to not be converted to irNull'

        blankJsonObj.jsonData['cheese'] = 'swiss'
        blankJsonObj.save()

        fetchObj = SimpleIRFieldModel.objects.get(blankJsonObj._id)

        assert fetchObj.jsonData.get('cheese', None) == 'swiss' , 'Expected updated field to retain new value'

    def test_DatetimeMicrosecond(self):
        datetimeStr = '2015-05-12 12:00:00'
        datetimeObj = datetime.datetime(year=2015, month=5, day=12, hour=12, minute=0, second=0)

        val = IRDatetimeValue(datetimeStr)
        assert val == datetimeObj, 'Expected datetime object created from string to match equivalent'

        datetimeStr += '.203511'
        try:
            val = IRDatetimeValue(datetimeStr)
        except Exception as e:
            raise AssertionError('Expected to be able to create object including microseconds. Got %s %s' %(str(e.__class__.__name__), str(e)))

        val = IRDatetimeValue(datetimeStr)
        assert val == datetimeObj, 'Expected datetime object created from string including microseconds to match equivalent without microseconds'

    def test_updatedFieldsAfterSave(self):
    
        SimpleIRFieldModel = self.model

        obj = SimpleIRFieldModel()

        updatedFields = obj.getUpdatedFields()

        assert updatedFields == {}, 'Expected empty updatedFields on newly created object'

        obj.favColour = 'purple'

        updatedFields = obj.getUpdatedFields()
        assert 'favColour' in updatedFields , 'Expected favColour to show up in updatedFields after updating value'

        assert not updatedFields['favColour'][0]  , 'Expected old value in updatedFields["favColour"] to be False'
        assert updatedFields['favColour'][1] == 'purple' , 'Expected new value to be in updatedFields["favColour"][1]'

        obj.name = 'hello'

        obj.save()

        updatedFields = obj.getUpdatedFields()
        assert updatedFields == {}, 'Expected empty updatedFields after saving'

        fetchedObj = SimpleIRFieldModel.objects.filter(name='hello').first()

        assert fetchedObj , 'Expected to be able to fetch'

        obj = fetchedObj

        updatedFields = obj.getUpdatedFields()
        assert updatedFields == {}, 'Expected empty updatedFields after fetching'

        obj.favColour = 'purple'
        updatedFields = obj.getUpdatedFields()
        assert updatedFields == {}, 'Expected empty updatedFields after changing to same value'
        

        obj.favColour = 'red'
        updatedFields = obj.getUpdatedFields()

        assert updatedFields['favColour'][0] == 'purple' , 'Expected old value to be in updatedFields["favColour"][0]'
        assert updatedFields['favColour'][1] == 'red' , 'Expected new value to be in updatedFields["favColour"][1]'

        obj.save()
        updatedFields = obj.getUpdatedFields()
        assert updatedFields == {}, 'Expected empty updatedFields after updating'



if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
