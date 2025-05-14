import os
from drtp_protocol import DRTP
from packet import Packet
import datetime
import time

class Server(DRTP):
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
            packet, client_addr = self.receive_packet()
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
                
    def receive_file(self, out_file):
        """
        This method recieve a file from the client

        """        
        #check firstly if we have a connection est.
        if not self.connected:
            client_addr = self.wait_for_handshake()

        #then we need to prepare time and total bytes, before we recieve any data
        start_time = time.time()
        tot_bytes = 0 #beginning with 0

        #open file with writing!!!
        
        with open(out_file, 'wb') as file:
            while self.connected: #while connection is est..
                packet, addr = self.receive_packet()

                #check for fin packet
                if packet and packet.check_fin():
                    print("FIN packet is recieved")

                    #Send FIN-ACK
                    fin_ack = Packet(flags=Packet.FIN_flag | Packet.ACK_flag)
                    self.send_packet(fin_ack, addr)
                    print("FIN ACK is sent")

                    #calculate throughput and display it
                    used_time = time.time() - start_time
                    throughput = (tot_bytes * 8) / (used_time / 1000000)
                    print(f"The throughput is: {throughput:.2f} Mbps")
                    print("Connection closes")

                    self.connected= False
                    break

                 #we have now recieved the data, and now we need to process it
                elif packet:

                    #FOR TESTING PURPOSES: check if we should discard the packet
                    if self.discarded_seq and packet.seq_num == self.discarded_seq and not self.discard_done:
                        print(f"{datetime.datetime.now()} - Discarding packet: {packet.seq_num} (test)")
                        self.discard_done = True #set flag to true
                        continue

                    #now we prosess the in- order packets
                    if packet.seq_num == self.expct_seq_num:
                        print(f"{datetime.datetime.now()} - packet: {packet.seq_num} is recieved")

                        #write data to the file
                        if packet.data:
                            file.write(packet.data)
                            tot_bytes += len(packet.data)

                        #send ack
                        ack = Packet(ack_num=self.expct_seq_num, flags=Packet.ACK_flag)
                        self.send_packet(ack, addr)
                        print(f"{datetime.datetime.now()} - sending ack for the recieved {self.expct_seq_num}")

                        #update the expected sequencenr
                        self.expct_seq_num += 1

                        #check in the buffer for packets
                        while self.expct_seq_num in self.buffer:
                            data = self.buffer.pop(self.expct_seq_num)
                            file.write(data)
                            tot_bytes += len(data)
                            self.expct_seq_num += 1 # and add

                #out of order packets
                elif packet.seq_num > self.expct_seq_num:
                    print(f"{datetime.datetime.now()}  - Out of order packcet: {packet.seq_num} is received. Expecting: {self.expct_seq_num}")
                     #now buffer the packet
                    self.buffer[packet.seq_num] = packet.data
                    #send duplicate ack for last in order packet
                    ack = Packet(ack_num=self.expct_seq_num-1, flags=Packet.ACK_flag)
                    self.send_packet(ack, addr)
                    print(f"{datetime.datetime.now()} - sending last ack nr for {self.expct_seq_num-1}")







                


    
