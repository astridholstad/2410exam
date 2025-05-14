#common (core) functionality 
import socket
import time
import os
from packet import Packet

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
        self.timeout = 0.4 #default 400 ms timeout, will use this for packet loss 
        self.socket.settimeout(self.timeout)

        #the current connection state
        self.connection = False
        self.seq_num = 0 #current sequence number 
        self.ack_num = 0 #current ack number


    def send_packet(self, packet, dest_addr):
        """
        This method sends a packet to a spesified destination address
        """   
        packet_bytes =  packet.convert_to_b()
        self.socket.sendto(packet_bytes, dest_addr)

    def receive_packet(self):
        """
        This method recieves a packet from the socket
        uses a try catch method, returns the packet and address
        If timeout, it returns nothing
        """   
        try:
            data, addr = self.socket.recvfrom(1024) #buffersize is 1024 bytes
            packet = Packet.convert_to_b(data) #calls convertion method from packet, and returns a new packet with the data 
            return packet, addr
        except:
            socket.timeout = 0
            return None, None #returns ether packet nor address if timeout
        

    def close_socket(self):
        """
        this method closes the socket after a connection
        """    
        if self.socket:
            self.socket.close() #calls close function 







        
    