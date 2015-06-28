Scaling Containers with Docker Swarm, Docker Compose and Consul (Part 3/4) - Automation with Ansible and Jenkins and Self-Healing procedure
===========================================================================================================================================

TODO: Links to all articles

In the previous article (TODO: Link) we manually deployed the first version of our service together with a separate instance of the Mongo DB container. Both are running on different servers. Docker Swarm decided where to run our containers and Consul stored information about service IPs and ports as well as other useful information. That data was used to link one service with another as well as to provide information nginx needed to create proxy.

We'll continue where we left and deploy a second version of our service. Since we're practicing blue/green deployment, the first version was called **blue** and the next one will be **green**. This time there will be some additional complications. Deploying the second time is a bit more complicated since there are additional things to consider, especially since our goal is to have no downtime.

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

Everything we did by now was fine as a learning exercise but in "real world", all this should be automated. We'll use Ansible as orchestration tool to run all the commands we did by now and a few more. We won't go into details of the Ansible playbook books-service.yml. It can be found together with the rest of surce code in the [docker-swarm](https://github.com/vfarcic/docker-swarm) GitHub repository. Since Ansible playbook follows the same logic as manual command we run and, in general, its playbooks are very easy to read, hopefully you won't have a problem understanding it without further explanation. If you run into problems, please consult [Continuous Integration, Delivery and Deployment](http://technologyconversations.com/category/continuous-integration-delivery-and-deployment/). It has quite a few articles dedicated to Ansible. Feel free to send comments (below) or contact me directly with questions if there are any.

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

Can we do it without even running that single command? That's what Jenkins (and similar tools) are for. If you already used Jenkins you might think that you should skip this part. Please bear with me because once we set it up, we'll go through ways to recuperate from failure.

Let us first make sure that Jenkins is up and running.

```bash
ansible-playbook /vagrant/ansible/jenkins.yml -i /vagrant/ansible/hosts/prod
```

Great thing about orchestration tools like Ansible is that they always check the state and act only when needed. If Jenkins was already up-and-running, Ansible did nothing. If, on the other hand, it was not deployed or was shut down, Ansible acted accordingly and made it work again.

Jenkins can be viewed by opening [http://10.100.199.200:8080/](http://10.100.199.200:8080/) in your favourite browser. Among other jobs, you should see **books-service** job that we'll use to deploy new version of our service.
 
TODO: Image

Next, create a new node by using following steps.

* Click **Manage Jenkins** > **Manage Nodes** > **New Node**
* Name it **cd**, select **Dumb Slave** and click **OK**
* Type **/data/jenkins/slaves/cd** as **Remote Root Directory**
* Type **10.100.199.200** as **Host**
* Click **Add* next to **Credentials**
* Use **vagrant** as both **Username** and **Password** and click **Add**
* Click *Save*

TODO: Image

Now we can run the **books-service** job. From the Jenkins home page, click **books-service** link and than the **Build Now** button. You'll see the icon in **Build History** blinking until its finished running. Once done, there will be a blue icon indicating that everything run correctly. 

TODO: Image

Run `docker ps` to confirm that the **green** service is running.

```bash
docker ps -a | grep booksservice
```

What is missing from this Jenkins job configuration is **Source Code Management** setup that would pull the code from repository whenever there is any change and initiate deployment. After all, we don't want to waste time pushing the **Build** button every time someone changes the code. Since this is being run in local, SCM setup cannot be demonstrated. You should have not trouble finding the information online.

Now let us more to more interesting things and see how to recuperate from failures.

Self-Healing System
===================

What happens when something goes wrong? What happens when, for example, one service or the whole node goes down? Our system should be able to recuperate from such problems. Self-Healing Systems is a big topic spanning code architecture, servers setup, notifications, etc. Due to it's size, we won't go deep into **Self-Healing** concepts but only take the simplest scenario. We'll set the system up in a way that when one service goes down it is redeployed. If, on the other hand, the whole node stops working, all containers from that node will be transferred to a healty one. We'll need Consul, Jenkins and Ansible for that.

Here's the flow we want to accomplish. We need something to monitor **health** of our services. We'll use **[Consul](https://www.consul.io/)** for this purpose. If one of them does not respond to a request made every 10 seconds, Jenkins job will be called. Jenkins, in turn, will run **[Ansible](http://www.ansible.com/home)** that will make sure that everything related to that service is up and running. Since we're using **[Docker Swarm](https://docs.docker.com/swarm/)**, if the cause of service not working is server shutdown, healthy node will be selected instead. We could have done this without Jenkins but since we already have it set up and it provides a lot of nice and easy to configure features (even though we don't use them in this example), we'll stick with it.

Before we go into details, let's see it in action. We'll start by stopping our service.

```bash
docker ps | grep booksservice
docker stop booksservice_green_1
docker ps -a
```

If the first `docker ps` command told you that you are currently running **blue** version, please change the above command to stop **booksservice_blue_1**. The second `docker ps -a` command is used to verify that the service is indeed stopped (status should be **Exited**).

Now that we stopped our service, Consul will detect that since it runs verifications every 10 seconds. We can see it's log with the following.

```bash
cat /data/consul/logs/watchers.log
```

The output should be similar to the one below.

```
Consul watch request:
[{"Node":"swarm-master","CheckID":"service:books-service","Name":"Service 'books-service' check","Status":"critical","Notes":"","Output":"HTTP GET http://10.100.199.200/api/v1/books: 502 Bad Gateway Output: \u003chtml\u003e\r\n\u003chead\u003e\u003ctitle\u003e502 Bad Gateway\u003c/title\u003e\u003c/head\u003e\r\n\u003cbody bgcolor=\"white\"\u003e\r\n\u003ccenter\u003e\u003ch1\u003e502 Bad Gateway\u003c/h1\u003e\u003c/center\u003e\r\n\u003chr\u003e\u003ccenter\u003enginx/1.9.2\u003c/center\u003e\r\n\u003c/body\u003e\r\n\u003c/html\u003e\r\n","ServiceID":"books-service","ServiceName":"books-service"}]

>>> Service books-service is critical

Triggering Jenkins job http://10.100.199.200:8080/job/books-service/build
```

It detected that there was something wrong and made a request to [http://10.100.199.200:8080/job/books-service/build](http://10.100.199.200:8080/job/books-service/build). This in turn triggered the same Jenkins job we run manually and performed another deployment.

```bash
docker ps | grep booksservice
```

Assuming that you stopped the **green** version, this time you would see **booksservice_blue_1** running.

Same procedure would happen if we stop MongoDB or even any of the nodes (for example swarm-node-01). If some service is not responding, Consul triggers corresponding Jenkins job and repeats the deployment cycle. Even if the whole node is down services residing on that node not respond and the procedure would be repeated.
 
How does this work?

Every time we deploy a service with Ansible (at the moment only one but that could extend to any number of them) we're making sure that Consul configuration is updated with information about the service. Let's take a look at configuration for the **books-service**.

```bash
cat /etc/consul.d/service-books-service.json
```

The output should be following.

```
{
    "service": {
        "name": "books-service",
        "tags": ["service"],
        "port": 80,
        "address": "10.100.199.200",
        "checks": [{
            "id": "api",
            "name": "HTTP on port 80",
            "http": "http://10.100.199.200/api/v1/books",
            "interval": "10s"
        }]
    }
}
```

It has the information about the service. Keep in mind that, unlike information stored with Consul Registrator that has the precise server and port a service is running on, this information is from the point of view of users. In other words, it points to our public IP and port (10.100.199.200) that is handled by **nginx** which, in turn, redirects requests to the server where actual service is residing. The reason for this is that in this particular case, we only care that service as a whole is never interrupted. Even though we're continually deploying **blue** and **green** releases, one of them should always be running.

Finally, there is **checks** section. it tells consul to perform **http** request on **http://10.100.199.200/api/v1/books** every **10** seconds. If server returns anything but code **200**, Consul will consider this service not working properly and initiate "rescue" procedure.

Each service should have it's own service configuration file with **checks** section tailored to its specifics. There are different types of checks but, in our case, **http** is doing exactly what we need.
 
Next in line is **watchers.json** configuration file.

```bash
cat /etc/consul.d/watchers.json
```

The output is following.

```
{
  "watches": [
    {
      "type": "checks",
      "state": "critical",
      "handler": "/data/consul/scripts/redeploy_service.sh >>/data/consul/logs/watchers.log"
    }
  ]
}
```

It tells Consul to watch all services of type **checks**. This filter is necessary since we have services registered with Consul and we want only those we specified to be checked. Second filter is **state**. We want only service in **critical** state to be retrieved. Finally, if Consul finds a service that has both **type** and **state** match, it will run the **redeploy_service.sh** command set in **handler**. Let's take a look at it.
 
```bash
cat /data/consul/scripts/redeploy_service.sh
```

The output is following.

```bash
#!/usr/bin/env bash

RED='\033[0;31m'
NC='\033[0;0m'

read -r JSON
echo "Consul watch request:"
echo "$JSON"
echo "$JSON" | jq -r '.[] | select(.CheckID | contains("service:")) | .ServiceName' | while read SERVICE_NAME
do
  echo ""
  echo -e ">>> ${RED}Service $SERVICE_NAME is critical${NC}"
  echo ""
  echo "Triggering Jenkins job http://10.100.199.200:8080/job/$SERVICE_NAME/build"
  curl -X POST http://10.100.199.200:8080/job/$SERVICE_NAME/build
done
```

I won't go into details of this script but say that it receives JSON from Consul, parses it to find out the name of the service that failed and, finally, makes a request to Jenkins to run the corresponding job and redeploys that service.

To Be Continued
===============

We deployed multiple releases of our service following **blue/green deployment** technique. At no time service was interrupted during the deployment process. We have the whole process automated with Ansible and run by Jenkins.

We introduced some new Consul features that allow us to monitor the status of our services and perform measures that will recuperate them from failures. In the current setup we still cannot guarantee zero downtime since it can take up to 10 seconds for Consul to detect a failure and a bit more time for Jenkins/Ansible to perform the deployment.

The next article will go further and explore ways to scale every service into multiple nodes so that when one instance goes down, there is at least one more running. That way, even though we can redeploy any failed service, during that process a second instance is running and making sure that there is no downtime. 

TODO: Link to the next article
