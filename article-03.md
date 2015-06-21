Scaling Containers with Docker Swarm, Docker Compose and Consul (Part 3/3)
==========================================================================

In the previous article (TODO: Link) we manually deployed the first version of our service together with a separate instance of the Mongo DB container. Both are running on different servers. Docker Swarm decided where to run our containers and Consul stored information about service IPs and ports as well as other useful information. That data was used to link one service with another as well as to provide information nginx needed to create proxy.

We'll continue where we left and deploy a second version of our service. Since we're practicing blue/green deployment, the first version was called **blue** and the next one will be **green**. This time there will be some additional complications. Deploying the second time is a bit more complicated since there are additional things to consider, especiall since our goal is to have no downtime.

Setup
=====

For those of you who stopped VMs we created in the previous article (`bagrant halt`) or turned of your laptops, here's how to quickly get to the same state where we were before. The rest of you can skip this chapter.

```bash
vagrant up
vagrant ssh swarm-master
ansible-playbook /vagrant/ansible/infra.yml -i /vagrant/ansible/hosts/prod
export DOCKER_HOST=tcp://0.0.0.0:2375
docker start booksservice_db_1
docker start booksservice_blue_1
sudo consul-template -consul localhost:8500 -template "/data/nginx/templates/books-service-blue-upstream.conf.ctmpl:/data/nginx/upstreams/books-service.conf:docker kill -s HUP nginx" -once
```

We can verify whether everything seems to be in order by running following.

```bash
docker ps
curl http://10.100.199.200/api/v1/books | jq .
```

The first command should list, among other things, booksservice_blue_1 and booksservice_db_1 containers. The second one should retrieve JSON response with three books we inserted before.
 
With this out of the way, we can continue where we left.

Run the Second Release Of The Service Container
===============================================

While the first release was **blue**, this one will be called **green**. We'll run it in parallel with the previous one in order to avoid any downtime. Once everything is up and running and we're sure that the new release (green) is working as expected, the old one (blue) will be stopped.

```bash
cd /data/compose/config/books-service
docker-compose pull green
docker-compose rm -f green
docker-compose up -d green
docker ps | grep booksservice
```

At this moment we have two versions of our service up and running (old and new; blue and green) . That can be seen by the output of the last command (`docker ps`). It should display both services running on different servers (or the same if that turned up to be the place with the least number of containers).

This is the moment when we should run our automated tests. We do not have them prepared for this article so we'll manually `curl` command to check whether everything seems to be OK.

```bash
curl http://localhost:8500/v1/catalog/service/books-service-green | jq .
curl http://10.100.199.201:32768/api/v1/books | jq .
```

The first command queries Consul and returns data related to the books-service-green service. Please make sure to change the IP and the port in the second command (`curl`) to the one you got from Consul.
 
Keep in mind that we tested the service by sending request directly to its IP and port and not to the publicly available address served with **nginx**. At this moment both services are running with the old one (blue) being available for the public on [http://10.100.199.200](http://10.100.199.200) and the new one (green) at the moment accessible only to us. Once it is tested, we'll change nginx and tell it to redirect all request to the new one thus archiving zero-downtime. Now that everything seems to be working as expected, it is time to make the new release (green) available to the public.

```bash
curl -X PUT -d 'green' http://localhost:8500/v1/kv/services/books-service/color
sudo consul-template -consul localhost:8500 -template "/data/nginx/templates/books-service-green-upstream.conf.ctmpl:/data/nginx/upstreams/books-service.conf:docker kill -s HUP nginx" -once
docker stop booksservice_blue_1
curl http://10.100.199.200/api/v1/books | jq .
docker ps -a | grep booksservice
```

First we put a new value (green) to the books-service/color Consul key. That is for future reference in case we want to know what color is currently running. That will come in handy when we reach the point of having all this fully automated. Then we updated nginx configuration by running consul-template. Next, `curl` command was the final piece of testing that verifies that publicly available service (this time green) continues working as expected and with no down-time. This testing should be automated but, for the sake of brevity, testing automation was skipped from this article. Finally, we're checking the output of the `docker ps -a` command. It should show booksservice_green_1 as **Up** and booksservice_blue_1 and **Exited**. 

Automation With Ansible And Jenkins
===================================

Everything we did by now was fine as a learning exercise but in "real world", all this should be automated. We'll use Ansible as orchestration tool to run all the commands we did by now and a few more. We won't go into details of the Ansible playbook books-service.yml. It can be found together with the rest of surce code in the [docker-swarm](https://github.com/vfarcic/docker-swarm) GitHub repository. Since Ansible playbook follows the same logic as manual command we run and, in general, is very easy to read, hopefully you won't have a problem understanding it without further explanation. If you run into problems, please consult [Continuous Integration, Delivery and Deployment](http://technologyconversations.com/category/continuous-integration-delivery-and-deployment/). It has quite a few articles dedicated to Ansible. Feel free to send comments (below) or contact me directly with questions if there are any.

Now, let us run **books-service.yml** playbook to deploy yet another version of our service.

```bash
ansible-playbook /vagrant/ansible/books-service.yml -i /vagrant/ansible/hosts/prod
```

Did was quite a better experience than what we did by now. A single command took care of everything.

Did it work correctly? We can check that in the same was as before.

```bash
curl http://localhost:8500/v1/kv/services/books-service/color?raw
curl http://10.100.199.200/api/v1/books | jq .
docker ps -a | grep booksservice
```

We can see that the current color is blue (previous was green), nginx works correctly,the old (green) container is stopped and the new one is running.

Can we do it without even running that single command? That's what Jenkins (and similar tools) are for. Let us first be sure that Jenkins is up and running.

```bash
ansible-playbook /vagrant/ansible/jenkins.yml -i /vagrant/ansible/hosts/prod
```

TODO: Continue

Self-Healing System
===================

What happens when something goes wrong? What happens when with services when, for example, one node goes down? Our system should be able to recuperate from such problems. Self-Healing Systems is a big topic spanning code architecture, servers setup, notifications, etc. Due to it's size, we won't go deep into Self-Healing concepts but only take the simplest scenario. We'll set it up in a way that when one node goes down, containers previously running on it are transferred to another server. We'll need Consul, Jenkins and Ansible for that.


TODO
====

* Explain books-fe.yml
* Ansible explained
* Consul health and watchers
* Jenkins failure recuperation; redeployment and notifications
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
