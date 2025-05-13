#server functionality class
import os
from .DRTP_protocol import DRTP
from .packet import Packet
import datetime
import time




class Server:
    """
    This will be used to initialze the reciever with a window size 
    DRTP implementation of the server (the reviecer of the file)
    The server need to handle ip, port, sliding window, file data, discarded sequence numbers. 


    """

    def __init__(self, ip, port, window_size=15, discarded_seq=None):
        """
        Constructor for the client with a set window size

        """
        super().__init__(ip, port)
        self.recv_window= window_size
        self.expct_seq_num = 1 #next expected sequence number
        self.buffer = {} #buffer to store data, as a dict
        self.discarded_seq = discarded_seq
        self.discard_done = False # flag that is T/F to check if discard have been done.

        #bind the socket door to the server address
        self.socket.bind((ip, port))

    def wait_for_handshake(self):
        """
        Wait for client to perform a three way handshake
        
        """

    
