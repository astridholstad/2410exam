#main entry point in this appication 
#command line parsing 

import argparse
import sys
import os
from .client import Client
from .server import Server

def parse_args():
    """
    This method will parse command line arguments 
    Using argparse module
    will return the arguments for the main method to use 
    """
    parser = argparse.ArgumentParser(description="DRTP File Transfer Application")

    # need to write what mode we want the application to be in. 
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('-s', '--server', action='store_true', help='Run in server mode')
    mode.add_argument('-c', '--client', action='store_true', help='Run in client mode')

    #command line args for client spesific functionality 
    parser.add_argument('-f', '--file', type=str, help='File you want to transfer')
    parser.add_argument('-w', '--window', type=int, default=3, help='Sliding window size')

    #command line args for server spesific functionality 
    parser.add_argument('-d', '--discard', type=int, help='Sequence number to discard (Test)')
    
    #common command line args 
    parser.add_argument('-i', '--ip', type=str, default='127.0.0.1', help='IP address')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port number')

    args = parser.parse_args()

    # need to validate args here 

    if args.client and not args.file:
        parser.error(#Client mode requiers -f for file)
            
    return args       



def main():
    """
    Main method for this application 
    """  
    args = parse_args()

    try:
        if args.server:
        #server mode
            server = Server(args.ip, args.port, discarded_seq=args.discard)
            out_file="file.txt"
            server.recieve_file(out_file)

        elif args.client:
        #client mode
            client = Client(args.ip, args.port, args.window)
            client.send_file(args.file)

            
   except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
         
            

if __name__ == "__main__":
    main()