from mininet.node import RemoteController, Host, OVSSwitch
from mininet.link import TCLink, Link, TCIntf
from random import random
from datetime import datetime as dt
import subprocess


class SdnIntf(TCIntf):
    def __init__(self, name, node=None, port=None, link=None,
                 mac=None, **params):
        super(SdnIntf, self).__init__(name, node=node, port=port, link=link, mac=mac, **params)
        self._running = True

    def up(self):
        if not self._running:
            self.ifconfig("up")
            self._running = True

    def down(self):
        if self._running:
            self.ifconfig("down")
            self._running = False


class SdnLink(TCLink):
    def __init__(self, node1, node2, port1=None, port2=None,
                 intfName1=None, intfName2=None, **params):
        Link.__init__(self, node1, node2, port1=port1, port2=port2,
                      intfName1=intfName1, intfName2=intfName2,
                      cls1=SdnIntf,
                      cls2=SdnIntf,
                      params1=params,
                      params2=params)
        self._connected = True

    def reconnect(self):
        if not self._connected:
            self.intf1.up()
            self.intf2.up()
            print "Reconnect Link {} - {}".format(self.intf1.node.name, self.intf2.node.name)
            self._connected = True

    def disconnect(self):
        if self._connected:
            self.intf1.down()
            self.intf2.down()
            print "Disconnect Link {} - {}".format(self.intf1.node.name, self.intf2.node.name)
            self._connected = False


class SdnHost(Host):
    def __init__(self, name, inNamespace=True, schedule=None, reliability=1.0, **params):
        super(SdnHost, self).__init__(name, inNamespace=inNamespace, **params)
        self.reliability = reliability
        self.schedule = schedule
        self._online = True
        self._processes = []
        self._services = []

        self.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        self.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")

    def _simulate_reliability(self):
        r = random()
        if self.reliability > r:
            self.boot()
        else:
            self.shut_down()

    def simulate_online(self):
        if self.schedule is not None:
            on_schedule = self.schedule(dt.now())
            if on_schedule and not self._online:
                self.boot()
            elif not on_schedule and self._online:
                self.shut_down()
            elif on_schedule and self._online:
                self._simulate_reliability()
            else:  # not on_schedule and offline
                pass
        else:
            self._simulate_reliability()

    def boot(self):
        if not self._online:
            for interface in self.intfList():
                interface.up()

            self.start_services()

            print "Boot Host {}".format(self.name)
            self._online = True

    def shut_down(self):
        if self._online:
            for interface in self.intfList():
                interface.down()

            self.stop_services()

            print "Shut down Host {}".format(self.name)
            self._online = False

    def start_services(self):
        for cmd in self._services:
            self._processes.append((cmd, self.popen(cmd.split())))
            print "POPEN: {} running '{}'".format(self.name, cmd)

    def stop_services(self):
        for cmd, proc in self._processes:
            proc.terminate()
            print "POPEN: {} stopped '{}'".format(self.name, cmd)
        self._processes = []

    def add_service(self, cmd):
        self._services.append(cmd)


class SdnNode(OVSSwitch):
    def __init__(self, name, reliability=1.0, **params):
        OVSSwitch.__init__(self, name, failMode='secure', datapath='kernel', inband=False, protocols=None, **params)
        self.reliability = reliability
        self._online = True
        self.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        self.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")

    def simulate_reliability(self):
        r = random()
        if self.reliability > r:
            self.boot()
        else:
            self.shut_down()

    def sdn_intf_List(self):
        return [interface for interface in self.intfList() if isinstance(interface, SdnIntf)]

    def boot(self):
        if not self._online:
            for interface in self.sdn_intf_List():
                interface.up()

            print "Boot Node {}".format(self.name)
            self._online = True

    def shut_down(self):
        if self._online:
            for interface in self.sdn_intf_List():
                interface.down()

            print "Shut down Node {}".format(self.name)
            self._online = False