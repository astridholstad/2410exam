#common (core) functionality 
import socket
import time
from .packet import Packet

class DRTP:
    """
    This class will represent the base for the DRTP protocol implementation
    """
    def __init__(self, ip, port):
        """
        Constructor for the protocol, ip and port using a socket setup
        """
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #note: using sock.dgram which is udp. will build my application on top of this, more on this later.
        self.timeout = 0.4 #default 400 ms timeout
        self.socket.settimeout(self.timeout)
        
    