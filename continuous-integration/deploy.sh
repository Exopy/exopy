set -e
cd $TRAVIS_BUILD_DIR
PACK="$(conda build conda --output)"
conda convert $PACK -p osx-64 -p win-64 --quiet -o $CONDA_BLD_PATH
conda convert $PACK -p win-32 --quiet -o $CONDA_BLD_PATH
cd $CONDA_BLD_PATH
source deactivate
python $TRAVIS_BUILD_DIR/continuous-integration/anaconda-push.py
