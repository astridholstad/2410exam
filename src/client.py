import os
from drtp_protocol import drtp
from packet import Packet
import datetime
import socket

class Client(drtp):
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
        self.connected = False

    def establish_connection(self):
        """
        Perform a three-way handshake
        Establish connection
        """
        
            # First: send a syn packet
        syn_packet = Packet(seq_num=0, flags=Packet.SYN_flag)
        self.send_packet(syn_packet, self.server_addr)
        print("SYN packet is sent")

        original_timeout = self.socket.gettimeout()
        

    
        # Wait for SYN-ACK response
        attempts = 0
        max_attempts = 5
        try: 
            while attempts < max_attempts:
                try:
                    packet, addr = self.receive_packet()
                    if packet:
                        print(f"Received packet with flags={packet.flags} from {addr}")
                    
                        if packet and packet.check_syn() and packet.check_ack():
                            print("SYN-ACK packet is received")
                        
                            # Adjust window size based on server's window
                            self.window_size = min(self.max_window_size, packet.recv_window)
                            print(f"Window size adjusted to {self.window_size}")
                        
                            # Send ACK
                            ack_packet = Packet(seq_num=1, ack_num=1, flags=Packet.ACK_flag)
                            self.send_packet(ack_packet, self.server_addr)
                            print("ACK packet is sent")
                            print("Connection is established")
                        
                            self.connected = True
                            self.socket.settimeout(original_timeout)
                            return True
                except socket.timeout:
                    print(f"Timeout waiting for SYN-ACK (attempt {attempts+1}/{max_attempts})")
                except Exception as e:
                    print(f"Exception during handshake: {e}")

                
                # Increment attempts and maybe resend SYN
                attempts += 1
                if attempts < max_attempts:
                    print(f"Retrying handshake (attempt {attempts}/{max_attempts})")
                    self.send_packet(syn_packet, self.server_addr)
        finally:
            # Reset timeout to original
            self.socket.settimeout(original_timeout)        
            
        print("Connection establishment failed after multiple attempts")
        return False



    def send_file(self, filename):
        """
        Send a file using go back n
        """
        if not self.connected:
            success = self.establish_connection()
            if not success:
                print("Failed to establish connection")
                return #only return if not connected
        
        try:
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

            data = file.read(992)
            #firsty, read file in chunks and send


            while data or self.packets_in_flight:
                #wee need to check if the window is full, and if not we send packet
                while data and self.next_seq_number < self.base_seq_number + self.window_size: 
                    #create a new packet, calling packet class, and send next packet
                    packet = Packet(seq_num=self.next_seq_number % 65536, data=data) #using now the next seqnr
                    self.send_packet(packet, self.server_addr) #to the server

                    #while transmission, we need to track packets for in case of retransmission
                    self.packets_in_flight[self.next_seq_number % 65536] = packet #using a 

                    start = self.base_seq_number % 65536
                    end = self.next_seq_number % 65536
            
                    # Create a window list accounting for wrap-around
                    window = []
                    current = start
                    while current != end:
                        window.append(current)
                        current = (current + 1) % 65536
                    window.append(end)  # Add the end value


                    in_flight_seqs = sorted(self.packets_in_flight.keys())    
                    print(f"{datetime.datetime.now()} -- packet with SEQ nr= {self.next_seq_number % 65536} is sent, sliding window now = {in_flight_seqs}")

                    self.next_seq_number += 1

                    

                    # Read next chunk if we have more data to send
                    if len(self.packets_in_flight) < self.window_size:
                        new_data = file.read(992)
                        if new_data:
                            data = new_data
                        else:
                            data = None
                        break

                try:
                    #now we will try to recieve the acks
                    packet, _ = super().receive_packet()
                    if packet and packet.check_ack():
                        ack_num = packet.ack_num
                        self.base_seq_number = packet.ack_num + 1 # updating the acks
                        print(f"{datetime.datetime.now()} - ACK for packet = {ack_num} is now recieved")

                        #we can now remove the acked packets, as they have been sendt
                        for seq_num in list(self.packets_in_flight.keys()):#using iterable 
                            if seq_num <= packet.ack_num:
                                del self.packets_in_flight[seq_num] #delete
                        # Read next chunk if we have space in the window

                        if data is None and self.next_seq_number < self.base_seq_number + self.window_size:
                            new_data = file.read(992)
                            if new_data:
                                data = new_data
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

            # Check if FIN-ACK is received
            attempts = 0
            while attempts < 5:  # Try 5 times
                packet, _ = super().receive_packet()
                if packet and packet.check_fin() and packet.check_ack():
                    print("FIN ACK packet is received")
                    self.connected = False
                    break

                attempts += 1
                if attempts % 2 == 0:
                    # Resend FIN if no response after 2 timeouts
                    self.send_packet(fin_packet, self.server_addr)
                    print("Resending FIN packet")
            print("Connection closing...")    
            















        





