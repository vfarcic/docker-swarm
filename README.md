Work in progress
================

```bash
vagrant up
vagrant provision --provision-with hosts

## swarm-node-01 ##
vagrant ssh swarm-node-01
ssh-keygen
exit

## swarm-node-02 ##
vagrant ssh swarm-node-02
ssh-keygen
exit

## swarm-node-03 ##
vagrant ssh swarm-node-03
ssh-keygen
exit

## swarm-master ##
vagrant ssh swarm-master
ssh-keygen
ssh-copy-id vagrant@10.100.199.200
ssh-copy-id vagrant@10.100.199.201
ssh-copy-id vagrant@10.100.199.202
ssh-copy-id vagrant@10.100.199.203

# Setup Consul
ansible-playbook /vagrant/ansible/consul.yml -i /vagrant/ansible/hosts/prod

# Check Consul
consul members
curl localhost:8500/v1/catalog/nodes
dig @127.0.0.1 -p 8600 swarm-master.node.consul
dig @127.0.0.1 -p 8600 swarm-node-01.node.consul
dig @127.0.0.1 -p 8600 swarm-node-02.node.consul
dig @127.0.0.1 -p 8600 swarm-node-03.node.consul
# TODO: Move to books-service
dig @127.0.0.1 -p 8600 books-service.service.consul SRV
# TODO: Move to books-service
dig @127.0.0.1 -p 8600 service.books-service.service.consul SRV
# TODO: Move to books-service
curl http://localhost:8500/v1/catalog/service/books-service
# TODO: Move to books-service
sudo killall -HUP consul

# Setup Docker Swarm
ansible-playbook /vagrant/ansible/swarm.yml -i /vagrant/ansible/hosts/prod

# Check Docker Swarm
docker -H tcp://0.0.0.0:2375 info

# Run Books Service
ansible-playbook /vagrant/ansible/books-service.yml -i /vagrant/ansible/hosts/prod

# Check Books Service
docker -H tcp://0.0.0.0:2375 ps -a
curl -H 'Content-Type: application/json' -X PUT -d \
  '{"_id": 1, "title": "My First Book", "author": "John Doe", "description": "Not a very good book"}' \
  http://10.100.199.201:9001/api/v1/books | python -mjson.tool
curl -H 'Content-Type: application/json' -X PUT -d \
  '{"_id": 2, "title": "My Second Book", "author": "John Doe", "description": "Not a bad as the first book"}' \
  http://10.100.199.201:9001/api/v1/books | python -mjson.tool
curl -H 'Content-Type: application/json' -X PUT -d \
  '{"_id": 3, "title": "My Third Book", "author": "John Doe", "description": "Failed writers club"}' \
  http://10.100.199.201:9001/api/v1/books | python -mjson.tool
curl http://10.100.199.201:9001/api/v1/books | python -mjson.tool
curl http://10.100.199.200/api/v1/books | python -mjson.tool

# Run Books Front-End
ansible-playbook /vagrant/ansible/books-fe.yml -i /vagrant/ansible/hosts/prod
docker -H tcp://0.0.0.0:2375 ps -a
curl http://10.100.199.202:9000
curl http://10.100.199.200

# Consul checks
curl http://localhost:8500/v1/health/state/critical
curl http://localhost:8500/v1/health/state/warning
docker -H tcp://0.0.0.0:2375 stop books-service
curl http://localhost:8500/v1/health/state/critical
# Open http://10.100.199.200:8500/ui/ in browser
# Open http://10.100.199.200:8080 in browser
docker -H tcp://0.0.0.0:2375 start books-service
curl http://localhost:8500/v1/health/state/critical
# Open http://10.100.199.200:8500/ui/ in browser
# Open http://10.100.199.200:8080 in browser
docker -H tcp://0.0.0.0:2375 stop books-fe
curl http://localhost:8500/v1/health/state/critical
# Open http://10.100.199.200:8500/ui/ in browser
# Open http://10.100.199.200:8080 in browser
docker -H tcp://0.0.0.0:2375 start books-fe
curl http://localhost:8500/v1/health/state/critical
# Open http://10.100.199.200:8500/ui/ in browser
# Open http://10.100.199.200:8080 in browser


```

TODO
====

* Add DB as a separate container
* Consul container
* Add loadavg check `cat /proc/loadavg | awk '{printf "CPU Load Average: 1m: %.2f, 5m: %.2f, 15m: %.2f\n", $1,$2,$3}'`
* Notifications
* Use mounted volumes