#server functionality class
import os
from .DRTP_protocol import DRTP
from .packet import Packet




class Server:
    """
    This will be used to initialze the reciever with a  window size 
    DRTP implementation of the server (the reviecer of the file)
    The server need to handle ip, port, sliding window, file data, discarded sequence numbers. 


    """

    def __init__(self):
        pass
