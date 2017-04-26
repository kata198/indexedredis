#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestCopyModel - Copy Model test
#

# vim: set ts=4 sw=4 expandtab

import sys
import subprocess
from IndexedRedis import IndexedRedisModel, IRField, InvalidModelException, validatedModels

# vim: ts=4 sw=4 expandtab

class TestCopyModel(object):


    def test_copyModel(self):
        class CopyModel(IndexedRedisModel):
            FIELDS = [
                IRField('name'),
                IRField('num', valueType=int, defaultValue=3),
            ]

            INDEXED_FIELDS = ['num']

            KEY_NAME = 'IRTestCopyModel__CopyModel'

        Model = CopyModel

        obj = Model()

        assert obj.num == 3 , 'Checking that original defaultValue=3 is applied'

        ModelCopy = CopyModel.copyModel()

        assert id(Model) != id(ModelCopy) , 'Expected copy of model not to have same id'
        assert Model.__name__ != ModelCopy.__name__ , 'Expected copy of model to have different name'

        assert id(Model.INDEXED_FIELDS) != id(ModelCopy.INDEXED_FIELDS) , 'Expected INDEXED_FIELDS to have different id on copied model'

        assert id(Model.FIELDS) != id(ModelCopy.FIELDS) , 'Expected FIELDS to have different id on copied model'

        assert id(Model.FIELDS[0]) != id(ModelCopy.FIELDS[0]) , 'Expected individual entries in FIELDS to have different id in copy'

        assert ModelCopy.INDEXED_FIELDS == ['num'] , 'Expected INDEXED_FIELDS data to be copied'

        assert ModelCopy.KEY_NAME == Model.KEY_NAME , 'Expected KEY_NAME to be the same between original and copy'

        ModelCopy.FIELDS['num'].defaultValue = 17

        obj2 = ModelCopy()

        assert obj2.num == 17 , 'Expected after changing num.defaultValue to 17 on ModelCopy, that instances of ModelCopy get that default'

        obj = Model()

        assert obj.num == 3 , 'Expected after changing num.defaultValue to 17 on ModelCopy, that instances of Model get the original default'

        
        obj.name = 'm1'
        obj2.name = 'm2'

        ids = obj.save()
        assert ids and ids[0] , 'Failed to save on original model'
        ids = obj2.save()
        assert ids and ids[0] , 'Failed to save on copied model'

        objFetched1 = Model.objects.filter(num=17).first()

        assert objFetched1 , 'Expected to be able to fetch object saved on copy with original'

        objFetched2 = ModelCopy.objects.filter(num=3).first()

        assert objFetched2 , 'Expected to be able to fetch object saved on original with copy'


            

            
if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
