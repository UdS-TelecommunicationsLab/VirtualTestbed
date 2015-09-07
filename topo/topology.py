class Topology(object):
    def __init__(self, rnd, switches):
        self.rnd = rnd
        self.switches = switches

    def generate(self):
        raise NotImplemented("Cannot generate topology using abstract base class.")
