#common (core) functionality 
import socket
import time
import os
from packet import Packet

class drtp():
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
        print(f"Socket timeout set to: {self.socket.gettimeout()} seconds")

        #the current connection state
        self.connected = False
        self.seq_num = 0 #current sequence number 
        self.ack_num = 0 #current ack number

    def send_packet(self, packet, dest_addr):
        """
        This method sends a packet to a spesified destination address
        """   
        try:
            packet_bytes =  packet.convert_to_b()
            self.socket.sendto(packet_bytes, dest_addr)
        except Exception as e:
            print(f"Error sending packet: {e}")

    def receive_packet(self):
        
        
        print("receive_packet called with no extra arguments")
        """
        This method receives a packet from the socket
        uses a try catch method, returns the packet and address
        If timeout, it returns none
        """
        try:
            print("About to call socket.recvfrom")
            data, addr = self.socket.recvfrom(1024) #buffersize is 1024 bytes
            if data:
                print("Converting data to packet")
                packet = Packet.convert_from_b(data) #calls convertion method from packet, and returns a new packet with the data 
                print("hei")
                return packet, addr 
            
            
            return None, None
        except socket.timeout:
            print("Socket timeout occurred")
            return None, None #returns ether packet nor address if timeout
        except Exception as e:
            
            print(f"Error setting timeout: {e}")
            return None, None
    def close_socket(self):
        """
        this method closes the socket after a connection
        """    
        if self.socket:
            self.socket.close() #calls close function 







        
    