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
        Connecting the server to the client

        """
        print("Waiting for client to connect...")

        #firstly we wait for SYN to be recieved

        while True:
            packet, client_addr = self.recieve_packet()
            if packet and packet.check_syn():
                print("SYN packet is recieved")

                #send SYN-ACK
                syn_ack = Packet(seq_num=0, ack_num=0, flags=Packet.SYN_flag | Packet.ACK_flag, recv_window=self.recv_window)
                self.send_packet(syn_ack, client_addr) #to the client 
                print("SYN-ACK is sent")

                #then we wait for ACK
                packet, _ = self.receive_packet()
                if packet and packet.check_ack():
                    print("ACK packet is received")
                    print("Connection to client is establised")
                    self.connected = True
                    self.client_addr = client_addr
                    return client_addr
                
    def             


    
