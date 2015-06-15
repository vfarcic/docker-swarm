Work in progress
================

Prerequisites
-------------

* VirtualBox
* Vagrant

```bash
vagrant plugin install vagrant-cachier
```

```bash
vagrant up

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
ssh-copy-id vagrant@10.100.199.200 # pass: vagrant
ssh-copy-id vagrant@10.100.199.201 # pass: vagrant
ssh-copy-id vagrant@10.100.199.202 # pass: vagrant
ssh-copy-id vagrant@10.100.199.203 # pass: vagrant

# Setup Jenkins, Consul and Swarm 
ansible-playbook /vagrant/ansible/infra.yml -i /vagrant/ansible/hosts/prod

# Check Consul
consul members
curl localhost:8500/v1/catalog/nodes | jq .

# Check Docker Swarm
export DOCKER_HOST=tcp://0.0.0.0:2375
docker info

# Run Books Service
ansible-playbook /vagrant/ansible/books-service.yml -i /vagrant/ansible/hosts/prod

# Check Books Service
docker ps
curl -H 'Content-Type: application/json' -X PUT -d \
  '{"_id": 1, "title": "My First Book", "author": "John Doe", "description": "Not a very good book"}' \
  http://10.100.199.200/api/v1/books | jq .
curl -H 'Content-Type: application/json' -X PUT -d \
  '{"_id": 2, "title": "My Second Book", "author": "John Doe", "description": "Not a bad as the first book"}' \
  http://10.100.199.200/api/v1/books | jq .
curl -H 'Content-Type: application/json' -X PUT -d \
  '{"_id": 3, "title": "My Third Book", "author": "John Doe", "description": "Failed writers club"}' \
  http://10.100.199.200/api/v1/books | jq .
curl http://10.100.199.200/api/v1/books | jq .
curl http://localhost:8500/v1/catalog/service/books-service-lb | jq .

# Run Books Front-End
ansible-playbook /vagrant/ansible/books-fe.yml -i /vagrant/ansible/hosts/prod
docker -H tcp://0.0.0.0:2375 ps
curl http://10.100.199.200

** TODO: Continue **
# Consul checks
curl http://localhost:8500/v1/health/state/critical
curl http://localhost:8500/v1/health/state/warning
docker -H tcp://0.0.0.0:2375 stop books-service
curl http://localhost:8500/v1/health/state/critical
# Open http://10.100.199.200:8500 in browser
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

# Scale Up
ansible-playbook /vagrant/ansible/books-service.yml \
  -i /vagrant/ansible/hosts/prod \
  --tags "service" \
  --extra-vars "service_instances=3"
curl http://localhost:8500/v1/catalog/service/books-service-blue | jq .
curl http://localhost:8500/v1/catalog/service/books-service-green | jq .
# TODO: Display nginx config
cd /data/compose/config/books-service
curl http://10.100.199.200/api/v1/books | jq .

# Scale Down
ansible-playbook /vagrant/ansible/books-service.yml \
  -i /vagrant/ansible/hosts/prod \
  --tags "service" \
  --extra-vars "service_instances=1"
# Open http://10.100.199.200:8500/ui/ in browser
curl http://10.100.199.200/api/v1/books | jq .


# Run Books Service for a new client
ansible-playbook /vagrant/ansible/books-service.yml -i /vagrant/ansible/hosts/prod --extra-vars "nginx_host=acme.com nginx_conf_name=acme alias=acme host=http://acme.com"
echo "10.100.199.200 acme.com" | sudo tee -a /etc/hosts
curl -H 'Content-Type: application/json' -X PUT -d \
  '{"_id": 1, "title": "ACME changed my life", "author": "ACME", "description": "To ACME or not to ACME"}' \
  http://acme.com/api/v1/books | jq .
curl http://acme.com/api/v1/books | jq .
curl http://10.100.199.200/api/v1/books | jq .
```

TODO
====

* Consul to Jenkins
* Add loadavg check `cat /proc/loadavg | awk '{printf "CPU Load Average: 1m: %.2f, 5m: %.2f, 15m: %.2f\n", $1,$2,$3}'`
* Notifications
* Use mounted volumes
* Fix PUT/POST in books-fe
* Write Consul blue/green Ansible module