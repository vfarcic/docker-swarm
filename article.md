Scaling Containers with Docker Swarm, Docker Compose and Consul
===============================================================

Previous articles put a lot a focus on Continuous Delivery and Containers (TODO: links). I explained how to continuously build, test and deploy micro services packaged into containers and do that across multiple servers, without downtime and with the ability to rollback (TODO: links). We used Ansible, Docker, Jenkins and few other tools (TODO: links). Now it's time to extend this and scale services across any number of servers. We'll treat servers as one server farm and deploy containers not to predefined locations but to those that have the least number of containers running. Instead of thinking of each server as an individual place where we deploy, we'll treat all of them as one unit. We'll continue using some of the same tools we used before. 

* Vagrant with VirtualBox TODO: description
* Docker TODO: description
* Ansible TODO: description
* Jenkins TODO: description
* nginx TODO: description

On top of those we'll see some new ones like following.

* Docker Compose TODO: description
* Docker Swarm TODO: description
* Consul TODO: description

In order to follow this article, set up VirtualBox and Vagrant. Once done, please install vagrant-cachier plugin. While it's not mandatory, it will speed up installations.
 
```bash
vagrant plugin install vagrant-cachier
```

With prerequisites out of our way, we're ready to start building our server farm.

Servers Setup
=============

We'll create four virtual machines. One (swarm-master) will be used to orchestrate deployments. It's primary function is act as Docker Swarm master node. Instead of deciding in advance where to deploy something, we'll tell Docker Swarm what to deploy and it will deploy it to a node that has least containers running. There are other strategies that we could employ but, as a demonstration, this default strategy should suffice. Besides Swarm, we'll also set up Ansible, Jenkins, Consul and Docker Compose on that same node. Three additional virtual machines will be created and named swarm-node-01, swarm-node-02 and swarm-node-03. Unlike swarm-master, those nodes will have only Consul and Swarm agents. Their purpose is to host our applications (packed as Docker containers). Later on, if we need more hardware, we would just add one more node and let Swarm take care of balancing deployments.

We'll start by bringing up Vagrant VMs. Keep in mind that four virtual machines will be created and that each of them requires 1GB of RAM. On a 8GB 64 bits computer, you should have no problem running those VMs. If, you don't have that much memory to spare, please try lowering `v.memory = 1024` to some smaller value.

```bash
vagrant up
```

In order for Ansible to be able to set up those servers, we'll have to create SSH keys and copy them to the master node.

```bash
vagrant ssh swarm-node-01
ssh-keygen
exit

vagrant ssh swarm-node-02
ssh-keygen
exit

vagrant ssh swarm-node-03
ssh-keygen
exit

vagrant ssh swarm-master
ssh-keygen
ssh-copy-id vagrant@10.100.199.200 # pass: vagrant
ssh-copy-id vagrant@10.100.199.201 # pass: vagrant
ssh-copy-id vagrant@10.100.199.202 # pass: vagrant
ssh-copy-id vagrant@10.100.199.203 # pass: vagrant
```

With SSH communication open, we can set up all the servers by running following. We'll use Ansible playbook defined in [infra.yml](TODO).

```bash
ansible-playbook /vagrant/ansible/infra.yml -i /vagrant/ansible/hosts/prod
```

I won't go into details regarding Ansible. You can find plenty of articles about it both in the official site as well as in other posts on this blog. Important detial is that, once the execution of that Ansible playbook is done, swarm-master will have Jenkins, Consul, Docker Compose and Docker Swarm installed. The other three nodes received instructions to install only Consul and Swarm agents. With this playbook we saved time on going into details on how to install each of those frameworks. For more information please consult official documentation.
 
Consul
======

**TODO: Consult description**

We can see all members of our Consul cluster with the following command.

```bash
consul members
```

The output should be something similar to the following.

```
Node           Address              Status  Type    Build  Protocol
swarm-master   10.100.199.200:8301  alive   server  0.5.0  2
swarm-node-01  10.100.199.201:8301  alive   client  0.5.0  2
swarm-node-02  10.100.199.202:8301  alive   client  0.5.0  2
swarm-node-03  10.100.199.203:8301  alive   client  0.5.0  2
```

With Consul running on all servers we have the ability to store information about applications we deploy and have it propagated to all servers. That way, applications store data locally and do not have to worry about location of a central server. At the same time, when an application needs information about others, it can also request it locally. Being able to propagate information across all servers is an essential requirement for all distributed systems.

Another way to retrieve the same information is through Consul's REST API. We can run following command.

```bash
curl localhost:8500/v1/catalog/nodes | jq .
```

This produces following JSON output formatted by jq.

