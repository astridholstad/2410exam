#main entry point in this appication 
#command line parsing 

import argparse
import sys
import os

def parse_args():
    """
    This method will parse command line arguments 
    Using argparse module
    will return the arguments for the main method to use 
    """
    parser = argparse.ArgumentParser(description="DRTP File Transfer Application")

    #common command line args 
    parser.add_argument('-i', '--ip', type=str, default='127.0.0.1', help='IP address')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port number')

    #command line args for client spesific functionality 
    parser.add_argument('-f', '--file', type=str, help='File you want to transfer')
    parser.add_argument('-w', '--window', type=int, default=3, help='Sliding window size')

    #command line args for server spesific functionality 
    parser.add_argument('-d', '--discard', type=int, help='Sequence number to discard')
    parser.add_argument()


def main():
    """
    Main method for this application 

    """    
    







if __name__ == "__main__":
    main()








