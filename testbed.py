#!/usr/bin/python

"""
sdnalyzer - Testbed
"""

import time
from random import Random

from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.log import setLogLevel
from sdn import SdnLink, SdnNode, SdnHost

from topo.jellyfish import JellyFishTopology
from topo.simple import SimpleTopology


class ServiceProfile(object):
    def __init__(self, name, rnd, provider_services, consumer_services, is_provide_first=True):
        self.name = name
        self.rnd = rnd

        self._provider_services = provider_services
        self._consumer_services = consumer_services

        self._consumers = []
        self._providers = []

        self.bind_providers_first = is_provide_first

    @staticmethod
    def _bind_services(hosts, services):
        for host in hosts:
            for service in services:
                host.add_service(service.format(ip=host.IP()))

    def _connect_services(self, hosts, services, targets):
        if len(targets) > 0:
            for host in hosts:
                for service in services:
                    target = self.rnd.choice(targets)
                    host.add_service(service.format(ip=target.IP()))

    def register_provider(self, provider):
        self._providers.append(provider)

    def register_consumer(self, consumer):
        self._consumers.append(consumer)

    def provider_count(self):
        return len(self._providers)

    def apply(self):
        if self.bind_providers_first:
            self._bind_services(self._providers, self._provider_services)
            self._connect_services(self._consumers, self._consumer_services, self._providers)
        else:
            self._bind_services(self._consumers, self._consumer_services)
            self._connect_services(self._providers, self._provider_services, self._consumers)


class LinkProfile(object):
    def __init__(self, bw=1000, delay="1ms", loss=0.001):
        self.bw = bw
        self.delay = delay
        self.loss = loss


