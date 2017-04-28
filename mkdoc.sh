#!/bin/bash

ALL_MODS="$(echo IndexedRedis/**.py IndexedRedis/**/*.py | tr ' ' '\n' | sed -e 's|/|.|g' -e 's|.py$||g' -e 's|.__init__$||g' | tr '\n' ' ')"

pydoc -w ${ALL_MODS}
mv *.html doc/
pushd doc >/dev/null 2>&1
rm -f index.html

for fname in `echo *.html`;
do
    python <<EOT

import AdvancedHTMLParser
import sys

if __name__ == '__main__':

    filename = "${fname}"

    parser = AdvancedHTMLParser.AdvancedHTMLParser()
    parser.parseFile(filename)

    em = parser.filter(tagName='a', href='.')

    if len(em) == 0:
        sys.exit(0)

    em = em[0]

    em.href = 'IndexedRedis.html'

    parentNode = em.parentNode

    emIndex = parentNode.children.index(em)

    i = len(parentNode.children) - 1
    
    while i > emIndex:
        parentNode.removeChild( parentNode.children[i] )
        i -= 1


    with open(filename, 'wt') as f:
        f.write(parser.getHTML())


EOT


done

ln -s IndexedRedis.html index.html

popd >/dev/null 2>&1
