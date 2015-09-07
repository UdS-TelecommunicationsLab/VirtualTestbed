Virtual Testbed
=============================================

Providing a [Mininet](http://mininet.org/)-based *Software Defined Networking*-testbed, including simulation of host reliability, consumption and provision of services, and link parameters like loss and delay.

**Author:** [Andreas Schmidt](mailto:schmidt@nt.uni-saarland.de)

**Website:** [Open Networking @ Saarland University](http://www.on.uni-saarland.de/)

**Institution:** [Telecommuncations Chair](http://www.nt.uni-saarland.de/) - [Saarland University](http://www.uni-saarland.de/)

**Version:** 2015.5.0

## Features

* Randomized topology with different generation algorithms and service association.
* Optional reliability simulation for hosts.
* Host uptime scheduling.
* Parametrized links.
* Provision and consumption of *HTTP*, *HTTPS*, *FTP* and *Multimedia Streaming* services.

## Installation Guide

The source code is written in **Python 2.7** so you need to have it installed on your system.

In order to run the testbed, the systems needs to have **Mininet** installed. How to do this is explained [here](http://mininet.org/download/). We highly recommend installing from source, e.g. by cloning the latest version from [GitHub](https://github.com/mininet/mininet).

Furthermore, an **SDN controller** is required to run on the same system. It is also possible to connect to a different controller, by changing the following line of `Testbed.__init__()` in `testbed.py`:

	self.ctrl = RemoteController("c1", ip=<controller ip>, port=<controller port>)

For running the **Service Simulation** you might also need the following packages, which you should find in your system's package manager. The following links give the names of the packages and point to the official websites related to them:

* [nodejs](http://nodejs.org/)
* [pure-ftpd](http://www.pureftpd.org)
* [vlc-nox](http://www.videolan.org/)
* [tstools](https://code.google.com/p/tstools/)

## Starting Simulation

The simulation can be started by running `./testbed.py` on the command-line. For this to work, `root` priviledges are required.

When run, the simulation can be canceled by pressing `Ctrl+C` on the keyboard.

## Resources

### Mininet

* [Official Website](http://mininet.org/)
* [Documentation](https://github.com/mininet/mininet/wiki/Documentation)

### Software Defined Networking

* [Open Networking Foundation](https://www.opennetworking.org/)
* [OpenFlow Specification](https://www.opennetworking.org/sdn-resources/onf-specifications/openflow)


## Questions?

Please send us feedback via [email](mailto:info@openflow.uni-saarland.de) on any problems you might encounter during installation and operation that are not covered here. The software and documentation are under constant development and improvements are highly appreciated. If you have any questions do not hesitate to ask them.
