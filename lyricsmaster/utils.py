# -*- coding: utf-8 -*-

from stem import Signal
from stem.control import Controller
import requests


class TorController:
    def __init__(self, ip='127.0.0.1', socksport=9050, controlport=None,
                 password=''):
        """

        :param ip: string
        :param socksport: integer
        :param controlport: integer
        :param password: string
        """
        self.socksport = socksport
        self.ip = ip
        self.controlport = controlport
        self.password = password

    def get_tor_session(self):
        """

        :return: requests.session Object
        """
        session = requests.session()
        session.proxies = {'http': 'socks5://{0}:{1}'.format(self.ip,
                                                             self.socksport),
                           'https': 'socks5://{0}:{1}'.format(self.ip,
                                                              self.socksport)}
        return session

    def renew_tor_circuit(self):
        """

        """
        with Controller.from_port(port=self.controlport) as controller:
            controller.authenticate(password=self.password)
            if controller.is_newnym_available():  # true if tor would currently accept a NEWNYM signal
                controller.signal(Signal.NEWNYM)
                print('New Tor circuit created')
                return True
            else:
                delay = controller.get_newnym_wait()
                print('Dealy to create new Tor circuit: {0}s'.format(delay))
                return False
