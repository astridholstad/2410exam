import os
from drtp_protocol import DRTP
from packet import Packet
import datetime

class Client(DRTP):
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
            packet, addr = self.receive_packet()
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
    
    def send_data(self, file):
        """
        Here i will implement go back n stradegy for sending the data 

        """    
        print("data transfer:")
         #firsty, read file in chunks and send
        while True:
            #wee need to check if the window is full, and if not we send packet
            while self.next_seq_number < self.base_seq_number + self.window_size:
                data = file.read(992) #992 bytes per packet we send
                if not data:
                    break #end of file....
                #create a new packet, calling packet class, and send next packet
                packet = Packet(seq_num=self.next_seq_number, data=data) #using now the next seqnr
                self.send_packet(Packet, self.server_addr) #to the server

                #while transmission, we need to track packets for in case of retransmission
                self.packets_in_flight[self.next_seq_number] = packet #using a list 

                window = list(range(self.base_seq_number, min(self.base_seq_number + self.window_size, + self.next_seq_number + 1))) 
                #list of the window, with a range from what it is to the minimum
                print(f"{datetime.datetime.now()} - packet with SEQ nr= {self.next_seq_number} is sent, sliding window now = {window}")
                #printing the status now as we go

                #update seqnr also
                self.next_seq_number += 1

            try:
                #now we will try to recieve the acks
                packet, _ = self.receive_packet()
                if packet and packet.check_ack():
                    self.base_seq_number = packet.ack_num + 1 # updating the acks
                    print(f"{datetime.datetime.now()} - ACK for packet = {packet.ack_num} is now recieved")

                    #we can now remove the acked packets, as they have been sendt
                    for _seq in list(self.packets_in_flight.keys()):#using iterable 
                        if _seq <= packet.ack_num:
                            del self.packets_in_flight[_seq] #delete
            except socket.timeout:
                #we now need to handle timeout
                #this will re-transmit all of the packets, if occured
                print(f"{datetime.datetime.now()} - TIMEOUT. Retransmitting window")

                for seq_num in range(self.base_seq_number, self.next_seq_number):
                    if seq_num in self.packets_in_flight:
                        self.send_packet(self.packets_in_flight[seq_num], self.server_addr)
                        print(f"{datetime.datetime.now()} - Restransmitting packet : {seq_num}")

             #checking if data transfer is complete
            if not data and not self.packets_in_flight: #is there any data in flight?
                break

        print("Data transmission finished")
        self.teardown_connection()
    
    def teardown_connection(self):
        """
        Here i will implement a two way handshake
        this will close the connection

        """
        print("Connection teardown: ")
        #send a FIN packet
        fin_packet = Packet(flags=Packet.FIN_flag)
        self.send_packet(fin_packet, self.server_addr)
        print("FIN is sent")

        #Check if FIN-ACK is recv

        while True:
            packet, _ = self.receive_packet()
            if packet and packet.check_fin() and packet.check_ack():
                print("FIN ACK is received")
                self.connected = False
                break
        print("Connection closing...")    
        















        





