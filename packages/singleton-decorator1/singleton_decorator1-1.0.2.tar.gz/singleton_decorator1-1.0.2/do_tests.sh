#!/usr/bin/bash
#set -x
eval "$(pyenv init - bash)"
pyenv shell dev-3.13

log=${PWD}/do_tests.log

rm -f ${log}
touch ${log}

# empty our "repository", but leave simpleindex.toml
rm -rf tests/dist/index* tests/dist/singleton*

# build working version of project-version-finder
hatchling build 2>&1 | tee -a ${log}
cp dist/* tests/dist

# build index for all packages
simple503 -e -s tests/dist
# make packages installable via pip from local "repository"
killall simpleindex
simpleindex tests/dist/simpleindex.toml 2>&1 | tee -a ${log} >simpleindex.log &

pyenv shell --unset

pass=1
for py_ver in 3.7.17 3.8.20 3.9.23 3.10.18 3.11.13 3.12.11 3.13.6; do
	echo ""
	echo "Python Version ${py_ver}"
	echo "####################"
	echo ""
	pyenv shell ${py_ver}

	
	rm -rf tests/.venv
	python -m venv tests/.venv
	source tests/.venv/bin/activate

	pip --disable-pip-version-check --require-virtualenv --no-input --no-cache-dir \
		install --index-url http://localhost:8000 --upgrade \
		singleton-decorator1 1>> ${log}
	
	pip --disable-pip-version-check --require-virtualenv --no-input --no-cache-dir \
		install --index-url http://localhost:8000 --upgrade \
		mypy pytest  1>> ${log}

	mypy 2>&1 | tee -a ${log}
	if [[ "$?" != "0" ]]; then
		pass=0
	fi
	pytest 2>&1 | tee -a ${log}
	if [[ "$?" != "0" ]]; then
		pass=0
	fi
	deactivate
	pyenv shell --unset
done

killall simpleindex

if [[ "$pass" == "1" ]]; then
	echo "All Tests Pass"
else
	echo "Some Tests Failed"
fi
