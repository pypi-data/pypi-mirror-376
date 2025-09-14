#!/usr/bin/env bash

echo "This script needs to be editted"
echo "Right now it is configured for:"
echo "1) bash ; to use a different shell consult"
echo "   https://github.com/pyenv/pyenv.git README.md"
echo "2) creates virtual env 'dev' using latest CPython stable release"
echo "   supported by pyenv; edit pyenv virtualenv command as you require"
echo "3) None of this is required if you don't want to use my method of"
echo "   building the package. Just (a) use pip to install from pypi, or"
echo "   use your own development flow"
echo ""
echo "Now, to run this script, edit it as you require, and remove the 'exit'"

exit 1

THIS_SCRIPT="$0"
if [[ "${THIS_SCRIPT#/}" == "${THIS_SCRIPT}" ]] ; then
	THIS_SCRIPT="${PWD}/${THIS_SCRIPT}"
fi
SCRIPT_DIR="${THIS_SCRIPT%/*}"
PYTHON_CONFIGURE_OPTS='--enable-optimizations --enable-shared'
PYTHON_CFLAGS='-march=native -mtune=native'
p
PYENV=$(which pyenv)
if [[ "${PYENV-}" == "" ]] ; then
	curl https://pyenv.run | bash
	echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
	echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
	echo 'eval "$(pyenv init - bash)"' >> ~/.bashrc
	echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
	pushd $(pyenv root)/plugins
	git clone https://codeberg.org/Pusher2531/pyenv-depends-plugin.git
	git clone https://github.com/zyrikby/pyenv-pip-upgrade.git
	popd
	pyenv rehash
	sudo apt update
	sudo apt install make build-essential libssl-dev zlib1g-dev \
		 libbz2-dev libreadline-dev libsqlite3-dev curl git \
		 libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
		 libffi-dev liblzma-dev
	latest_python=$(pyenv install --complete | grep '^3\.' | grep -v '[a-z]' | tail -n 1 | cut -d . -f 1-2)
	pyenv install ${latest_python}
fi	

source "${SCRIPT_DIR}/pyenv_setup_source"

latest_python=$(pyenv versions --skip-aliases --skip-envs | grep '^3\.' | grep -v '[a-z]' | tail -n 1 | cut -d . -f 1-2)

pyenv virtualenv ${latest_python} dev

pyenv shell dev

pyenv exec pip install --upgrade pip
pyenv exec pip install tomlkit packaging poetry poethepoet[poetry-plugin] poethepoet-tasks black pytest mypy 

#poe _bash_completion | sudo tee /etc/bash_completion.d/poe.bash-completion

echo "To integrate pyenv into your shell, do"
echo "exec \$SHELL"
