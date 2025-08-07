#!/bin/bash
# bash script to run gemouse


tag="dev_2025-07-23b"

# go to repository directory, git reset to tag for testing
cd $HOME/git/Autoresuscitation
git fetch
git checkout $tag
git reset --hard $tag


# check for dependency 
# swig - is a recently needed dependency for 2025 updates 
# to autoresuscitation repository


if ! command -v swig &> /dev/null
then
{
  echo "Please install swig and try again. >sudo apt install swig"
  exit 1
}
else
{
  echo "swig installed"
}
fi

if ! dpkg -s liblgpio-dev &> /dev/null
then
{
  echo "Please install liblgpio-dev"
}
else
{
  echo "liblgpio-dev found"
}
fi

if ! command -v uv &> /dev/null
then
{
  echo "Please install uv and try again. >curl -LsSf https://astral.sh/uv/install.sh | sh"
}
else
{
  echo "uv is installed"
  cd $HOME/git/Autoresuscitation
  uv run $HOME/git/Autoresuscitation/GEMouse.py &
  uv run $HOME/git/Autoresuscitation/PCC.py
}
fi