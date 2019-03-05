import vote_crypto
import secrets
import socket
import sys
from tabulate import tabulate
import time


# Voter ID
voter_id = '02'
token = 'xyz789'

# Encrypt message to send to server
def prepare_message( voter_id, candidate, token ):

    ciphertext = vote_crypto.encrypt( vote_crypto.server[ 'public_key' ], voter_id, candidate, token )
    signature  = vote_crypto.sign( vote_crypto.client2[ 'private_key' ], ciphertext )
    message    = vote_crypto.encode( ciphertext, signature )

    return message

# Set up connection to election server
try:
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
	print("Failed to connect to election server")
	sys.exit();

host = 'localhost'
port = 50000

try:
	s.connect((host, port))
except ConnectionRefusedError:
	print("\nElection server is not active.")
	sys.exit();

# token=s.recv(10000)

print("\nSuccessfully connected to election server!\n")

# Recieve welcome message from server and format
announcement=s.recv(100000)

welcome = announcement.decode().split('\n')
a = []
for i in range(0, 1):
	a.append([welcome[i]])
print(tabulate(a, tablefmt='fancy_grid'))

c = []
for i in range(1, len(welcome)):
	c.append([welcome[i]])
print (tabulate(c, headers=['  * * *  CANDIDATES  * * * '], tablefmt='orgtbl'))

# Get voter's vote
candidate = input("\nPlease enter the candidate of your choice: ")

# Encrypt voter_id, vote, and random token into message
encrypted_message = prepare_message(voter_id, candidate, token)

# Send encrypted message to election server
s.sendto(encrypted_message.encode(), ('localhost', 50000))

# Print out status from server
# Options: vote successfully submitted, candidate not valid, or voter has already voted before
status=s.recv(100000)
print(status.decode())

# Brief pause for user to see status
time.sleep(5)

# Close socket
s.close()