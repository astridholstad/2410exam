import struct

class Packet:
    #this class is representing a DRTP packet

    """
    Set the flag constants for this class
    These bit patters all is binary notation, therefore it is "0b" in front of the constants.
    I have chosen to do it this way, because it give me a clearer representation of when a flag
    is set and not. For instance 0010 mean the syn flag is set, and 0011 mean 
    the syn and ack flag is set. 
    Help from claude.ai
    """
    SYN_flag = 0b0010 #2 
    ACK_flag = 0b0001 #1
    FIN_flag = 0b0100 #4
    RESET_flag = 0b0000 #0, never used

    def __init__(self, seq_num=0, ack_num=0, flags= 0, recv_window=0, data=b''): 
        """
        This method is a constuctor. Help from safiquls github repo.
        this is a packet with the needed headers and data. 
        """
        self.seq_num = seq_num 
        self.ack_num = ack_num
        self.flags = flags 
        self.recv_window = recv_window
        self.data = data 

    def check_syn(self):
        """
        This method is checking if SYN flag is set. 
        Returns flags and syn flag if bool is true.
        (each of the check-methods uses &, which check if the specific bits are set in the flag)
        """
        return bool(self.flags & self.SYN_flag)
    
    def check_ack(self):
        """
        This method is checking if ACK flag is set. 
        Returns flags and ack flag if bool is true.
        """
        return bool(self.flags & self.ACK_flag)
    
    def check_fin(self):
        """
        This method is checking if FIN flag is set. 
        Returns flags and FIN flag if bool is true.

        """
        return bool(self.flags & self.FIN_flag)
    
    def convert_to_b(self):
        """
        This method will convert packet to bytes for transmission.
        I am using the imported libary struct to do so.
        The method returns a header packed as (2) bytes using struct
        
        """
        seq_num = self.seq_num & 0xFFFF
        ack_num = self.ack_num & 0xFFFF

        header = struct.pack('!HHHH', self.seq_num, self.ack_num, self.flags, self.recv_window)
        #!HHHH means big-endian unsigned short, 16, bit integer.
        return header + self.data
    
    @classmethod
    def convert_from_b(cls, packet_bytes):
        """
        this class method create a packet object from the received bytes. 
        It is bound to the class and not the instance of the class. 
        It unpacks the header if there are any data.
        It also include error handling when recieving a header
        'Cls' refers to the class itself, and therefore it is allowed to create a new instance of the class.  
        It returns a new packet object
        """
        try:
            if len(packet_bytes) < 8:
                #8 is minimum size of revieved header
                print("Packet is too small to contain header")
                return None
            #unpack the header
            header = struct.unpack('!HHHH', packet_bytes[:8])
            #the 'struct.unpack function' unpacks the packet_bytes according to !HHHH. 
            #the struct.unpack function allways returns a tuple, which is similar to lists but elements are unchangeable. 
            #the header must allways match the bit size of 8. 
            seq_num, ack_num, flags, recv_window = header

            data = packet_bytes[8:] if len(packet_bytes) > 8 else b''
            #data is extraced if there are any 
            return cls(seq_num, ack_num, flags, recv_window, data)
        except Exception as e:
            print(f"Error converting bytes to packet: {e}")
            return None


        





        



        