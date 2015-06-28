Scaling Containers with Docker Swarm, Docker Compose and Consul (Part 4/4) - Scaling Services and Clients
=========================================================================================================

TODO: Links to all articles

In the previous article (TODO: Link) we switched from manual deployment to automatic one with Jenkins and Ansible. In the quest for **zero-downtime** we employed Consul to check **health** of our services and initiate deployment through Jenkins is one of them fails.

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

Scaling Services
================

Let us scale our **books-service** so that it is running on at least two nodes. That way we can be sure that if one of them fails, the other one will be running while the **rescue** setup we did in the previous article (TODO: Link) is finished and the failed service is redeployed.

```bash
docker ps | grep booksservice
cd /data/compose/config/books-service
docker-compose scale blue=2
docker ps | grep booksservice
```

If you are currently running **green**, please change the above command to `docker-compose scale blue=2`.

The last `docker ps` command listed that two instances of our service are running; **booksservice_blue_1** and **booksservice_blue_2**.

As with everything else we did by now, we already added scaling option to the Ansible setup. Let's see how to do the equivalent of the command above with Ansible. We'll scale the service to three instances.

```bash
ansible-playbook /vagrant/ansible/books-service.yml -i /vagrant/ansible/hosts/prod --extra-vars "service_instances=3"
docker ps | grep booksservice
```

Just like that we have three instances of our service. 

We won't go into details but you can probably imagine the potential this has beyond simple scaling to allow two services to be running in case one fails. We could, for example, create a system that would scale services that are under heavy load. That can be done with Consul that would monitor services response times and, if they reach some threshold, scale them to meet the increased traffic demand.

Just as easy, we can scale down back to two services.

```bash
ansible-playbook /vagrant/ansible/books-service.yml -i /vagrant/ansible/hosts/prod --extra-vars "service_instances=2"
docker ps | grep booksservice
```

All this would be pointless if our **nginx** configuration would not support it. Even though we have multiple instances of the same service, **nginx** needs to know about it and perform load balancing across all of them. The Ansible playbook that we've been using already handles this scenario.

Let's take a look at **nginx** configuration related to the **books-service**.

```bash
cat /data/nginx/includes/books-service.conf
```

The output is following.

```
location /api/v1/books {
  proxy_pass http://books-service/api/v1/books;
}
```

This tells **nginx** that whenever someone requests an address that starts with **/api/v1/books**, it should be proxied to **http://books-service/api/v1/books**. Let's take a look at the configuration for the **books-service** address (after all, it's not a real domain).

```bash
cat /data/nginx/upstreams/books-service.conf
docker ps | grep booksservice
```

The output will differ from case to case. The important part is that the list of nginx **upstream** servers should conicide with the list of services we obtained with `docker ps`. One possible output of the first command could be following.

```
upstream books-service {
    server  10.100.199.202:32770;
    server  10.100.199.203:32781;
}
```

This tells **nginx** to balance requests between those two servers and ports.

We already mentioned in previous articles that we are creating nginx configurations using Consul Template. Let us go through it again. The **blue** template looks like this.

```
upstream books-service {
    {{range service "books-service-blue" "any" }}
    server {{.Address}}:{{.Port}};
    {{end}}
}
```

It tells Consul to retrieve a all instances of a service (range) called books-service-blue ignoring their status (any). For each of those instances it should write the IP (.Address) and port (.Port). We created a template for both blue and green versions. When we deployed with Ansible, it took care of creating this template (with correct color), copying it to the server and running Consul Template which, in turn, reloaded nginx at the end of the process.

The current setting does not scale MongoDB. I'll leave that up to you. The process should be the same as with the service itself with additional caveat that Mongo should be set to use **Replica Set** with one instance being primary and the rest secondary instances.


The End (For Now)
=================

We covered a lot of ground in these four articles (TODO: Links) and left even more possibilities unexplored. We could, host one the same cluster not only different services but copies of the same services for multiple customers. We could create logic that deploys services not only to nodes that have the least number of containers but those that have enough CPU or memory. We could add Kubernetes or Mesos to the setup and have more powerful and precise ways to schedule deployments. However, time is limited and not all can be explored at once.

I'd like to hear from you what would be the next subject to explore or which parts of these articles require more details.

If you have any trouble following these examples, please let me know and I'll give my best to help you out.