class Testbed(object):
    def __init__(self, is_reliability_simulation=True, simulation_interval=5, topology=None, rng=None, host_count=10):
        self.ctrl = RemoteController("c1", port=6653)
        self.net = Mininet()
        self.hosts = []
        self.switches = []
        self.links = []
        self.is_reliability_simulation = is_reliability_simulation
        self.simulation_interval = simulation_interval

        if rng is None:
            self.rnd = Random()
            self.rnd.seed(0)
        else:
            self.rnd = rng

        topology = SimpleTopology(self.rnd, 10) if topology is None else topology
        self.host_count = host_count
        self.switch_count = topology.switches
        self.topology = topology.generate()

        self._host_no = 0
        self._switch_no = 0

        self.schedules = [lambda now: now.minute % 2 == 0,
                          lambda now: now.minute % 2 == 1,
                          lambda now: now.minute % 5 != 0, ]

        # Link
        self.link_profile_wireless = LinkProfile(bw=10, delay="200ms", loss=15)
        self.link_profile_wired_1 = LinkProfile(bw=1000, delay="1ms", loss=1)
        self.link_profile_wired_2 = LinkProfile(bw=400, delay="20ms", loss=5)
        self.link_profile_wired_3 = LinkProfile(bw=100, delay="80ms", loss=10)
        self.link_host_profiles = [self.link_profile_wired_1, self.link_profile_wireless]
        self.link_node_profiles = [self.link_profile_wired_1, self.link_profile_wired_2, self.link_profile_wired_3]

        # Services
        self.service_profile_ping = ServiceProfile("Ping", self.rnd, [], ["ping -c 1 {ip}"])
        self.service_profiles = [
            ServiceProfile("SSH", self.rnd, ["sshd -D"], ["ssh testbed@{ip} -oStrictHostKeyChecking=no command -v ls /"]),
            ServiceProfile("FileTransfer", self.rnd, ["pure-ftpd -I 1"],
                           ["python ./services/repeater.py wget ftp://testbed:testbed@{ip}/ftp/small.txt -O /dev/null",
                            "python ./services/repeater.py wget ftp://testbed:testbed@{ip}/ftp/Tomorrowland2011Aftermovie.ts -O /dev/null"]),
            ServiceProfile("Web", self.rnd, ["nodejs ./services/webServer.js"],
                           ["python ./services/repeater.py curl {ip}"]),
            ServiceProfile("Secure Web", self.rnd, ["nodejs ./services/secureWebServer.js"],
                           ["python ./services/repeater.py curl https://{ip}"]),
            ServiceProfile("Video", self.rnd, ["tsplay ./services/Tomorrowland2011Aftermovie.ts -loop -udp {ip}:554"],
                           [r'su - vagrant -c "cvlc --no-embedded-video --video-title=UDP-TSPLAY '
                            r'--udp-caching 1000 --deinterlace 0 --deinterlace-mode yadif '
                            r'--sout-deinterlace-mode x udp://@:554"'], is_provide_first=False)
        ]

        """
        TODO:
            DNS:  !! consume part not working
                provide:    "dnsmasq -k -h -z --addn-hosts=/vagrant/testbed/services/hosts"
                consume:    "dig sdnalyzer @{ip}"

            RTPS:
                provide: ["nodejs ./services/rtsp/rtsp-server/server.js", "ffmpeg -re -i ./services/rtsp/big_buck_bunny_480p_h264.mov -c:v copy -c:a copy -f flv rtmp://localhost/live/stream"]
                consume: "su - vagrant -c 'cvlc --no-embedded-video --video-title=Video --deinterlace 0 --deinterlace-mode yadif  --sout-deinterlace-mode x rtsp://{ip}/live/stream'"
        """

    def _add_switch(self, reliability=1.0):
        self._switch_no += 1
        ip, mac = self.get_next_ip_and_mac()
        datapath_id = "0001{}".format(mac.replace(":", ""))
        sw = self.net.addSwitch("s{}".format(self._switch_no), cls=SdnNode, reliability=reliability, ip=ip,
                                dpid=datapath_id)
        self.switches.append(sw)
        return sw

    def _start_switches(self):
        for sw in self.switches:
            sw.start([self.ctrl])

    def _add_link(self, left, right, profile=None):
        if profile is None:
            profile = LinkProfile()

        link = self.net.addLink(left, right, cls=SdnLink)
        link.intf1.config(bw=profile.bw, delay=profile.delay, loss=profile.loss)
        link.intf2.config(bw=profile.bw, delay=profile.delay, loss=profile.loss)
        self.links.append(link)
        return link

    def get_next_ip_and_mac(self):
        cnt = self._host_no + self._switch_no + 1
        ip = "10.0.{}.{}/8".format(cnt // 255, cnt % 255)
        mac = "c0:de:00:00:{:02x}:{:02x}".format(cnt // 256, cnt % 256)
        return ip, mac

    def _add_host(self, reliability=1.0, schedule=None):
        self._host_no += 1
        ip, mac = self.get_next_ip_and_mac()
        host = self.net.addHost("h{}".format(self._host_no), ip=ip, mac=mac, cls=SdnHost,
                                reliability=reliability if self.is_reliability_simulation else 1,
                                schedule=schedule if self.is_reliability_simulation else None)

        self.hosts.append(host)
        return host

    def _start_simulation(self):
        for host in self.hosts:
            host.start_services()

        try:
            while True:
                for host in self.hosts:
                    host.simulate_online()

                time.sleep(self.simulation_interval)
        except KeyboardInterrupt:
            print "End simulation."

    def _stop_simulation(self):
        for host in self.hosts:
            host.shut_down()

        self.net.stop()

    def _apply_profiles(self):
        self.service_profiles.append(self.service_profile_ping)

        for profile in self.service_profiles:
            profile.apply()

    def _generate_host(self, link_profiles):
        reliability = 0.85 + self.rnd.random() * 0.1
        schedule = self.rnd.choice(self.schedules) if self.rnd.random() > 0.8 else None
        hst = self._add_host(reliability=reliability, schedule=schedule)
        if self.service_profile_ping.provider_count() == 0:
            self.service_profile_ping.register_provider(hst)
        elif self.rnd.random() > 0.4:
            profile = self.rnd.choice(self.service_profiles)
            if self.rnd.random() > 0.5:
                profile.register_provider(hst)
            else:
                profile.register_consumer(hst)
        else:
            self.service_profile_ping.register_consumer(hst)
        self._add_link(hst, self.rnd.choice(self.switches), self.rnd.choice(link_profiles))

    def _generate_network(self):
        for _ in range(self.switch_count):
            self._add_switch()

        for _ in range(self.host_count):
            self._generate_host(self.link_host_profiles)

        for left_id in self.topology:
            for right_id in self.topology[left_id]:
                if left_id < right_id:
                    profile = self.rnd.choice(self.link_node_profiles)
                    self._add_link(self.switches[left_id], self.switches[right_id], profile)

    def run(self):
        self._generate_network()
        self._start_switches()
        self.net.build()
        self._apply_profiles()
        self._start_simulation()
        self._stop_simulation()


if __name__ == '__main__':
    setLogLevel('info')
    rng = Random()
    rng.seed = 0
    topo = JellyFishTopology(rng, 7, 3)
    tb = Testbed(is_reliability_simulation=True, simulation_interval=5, topology=topo, rng=rng, host_count=30)
    tb.run()
