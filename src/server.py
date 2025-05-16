import os
from drtp_protocol import drtp
from packet import Packet
import datetime
import time
import socket

class Server(drtp):
    """
    This will be used to initialze the reciever with a window size 
    DRTP implementation of the server (the reviecer of the file)
    The server need to handle ip, port, sliding window, file data, discarded sequence numbers. 
    
    """
    def __init__(self, ip, port, window_size=15, discarded_seq=None):
        """
        Constructor for the client with a default window size

        """
        super().__init__(ip, port)
        self.recv_window= window_size
        self.expct_seq_num = 1 #next expected sequence number
        self.buffer = {} #buffer to store out of order data
        self.discarded_seq = discarded_seq
        self.discard_done = False # flag that is T/F to check if discard have been done.

        #bind the socket door to the address
        self.socket.bind((ip, port))

    def wait_for_handshake(self):
        """
        Wait for client to perform a three-way handshake
        """ 
        # Reset state for clean start
        self.connected = False
        self.expct_seq_num = 1
        self.buffer = {}
        self.discard_done = False
        
        # Set a longer timeout for waiting for clients
        original_timeout = self.socket.gettimeout()
        self.socket.settimeout(30.0)  # 30 seconds for initial connection
        
        try:
            while True:
                try:
                    packet, client_addr = self.receive_packet()
                    
                    if packet and client_addr and packet.check_syn():
                        print(f"SYN packet is received from {client_addr}")
                        
                        # Create and send SYN-ACK packet
                        # Use socket directly for more reliability
                        syn_ack = Packet(seq_num=0, ack_num=0, flags=Packet.SYN_flag | Packet.ACK_flag, recv_window=self.recv_window)
                        syn_ack_bytes = syn_ack.convert_to_b()
                        
                        # Send SYN-ACK multiple times to increase reliability
                        for _ in range(3):
                            self.socket.sendto(syn_ack_bytes, client_addr)
                            time.sleep(0.1)  # Brief delay between sends
                        
                        print(f"SYN-ACK is sent to {client_addr}")
                        
                        # Wait for ACK with reasonable timeout
                        self.socket.settimeout(5.0)
                        ack_received = False
                        
                        for attempt in range(5):
                            try:
                                ack_packet, ack_addr = self.receive_packet()
                                
                                if ack_packet and ack_addr and ack_packet.check_ack():
                                    print("ACK packet is received")
                                    print("Connection to client is established")
                                    self.connected = True
                                    self.client_addr = client_addr
                                    ack_received = True
                                    
                                    # Reset timeout to original
                                    self.socket.settimeout(original_timeout)
                                    return client_addr
                            except socket.timeout:
                                print(f"Timeout waiting for ACK (attempt {attempt+1}/5)")
                            except Exception as e:
                                print(f"Error waiting for ACK: {e}")
                        
                        if not ack_received:
                            print("Failed to receive ACK, waiting for new connection...")
                except socket.timeout:
                    print("Timeout waiting for connection, still listening...")
                except Exception as e:
                    print(f"Error in handshake: {e}")
        except KeyboardInterrupt:
            print("Server terminated by user")
        finally:
            # Reset timeout to original
            self.socket.settimeout(original_timeout)
        
        return None                
                    
    def receive_file(self, client_addr, file_name):
        """
        This method recieve a file from the client
        """        
        #check firstly if we have a connection est.
        print("debug:starting revieve file method")
        if not self.connected:
            client_addr = self.wait_for_handshake()
            if not client_addr:
                print("Could not establish connection")
                return
            print("ready to recieve file")
        
        #then we need to prepare time and total bytes, before we recieve any data
        start_time = time.time()
        tot_bytes = 0 #beginning with 0
        
        # Track the last ACK sent to avoid duplicate ACKs
        last_ack_sent = 0
        
        #open file with writing!!!
        print(f"Opening file {file_name} for writing") 
        
        with open(file_name, 'wb') as file:
            print("File opened, waiting for data")
            while self.connected: #while connection is est..
                print("Waiting for packet...")  # Debug
                packet, addr = super().receive_packet()
                print(f"Received packet: {packet}, from {addr}")

                #check for fin packet
                if packet and packet.check_fin():
                    print("FIN packet is recieved")

                    #Send FIN-ACK
                    fin_ack = Packet(flags=Packet.FIN_flag | Packet.ACK_flag)
                    self.send_packet(fin_ack, addr)
                    print("FIN ACK is sent")

                    #calculate throughput and display it
                    used_time = time.time() - start_time
                    throughput = (tot_bytes * 8) / (used_time * 1000000)
                    print(f"The throughput is: {throughput:.2f} Mbps")
                    print("Connection closes")

                    self.connected = False
                    break

                #we have now recieved the data, and now we need to process it
                elif packet:

                    #FOR TESTING PURPOSES: check if we should discard the packet
                    if self.discarded_seq and packet.seq_num == self.discarded_seq and not self.discard_done:
                        print(f"{datetime.datetime.now()} -- Discarding packet: {packet.seq_num} (test)")
                        self.discard_done = True #set flag to true
                        continue

                    #now we prosess the in- order packets
                    if packet.seq_num == self.expct_seq_num % 65536:
                        print(f"{datetime.datetime.now()} -- packet: {packet.seq_num} is recieved")

                        #write data to the file
                        if packet.data:
                            file.write(packet.data)
                            tot_bytes += len(packet.data)

                        #send ack
                        ack = Packet(ack_num=self.expct_seq_num % 65536, flags=Packet.ACK_flag)
                        self.send_packet(ack, addr)
                        print(f"{datetime.datetime.now()} -- sending ack for the recieved {self.expct_seq_num}")
                        
                        # Update the last ACK sent
                        last_ack_sent = self.expct_seq_num % 65536

                        #update the expected sequencenr
                        self.expct_seq_num += 1

                        #check in the buffer for packets
                        while (self.expct_seq_num % 65536) in self.buffer:
                            data = self.buffer.pop(self.expct_seq_num)
                            file.write(data)
                            tot_bytes += len(data)
                            self.expct_seq_num += 1 # and add

                    #out of order packets
                    elif packet.seq_num > self.expct_seq_num % 65536:
                        print(f"{datetime.datetime.now()}  -- Out of order packcet: {packet.seq_num} is received. Expecting: {self.expct_seq_num}")
                        #now buffer the packet
                        self.buffer[packet.seq_num] = packet.data
                        
                        # Only send the ACK if we haven't already sent one for this sequence number
                        if (self.expct_seq_num-1) % 65536 != last_ack_sent:
                            #send duplicate ack for last in order packet
                            ack = Packet(ack_num=(self.expct_seq_num-1) % 65536, flags=Packet.ACK_flag)
                            self.send_packet(ack, addr)
                            print(f"{datetime.datetime.now()} -- sending last ack nr for {self.expct_seq_num-1}")
                            
                            # Update the last ACK sent
                            last_ack_sent = (self.expct_seq_num-1) % 65536
                        else:
                            print(f"{datetime.datetime.now()} -- NOT sending duplicate ACK for {self.expct_seq_num-1} (already sent)")