#client functionality class. 

import os
from DRTP_protocol import DRTP
from packet import Packet
import datetime



class Client:
    """
    This class handles the sender of the file. 
    I will implement a three way handshake to est. connection. 
    I will implement Go-back-N strsdegy to send the file and the data.
    Lastly, the connection will be closed with a two-way-handshake. 

    """
    def __init__(self, ip, port, window_size=3):
        """ This is the constructor of the client with a window size"""
        super().__init__(ip, port) #using inheritance 
        self.server_addr=(ip, port)
        self.max_window_size = window_size
        self.window_size = window_size #this needs to be adjustable to the client side
        self.base_seq_number = 1 #the starting number of the seqnr to the sliding window
        self.next_seq_number = 1 #the next seqnr to use
        self.packets_in_flight = {} #i have used a dict here, witch will be adjustable

    def establish_connection(self):
        """
        perform a three-way handshake
        Establish connection
        """

        #first: send a syn packet
        syn_packet = Packet(seq_num=0, flags=Packet.SYN_flag)#inherit packet class and use the flags
        self.send_packet(syn_packet,self.server_addr) #the packet concist of the syn and the reciever is the server
        print("SYN packet is sent")

        #now, we need to wait for the corresponding ack 
        while True:
            packet, addr = self.recieve_packet()
            if packet and packet.check_syn() and packet.check_ack(): #this checks if the syn and ack flags are set
                print("SYN packet is sent")

                #now we need to add to the window size, based on the servers window
                self.window_size =min(self.max_window_size, packet.recv_window) #calls from packet

                #now we need to send a acknowledgement
                #make a new ack packet

                ACK_packet = Packet(seq_num=1,ack_num=1, flags=Packet.ACK_flag) #send base (first) ack
                self.send_packet(ACK_packet, self.server_addr) #to the server
                print("ACK is sent")
                print("Connection is establised")

                self.connected = True
                break



    def send_file(self, filename):
        """
        Send a file
        Using go back n
        """
        if not self.connected: #checks if we are connected to the server, or else estabish the connection
            self.establish_connection()
        
        try:
            file_size= os.path.getsize(filename)
            with open(filename, 'rb') as file:
                self.send_data(file)

        except FileNotFoundError:
            print(f"File {filename} not found")
            return
        

        

        





