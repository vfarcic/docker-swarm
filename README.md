Work in progress
================

```bash
vagrant up
vagrant provision

vagrant ssh swarm-master
CLUSTER_ID=$(sudo docker run --rm swarm create)
echo $CLUSTER_ID
#cd /tmp
#wget https://github.com/coreos/etcd/releases/download/v2.0.10/etcd-v2.0.10-linux-amd64.tar.gz
#tar -xzvf etcd-v2.0.10-linux-amd64.tar.gz
#sudo cp etcd-v2.0.10-linux-amd64/etcd* /usr/local/bin/.
#etcd &

vagrant ssh swarm-node-01
# Make sure to put the correct cluster ID
CLUSTER_ID=d7b292df718d4136333dbf7e589354e4
# TODO: Put -H tcp://0.0.0.0:2375 to /etc/default/docker
# TODO: Put -H unix:///var/run/docker.sock to /etc/default/docker
sudo service docker restart
sudo docker run -d --name swarm-node swarm join --addr=10.100.199.201:2375 token://$CLUSTER_ID
exit

vagrant ssh swarm-node-02
# Make sure to put the correct cluster ID
CLUSTER_ID=d7b292df718d4136333dbf7e589354e4
# TODO: Put "-H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock" to /etc/default/docker
sudo service docker restart
sudo docker run -d --name swarm-node swarm join --addr=10.100.199.202:2375 token://$CLUSTER_ID
exit

vagrant ssh swarm-node-03
# Make sure to put the correct cluster ID
CLUSTER_ID=d7b292df718d4136333dbf7e589354e4
# TODO: Put "-H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock" to /etc/default/docker
sudo service docker restart
sudo docker run -d --name swarm-node swarm join --addr=10.100.199.203:2375 token://$CLUSTER_ID
exit

vagrant ssh swarm-master
sudo docker run -d -p 2375:2375 --name swarm-master swarm manage token://$CLUSTER_ID
docker -H tcp://0.0.0.0:2375 info
sudo docker run --rm swarm list token://$CLUSTER_ID

# Run books-service container
docker -H tcp://0.0.0.0:2375 run -d \
  --name books-service \
  -p 9001:8080 \
  -v /data/books-service/db:/data/db \
  vfarcic/books-service
docker -H tcp://0.0.0.0:2375 ps -a
# TODO: Change to etcd
BOOKS_SERVICE_IP=10.100.199.202
curl -H 'Content-Type: application/json' -X PUT -d \
  '{"_id": 1, "title": "My First Book", "author": "John Doe", "description": "Not a very good book"}' \
  http://$BOOKS_SERVICE_IP:9001/api/v1/books | python -mjson.tool
curl -H 'Content-Type: application/json' -X PUT -d \
  '{"_id": 2, "title": "My Second Book", "author": "John Doe", "description": "Not a bad as the first book"}' \
  http://$BOOKS_SERVICE_IP:9001/api/v1/books | python -mjson.tool
curl -H 'Content-Type: application/json' -X PUT -d \
  '{"_id": 3, "title": "My Third Book", "author": "John Doe", "description": "Failed writers club"}' \
  http://$BOOKS_SERVICE_IP:9001/api/v1/books | python -mjson.tool
curl http://$BOOKS_SERVICE_IP:9001/api/v1/books | python -mjson.tool

# Run books-fe container
docker -H tcp://0.0.0.0:2375 run -d \
  --name books-fe \
  -p 9011:8080 \
  vfarcic/books-fe


docker -H tcp://0.0.0.0:2375 ps -a
docker -H tcp://0.0.0.0:2375 logs -f books-fe-mock
```
