sudo apt update
sudo apt upgrade -y
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release htop -y
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
sudo groupadd docker
sudo usermod -aG docker $USER

sudo chmod 666 /var/run/docker.sock

sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

sudo apt-get install python3-pip -y
pip3 install docker
pip3 install numpy
pip3 install thrift
pip3 install pandas
pip3 install scikit-learn

git clone https://github.com/jovans2/DeathStarBench_TestScripts
git clone https://github.com/delimitrou/DeathStarBench

cd DeathStarBench_TestScripts
python3 ml_train_server.py