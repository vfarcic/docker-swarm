Scaling Containers with Docker Swarm, Docker Compose and Consul (Part 3/3)
==========================================================================

TODO
====

* Color is retrieved from Consul
* Container is stopped
* Container removed
* Stop old container

* Manual commands
* Explain books-fe.yml
* Consul health and watchers
* Jenkins failure recuperation; redeployment and notifications
* Ansible explained
* Explain "alias" Ansible variable
* Consul UI
* Scale single container


We'll start with the deployment of the books-service. Ansible playbook books-service.yml is following.

```yml
- hosts: service
  remote_user: vagrant
  sudo: yes
  vars:
    - container_image: books-service
    - container_name: books-service
    - http_address: /api/v1/books
    - has_db: true
  roles:
    - docker
    - consul
    - swarm
    - nginx
    - service
```

First four roles are taking care of necessary prerequisites. We need to have **Docker**, **Consul**, **Docker Swarm** and **nginx** installed. Docker manages our containers, Consul is taking care key/value storage, service discovery and health, Docker Swarm will distribute our service to one of the servers and nginx is in charge or proxy.
