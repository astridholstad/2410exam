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
        Constructor for the protocol, it takes in ip and port parameter
        """
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #note: using sock.dgram which is udp. 
        self.timeout = 0.4 #default 400 ms timeout, will use this for packet loss 
        self.socket.settimeout(self.timeout)

        
         # Create new socket with improved options
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        

        #the current connection state
        self.connected = False
        self.seq_num = 0 #current sequence number 
        self.ack_num = 0 #current ack number
        self.client_addr = None

    def send_packet(self, packet, dest_addr):
        """
        This method sends a packet to a spesified destination address
        uses convertion by calling the convert_to_b() method
        The converted packet to bytes is being sendt to a dest address

        """   
        try:
            packet_bytes =  packet.convert_to_b()
            self.socket.sendto(packet_bytes, dest_addr)
        except Exception as e: #error handling
            print(f"Error sending packet: {e}")

    def receive_packet(self):
        """
        This method receives a packet from the socket
        The method, returns the packet converted back to a packet from bytes
        and the source address 
        
        """
        try:
            data, addr = self.socket.recvfrom(1024) #buffersize is 1024 bytes
            if data:
                packet = Packet.convert_from_b(data) #calls convertion method from packet, and returns a new packet with the data 
                return packet, addr 
            return None, None
        except socket.timeout:
            #re-raises the timeout exception
            raise
        except BlockingIOError:
            # This will be raised when using non-blocking sockets and no data is available
            return None, None
        except Exception as e:
            print(f"Error receiving packet: {e}")
            return None, None
        
    def close_socket(self):
        """
        This method closes the socket after a connection
        It checks if the socket exists and is inizialised 
        Sets connection to false to indicate no connection. 
        it make shure the socket is accually closed by set it to None
        """    
        if hasattr(self, 'socket') and self.socket:
            try:
                # Set connected to False to indicate we're no longer connected
                self.connected = False
                
                # Close the socket properly
                self.socket.close()
                self.socket = None
                print("Socket properly closed")
            except Exception as e:
                print(f"Error closing socket: {e}")


                
