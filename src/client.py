import os
from drtp_protocol import drtp
from packet import Packet
import datetime
import socket
import time


class Client(drtp):
    """
    This class handles the sender of the file. 
    I will implement a three way handshake to est. connection. 
    I will implement Go-back-N strsdegy to send the file and the data.
    Lastly, the connection will be closed with a two-way-handshake. 

    """
    def __init__(self, ip, port, window_size=3): #3 is default 
        """ This is the constructor of the client with a window size"""
        super().__init__(ip, port) #using inheritance 
        self.server_addr=(ip, port)
        self.max_window_size = window_size
        self.window_size = window_size #this needs to be adjustable to the server side
        self.base_seq_number = 1 #the starting number of the seqnr to the sliding window
        self.next_seq_number = 1 #the next seqnr to use
        self.packets_in_flight = {} #i have used a dict here, witch will be adjustable, this is unacknowledged packets
        self.connected = False

    def establish_connection(self):
        """
        Perform a three-way handshake
        Establish connection

        """
        
        # First: send a syn packet to the server
        syn_packet = Packet(seq_num=0, flags=Packet.SYN_flag) #set the flags
        self.send_packet(syn_packet, self.server_addr)
        print("SYN packet is sent")

        original_timeout = self.socket.gettimeout()
        self.socket.settimeout(0.4)  # Set  timeout for initial connection
        
        # Wait for SYN-ACK response
        attempts = 0
        max_attempts = 5
        
        #this is error handling, and the client makes up to 5 attempts to connect 
        try: 
            while attempts < max_attempts: #loop up to 5
                try:
                    packet, addr = self.receive_packet()
                    if packet:
                        print(f"Received packet with flags={packet.flags} from {addr}")
                    
                        if packet and packet.check_syn() and packet.check_ack():
                            print("SYN-ACK packet is received")
                        
                            # Adjust window size based on server's window
                            server_window = packet.recv_window # can never go above 15

                            self.window_size = min(self.max_window_size, server_window)
                            print(f"Window size adjusted to {self.window_size}")
                        
                            # Send ACK
                            ack_packet = Packet(seq_num=1, ack_num=1, flags=Packet.ACK_flag)
                            self.send_packet(ack_packet, self.server_addr)
                            print("ACK packet is sent")
                            print("Connection is established")
                        
                            self.connected = True
                            self.socket.settimeout(original_timeout)
                            return True #if connected
                except socket.timeout:
                    print(f"Timeout waiting for SYN-ACK (attempt {attempts+1}/{max_attempts})")
                except socket.error as e:
                    print(f"Socket error: {e}")
                    # For connection errors like "Connection refused", this makes it immediately 
                    if e.errno in [111, 61, 10061]:  # Various connection refused error codes, Used claude.ai for this error handeling. 
                        print(f"Server at {self.server_addr[0]}:{self.server_addr[1]} actively refused connection")
                        return False
                    
                #increment attempts and resend SYN
                attempts += 1
                if attempts < max_attempts:
                    print(f"Retrying handshake (attempt {attempts}/{max_attempts})") #timeout if server is not responding 
                    self.send_packet(syn_packet, self.server_addr)
                else:
                    print(f"Server at {self.server_addr[0]}:{self.server_addr[1]} is not responding after {max_attempts} attempts")
        finally:
            # Reset timeout to original
            self.socket.settimeout(original_timeout)
            
        print("Connection establishment failed")
        # Ensure we are disconnected
        self.connected = False
        return False 
    
    def send_file(self, filename):
        """
        Check if connection is established, if not, try to do so. 
        Open the file for reding in binary, calls send_data() to transfer the contents

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
        This is the Go-Back-N strategy for sending the data.
        It reads the files in chunks of 992 bytes. 
        the sliding window is maintained based on the window size.
        Tracks the (not acked) packets in flight
        Handles timeout and packet transmission
        """    
        #Read first chunk of data
        data = file.read(992)
        file_position = 992 if data else 0
        total_file_size = os.path.getsize(file.name)
        
        #track if we've reached end of file
        end_of_file_reached = False
        
        #for timeout detection
        last_transmission_time = time.time()
        
        #use blocking mode initially
        self.socket.setblocking(True)
        
        # Main transfer loop
        while data is not None or self.packets_in_flight:
            #if we have data and window space, send packets
            while data and len(self.packets_in_flight) < self.window_size: 
                # Create and send packet
                current_seq = self.next_seq_number % 65536 
                packet = Packet(seq_num=current_seq, data=data)
                self.send_packet(packet, self.server_addr)

                #track for retransmission
                self.packets_in_flight[current_seq] = packet
                
                #Display current window
                in_flight_seqs = sorted(self.packets_in_flight.keys())
                print(f"{datetime.datetime.now()} -- packet with SEQ nr= {current_seq} is sent, sliding window now = {in_flight_seqs}")

                #update transmission time
                last_transmission_time = time.time()
                
                self.next_seq_number += 1 #update next seq number.
                
                #read next chunk
                data = file.read(992)
                if data:
                    file_position += len(data)
                    #print progress every 50 packets, for visualisating 
                    if self.next_seq_number % 50 == 0:
                        print(f"Progress: {file_position}/{total_file_size} bytes ({file_position/total_file_size*100:.1f}%)")
                else:
                    print("Reached end of file. Waiting for all ACKs...")
                    end_of_file_reached = True
            
            # If end of file reached and all packets acknowledged, we're done with transmission
            if end_of_file_reached and not self.packets_in_flight:
                print("All data sent and all packets acknowledged. Transfer complete.") #printing for testing
                break
            
            #Check if timeout should come
            current_time = time.time()
            time_since_last_transmission = current_time - last_transmission_time
            
            if time_since_last_transmission > self.timeout:
                print(f"{datetime.datetime.now()} - TIMEOUT. Retransmitting window")
                
                # Retransmit all packets in the window
                for seq_num in sorted(self.packets_in_flight.keys()):
                    self.send_packet(self.packets_in_flight[seq_num], self.server_addr)
                    print(f"{datetime.datetime.now()} - Retransmitting packet: {seq_num}")
                
                #reset timer
                last_transmission_time = time.time()
            
            # Wait for ACKs with a short timeout to allow frequent timeout checks
            try:
                self.socket.settimeout(0.1)  #use a short timeout
                packet, _ = super().receive_packet()
                
                if packet and packet.check_ack():
                    ack_num = packet.ack_num
                    
                    #Ignore ACK 0 which might be from initialization
                    if ack_num == 0:
                        continue
                        
                    self.base_seq_number = ack_num + 1
                    print(f"{datetime.datetime.now()} - ACK for packet = {ack_num} is now received")

                    #Remove acknowledged packets
                    for seq_num in list(self.packets_in_flight.keys()):
                        if seq_num <= ack_num:
                            del self.packets_in_flight[seq_num]
                    
                    #Reset the timer since we had a successful operation
                    last_transmission_time = time.time()
                    
                    if self.packets_in_flight:
                        print(f"Packets still in flight: {len(self.packets_in_flight)}")
                    else:
                        print("No packets in flight")
                    
                    # If end of file and all packets acknowledged, we're done with transfer
                    if end_of_file_reached and not self.packets_in_flight:
                        print("All packets acknowledged. Transfer complete.")
                        break

            except socket.timeout:
                #is expected with our short timeout therefore pass
                pass
            except socket.error as e:
                if e.errno == 35:  # Resource temporarily unavailable
                    #this is normal with non-blocking sockets, so i print nothing here. Help from claude.ai
                    pass
                else:
                    print(f"Socket error: {e}")

        #Restore blocking mode
        self.socket.setblocking(True)
        print("Data transmission finished")
        self.teardown_connection() #close

    def teardown_connection(self):
            
            """
            Here i will implement a two way handshake
            this will close the connection

            """
            print("Connection teardown: ")
            #send a FIN packet
            fin_packet = Packet(flags=Packet.FIN_flag) #set flags
            self.send_packet(fin_packet, self.server_addr)
            print("FIN is sent")


            # Check if FIN-ACK is received
            attempts = 0
            while attempts < 5:  # Try 5 times, error handling
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
            















        





