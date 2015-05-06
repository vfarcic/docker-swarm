# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.synced_folder ".", "/vagrant"
  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
  end
  config.vm.provision "shell", path: "bootstrap.sh"
  (1..3).each do |i|
    config.vm.define "swarm-node-0#{i}" do |node|
      node.vm.hostname = "swarm-node-0#{i}"
      node.vm.network "private_network", ip: "10.100.199.20#{i}"
      node.vm.provision :hosts
    end
  end
  config.vm.define :master do |master|
    master.vm.hostname = "swarm-master"
    master.vm.network "private_network", ip: "10.100.199.200"
    master.vm.network "forwarded_port", guest: 2376, host: 2376
    master.vm.network "forwarded_port", guest: 2375, host: 2375
    master.vm.provision :hosts
  end
  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end
end