#!/bin/bash
# bash script to run gemouse


tag="stable_2025-08-20a"

# go to repository directory, git reset to tag
cd $HOME/git/Autoresuscitation
git fetch --tags
git checkout stable
git pull
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

# liblgpio-dev is needed for 2025 updates for the pi5 compatible GEMouse
if ! dpkg -s liblgpio-dev &> /dev/null
then
{
  echo "Please install liblgpio-dev and try again. >sudo apt install liblgpio-dev"
}
else
{
  echo "liblgpio-dev found"
}
fi

# uv is the preferred venv and package manager for GEMouse and successor to PCC
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
  # mamba/conda is still needed for py38 compatibility needed for PCC (pygame)
  source activate py38
  python $HOME/git/Autoresuscitation/PCC.py
}
fi
