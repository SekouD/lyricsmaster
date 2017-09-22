# -*- coding: utf-8 -*-

"""Utilities."""

import os
import re
from stem import Signal
from stem.control import Controller
import requests
try:
    basestring
except NameError:
    basestring = str

def normalize(value):
    """

    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    :param value: string.
        String.
    :return: string.
        Cleaned string.
    """
    value = re.sub('[^\w\s-]', '', value).strip()
    value = re.sub('[-\s]+', '-', value)
    return value


def set_save_folder(folder):
    """
    Sets the folder in which lyrics will be downloaded and saved.

    :param folder: string.
        Folder path.
    :return: string.
        Folder path.
    """
    if not folder:
        folder = os.path.join(os.path.expanduser("~"), 'Documents', 'LyricsMaster')
    else:
        folder = os.path.join(folder, 'LyricsMaster')
    return folder

class TorController:
    """

    :param ip: string.
        The IP adress of the TOR proxy.
    :param socksport: integer.
        The SOCKSPORT port number for TOR.
    :param controlport: integer.
        The CONTROLPORT port number for TOR.
    :param password: string.
        The password to authenticate on the TOR CONTROLPORT.
    """
    def __init__(self, ip='127.0.0.1', socksport=9050, controlport=None, password=''):
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
        def renew_circuit(password):
            controller.authenticate(password=password)
            if controller.is_newnym_available():  # true if tor would currently accept a NEWNYM signal
                controller.signal(Signal.NEWNYM)
                print('New Tor circuit created')
                return True
            else:
                delay = controller.get_newnym_wait()
                print('Dealy to create new Tor circuit: {0}s'.format(delay))
            return False

        if isinstance(self.controlport, int):
            with Controller.from_port(port=self.controlport) as controller:
                return renew_circuit(self.password)
        elif isinstance(self.controlport, basestring):
            with Controller.from_socket_file(path=self.controlport) as controller:
                return renew_circuit(self.password)


