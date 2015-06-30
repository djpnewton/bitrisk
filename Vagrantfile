# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty32"
  config.vm.network :forwarded_port, host: 5000, guest: 5000
  config.vm.network :forwarded_port, host: 8888, guest: 8888

  config.vm.provision :shell, path: "vagrant_bootstrap.sh"
  config.vm.provision :shell, path: "vagrant_bitrisk.sh", privileged: "false"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  config.vm.provider "virtualbox" do |vb|
  #   # Display the VirtualBox GUI when booting the machine
  #   vb.gui = true
  #
    # Customize the amount of memory on the VM:
    vb.memory = "2048"
  end
end
