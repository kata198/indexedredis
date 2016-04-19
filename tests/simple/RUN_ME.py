#!/usr/bin/env python

'''
    RUN_ME.py - Run to create a symlink to run these tests, since MANIFEST.in doesn't support symlinks.
'''

import os

if __name__ == '__main__':

    # First, change to directory which contains this script
    dirName = os.path.dirname(__file__)
    if dirName and os.getcwd() != dirName:
        os.chdir(dirName)

    # Give us a little blank line at the top
    print ("")
    # Symlinks because MANIFEST.in does not support them
    if not os.path.exists('./IndexedRedis'):
        os.symlink('../../IndexedRedis', 'IndexedRedis')
        print ( "Created symlink: IndexedRedis -> ../../IndexedRedis\n")

    print ("You may now run the tests in this directory.")
