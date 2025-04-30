#error handling, validation
#parsing
#packet construction
import struct
import 

class Packet:
    """this class is representing a DRTP packet"""

    #set the flag constants
    SYN_flag = 0b0010
    ACK_flag = 0b0001
    FIN_flag = 0b0100

    def __init__(self, seq_num=0, ack_num=0, flags= 0, recv_window=0, data=b''):
        """
        This method is used as a constuctor of the objects of this class.
        this is a packet with the needed headers and data
        the def init method in python is standard for contructors 
        as i am sending in self in the methods below, i am simply reffering to the contructors (pyhton syntax)
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
        This method will convert packet to bytes for transmission over DRTP.
        I am using the imported libary struct to do so.
        The methos returns a header packed using struct 
        
        """
        header = struct.pack('!HHHH', self.seq_num, self.ack_num, self.flags, self.recv_window)
        #the "struct.pack" function returns a byte object containg the values i have sent in..
        #Packed in the format !HHHH where ! represents the network byte order and H is unsigned short for 2 integer which represents 16 bytes. 
        return header + self.data
    
    @classmethod
    def convert_from_b(cls, packet_bytes):
        """
        this class method create a packet object from the reveiced bytes 
        it returns the object by
        It cheks if the packet is allowed 
        """
        if len(packet_bytes) < 8:
            #8 is minimum size of revieved header
            raise ValueError("Pakcet is too small to contain header")
        #unpack the header
        header = struct.unpack('!HHHH', packet_bytes[:8])
        #the 'struct.unpack function' unpacks the packet_bytes according to !HHHH. 
        #the struct.unpack function allways returns a tuple, which is similar to lists but elements are unchangeable. 
        #the header must allways match the byte size of 8. 
        seq_num, ack_num, flags, recv_window = header

        data = packet_bytes[8:] if len(packet_bytes) > 8 else b''
        #data is extraced if there are any 

        return cls(seq_num, ack_num, flags, recv_window, data)


        





        



        