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

git clone https://github.com/jovans2/DeathStarBench_TestScripts
git clone https://github.com/delimitrou/DeathStarBench

cp DeathStarBench_TestScripts/docker-compose.yml DeathStarBench/socialNetwork/
cp DeathStarBench_TestScripts/service-config.json DeathStarBench/socialNetwork/config/
cp DeathStarBench_TestScripts/FrontendSimple.py DeathStarBench/socialNetwork/test

docker pull jovanvr97/deathstarbench

cd DeathStarBench/socialNetwork

docker-compose up -d

cd test

python3 FrontendSimple.py
