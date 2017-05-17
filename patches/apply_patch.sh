#!/bin/bash

if [ $# -lt 0 ];
then
    echo "Usage: apply_patch.sh [patch name]" >&2
    exit 1
fi

pushd ${BASH_SOURCE[0]} >/dev/null 2>&1

cd ..

RET=0

for patchName in "$@";
do
    basePatchName="$(basename "${patchName}")"
    if [ ! -f "patches/${basePatchName}" ];
    then
        echo "Can't find patch: ${patchName}" >&2
        RET=1
        continue
    fi
    cat "patches/`basename ${patchName}`"  | patch -p1
done

exit ${RET}