```
[
  {
    "Node": "swarm-master",
    "Address": "10.100.199.200"
  },
  {
    "Node": "swarm-node-01",
    "Address": "10.100.199.201"
  },
  {
    "Node": "swarm-node-02",
    "Address": "10.100.199.202"
  },
  {
    "Node": "swarm-node-03",
    "Address": "10.100.199.203"
  }
]
```

Later on, when we deploy the first application, we'll see Consul in more detail. Please take note that even though we'll use Consul by running commands from Shell (at least until we get to health section), it has an UI that can be accessed by opening [http://10.100.199.200:8500](http://10.100.199.200:8500).

Docker Swarm
============

**TODO: Swarm description**

Docker Swarm is easiest to use when DOCKER_HOST environment variable is present.

```bash
export DOCKER_HOST=tcp://0.0.0.0:2375
docker info
```

The output should be similar to the following.

```
Containers: 9
Strategy: spread
Filters: affinity, health, constraint, port, dependency
Nodes: 3
 swarm-node-01: 10.100.199.201:2375
  └ Containers: 3
  └ Reserved CPUs: 0 / 1
  └ Reserved Memory: 0 B / 1.019 GiB
 swarm-node-02: 10.100.199.202:2375
  └ Containers: 3
  └ Reserved CPUs: 0 / 1
  └ Reserved Memory: 0 B / 1.019 GiB
 swarm-node-03: 10.100.199.203:2375
  └ Containers: 3
  └ Reserved CPUs: 0 / 1
  └ Reserved Memory: 0 B / 1.019 GiB
```

We get immediate information regarding number of deployed containers, strategy Swarm uses to distribute them, number of nodes (servers) and additional details for each of them, etc At the moment, each server has one Swarm agent and two Consul registrators deployed. All those deployments were done as part of the infra.yml playbook that we run earlier.
  
Deployment
==========

Let us deploy the first service. We'll use Ansible playbook defined in [books-service.yml](TODO).

```bash
ansible-playbook /vagrant/ansible/books-service.yml -i /vagrant/ansible/hosts/prod
```

The playbook that we just run follows the same logic as the one we already discussed in [blue/green deployment](TODO). The major difference is that this time there are few things that are unknown to us before playbook is actually run. We don't know the IP of the node service will be deployed to. Since the idea behind this setup is not only to distribute applications between multiple services but also to scale them effortlessly, port is also unknown. If we'd define it in advance there would be a probable danger that multiple instances would use the same port and clash.

We'll go through what this playbook does and, later on, we'll explore how it was done (TODO: Move how to a separate article).

Books service consists of two containers. One is the application itself and the other contains MongoDB that the application needs. Let's see where were they deployed to.

```bash
docker ps | grep booksservice
```

The output will deffer from case to case and it will look similar to the following. Docker ps command will output more information than presented below. Those that are not relevant for this article were removed.

```bash
vfarcic/books-service:latest    10.100.199.203:32768->8080/tcp    swarm-node-03/booksservice_blue_1   
mongo:latest                    10.100.199.201:32768->27017/tcp   swarm-node-01/booksservice_db_1
```

We can see that the application container was deployed on swarm-node-03 and is listening to the port 32768. Database, on the other hand, went to a separate node swarm-node-01 and listens to the port 32768. Let's check whether those two containers communicate with each other. When we request data from the application container (booksservice_blue_1) it will retrieve it from the database (booksservice_db_1). The books service can store and retrieve books. In order to test it we'll request service to insert few and than ask it to retrieve all store records.

```bash
curl -H 'Content-Type: application/json' -X PUT -d '{"_id": 1, "title": "My First Book", "author": "Joh Doe", "description": "Not a very good book"}' http://10.100.199.200/api/v1/books | jq .
curl -H 'Content-Type: application/json' -X PUT -d '{"_id": 2, "title": "My Second Book", "author": "John Doe", "description": "Not a bad as the first book"}' http://10.100.199.200/api/v1/books | jq .
curl -H 'Content-Type: application/json' -X PUT -d '{"_id": 3, "title": "My Third Book", "author": "John Doe", "description": "Failed writers club"}' http://10.100.199.200/api/v1/books | jq .
curl http://10.100.199.200/api/v1/books | jq .
```

The result of the last request is following.

```
[
  {
    "_id": 1,
    "title": "My First Book",
    "author": "John Doe"
  },
  {
    "_id": 2,
    "title": "My Second Book",
    "author": "John Doe"
  },
  {
    "_id": 3,
    "title": "My Third Book",
    "author": "John Doe"
  }
]
```

All three books that we requested the service to put to its database were stored. You might have noticed that we did not perform requests from the IP/port where the application is running. Instead of doing `curl` against 10.100.199.203:32768 we performed requests through 10.100.199.200 on the standard 80 port. That's where our nginx server is deployed and, through the "magic" of Consul, Registrator and Templating, nginx was updated to point to the correct IP/port. Details of how this happened are explained in the next [article](TODO). For now, it is important to know that data about our application is stored in Consul and freely accesible to every other service that might need it. In this case, that service is nginx that acts are reverse proxy and load balancer at the same time.

To prove this, let's run following. 

```bash
curl http://localhost:8500/v1/catalog/service/books-service-blue | jq .
```

Since we'll practice [blue/green deployment](TODO), name of the service is alternating between books-service-blue and books-service-green. Since this is the first time we deployed it, the name is blue. The next deployment will be green, than blue again and so on.

```
[
  {
    "Node": "swarm-node-03",
    "Address": "10.100.199.203",
    "ServiceID": "swarm-node-03:booksservice_blue_1:8080",
    "ServiceName": "books-service-blue",
    "ServiceTags": null,
    "ServiceAddress": "",
    "ServicePort": 32768
  }
]
```

We also have the information stored as books-service-lb (short for load balancer) with IP and port that should be accessible to public.

```bash
curl http://localhost:8500/v1/catalog/service/books-service-lb | jq .
```

Unlike previous outputs that can be different from case to case (IPs and ports are changing from deployment to deployment), this output should always be the same.

```
[
  {
    "Node": "swarm-master",
    "Address": "10.100.199.200",
    "ServiceID": "books-service-lb",
    "ServiceName": "books-service-lb",
    "ServiceTags": [
      "service"
    ],
    "ServiceAddress": "10.100.199.200",
    "ServicePort": 80
  }
]
```

No matter where we deploy our services, they are always accessible from a single location 10.100.199.200 (at least until we start adding multiple load balancers) and are always accessible from the default HTTP port 80. nginx will make sure that requests are sent to the correct service on the correct IP and port.

We can deploy another service using the same principle. This time it will be a front-end for our books-service.

```bash
ansible-playbook /vagrant/ansible/books-fe.yml -i /vagrant/ansible/hosts/prod
```

TODO: Output and explanation

You can see the result by opening [http://10.100.199.200](http://10.100.199.200) in your browser. It's an AngularJS UI that uses books-service to retrieve all the available books. As with books-service, you can run following to see where was the container deployed.

TODO: Fix PUT in books-service

```bash
docker ps | grep booksfe
curl http://localhost:8500/v1/catalog/service/books-fe-blue | jq .
```

Now let us imagine that someone changed the code of books-service and we want to deploy a new release. The procedure is exactly the same.

```bash
ansible-playbook /vagrant/ansible/books-service.yml -i /vagrant/ansible/hosts/prod
```

To verify that everything went as expected we can query Consul.

```bash
curl http://localhost:8500/v1/catalog/service/books-service-green | jq .
```

While blue release was on IP 10.100.199.203, this time the container was deployed to 10.100.199.202. Docker swarm checked which server had the least number of containers running and decided that the best place to run the contained is swarm-node-02.

```
[
  {
    "Node": "swarm-node-02",
    "Address": "10.100.199.202",
    "ServiceID": "swarm-node-02:booksservice_green_1:8080",
    "ServiceName": "books-service-green",
    "ServiceTags": null,
    "ServiceAddress": "",
    "ServicePort": 32768
  }
]
```

Jenkins
=======

The only thing missing for fully [continuous deployment](TODO) is to have something that will detect changes to our source code repository, build, test and deploy containers. With Docker it's very easy to standardize and have all builds, testing and deployments follow the same standard. Please read [TODO](TODO) for more information on this subject. For this article, I created only jobs that do the actual deployment. We'll use them later in the next article when we explore ways to recuperate from failure. Until then, you can take a look at the running Jenkins instance by opening [http://10.100.199.200:8080/](http://10.100.199.200:8080/).  


To Be Continued
===============

In the next article we're exploring additional features of Consul and how we can utilize them to recuperate from failures. Whenever some container stops working, Consul will detect it and send a notification to Jenkins which, in turn, will redeploy the failed container and send an email notification.

From there on we'll explore how we could host multiple versions of the same applications and facilitate deployments to multiple customers.

Finally, I'll go in depth how was all this accomplished and show you manual commands with Docker Compose, Consul-Template, Registrator, etc. It is required to understand those commands in order to reach the final outcome in form of Ansible playbooks that we saw earlier. You got the taste of **what** and now it's time to understand **how**.

TODO
====

* More info about Consul
* More info about Swarm
* More info about Registrator
* Links to previous articles
* Consul health and watchers
* Jenkins failure recuperation; redeployment and notifications
* Manual commands
* Ansible explained