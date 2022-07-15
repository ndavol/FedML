#CPU installation

pip install torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric -f https://data.pyg.org/whl/torch-1.12.0+cpu.html
DATA_PATH= ../data/clintox
wget --no-check-certificate --no-proxy -P $DATA_PATH https://fedmol.s3-us-west-1.amazonaws.com/datasets/clintox/clintox.zip &&
cd $DATA_PATH &&
unzip clintox.zip && rm clintox.zip


