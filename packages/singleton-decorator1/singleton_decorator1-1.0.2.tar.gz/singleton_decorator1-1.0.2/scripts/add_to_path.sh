#!/usr/bin/bash

# Usage: eval $(add_to_path.sh)

# Adds the directory this file is in to the PATH
# clean_path.py should be in the same directory

me="$0"
if [[ "${me#./}" != "${me}" ]] ; then
	full_me="${PWD}/${me#./}"
elif [[ "${me#/}" != "${me}" ]] ; then
	full_me="${me}"
else
	echo "Where am I?" 1>2
	exit 1
fi

dir="${full_me%/*}"

export PATH="$dir:$PATH"

"${dir}/clean_path.py"
