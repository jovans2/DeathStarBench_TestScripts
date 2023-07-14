sudo apt update
sudo apt upgrade -y
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release htop -y
sudo apt-get update

sudo apt-get install python3-pip -y
pip3 install numpy
pip3 install pandas
pip3 install scikit-learn

git clone https://github.com/jovans2/DeathStarBench_TestScripts

cd DeathStarBench_TestScripts
python3 ml_train_server.py