import vote_crypto
import socket
import secrets
import datetime
from _thread import *
from tabulate import tabulate
import atexit
import sys
import random
import time


past_voters = {}		# key = voter id; value = [candidate, token, timestamp]
randomized_voters = {}		# randomizes voter order 
random_tokens = {		# random_tokens assigned to voters, updated every election cycle
	"01":"abc123",
	"02":"xyz789"
}
visitors = 0 			# Keeps track of number of unique voters
candidates = {			# Keeps track of vote tallies for the candidates
	"Alfred Ainsworth": 0,
	"Boris Billingham": 0,
	"Charlie Cadwallader": 0
}
registry = {			# Voter 
	'01' : vote_crypto.client1['public_key'],
	'02' : vote_crypto.client2['public_key'],
}

def format_results(candidates):		# Format and output results in terminal and in a file named 'results.txt' after all votes have been collected
	# Randomly shuffle votes
	keys = list(past_voters.keys())	
	random.shuffle(keys)
	random_vote = []

	f = open('results.txt','w')

	for key in keys:
		k = str(past_voters[key][0])
		random_vote.append([k])
		randomized_voters[key] = past_voters[key]

	votes = tabulate(random_vote, headers=[' * * * Votes * * *'], tablefmt='orgtbl')
	f.write(votes)
	print (votes) 					# print votes in random order

	# Print final tally of the election
	c = []
	for i in candidates:
		k = [i, candidates[i]]
		c.append(k)

	x = "\n\n\n *RESULTS OF THE 2020 ELECTION* \n\n"
	y = tabulate(c, headers=['CANDIDATE', 'VOTES'], tablefmt='orgtbl')
	f.write(x)
	f.write(y)
	print(x)
	print (y)

	f.close()




def receive(message):				# Decrypt and check authorization of recieved vote
	cipher = vote_crypto.decode(message)
	ciphertext = cipher[0]
	signature = cipher[1]
	
	(voter_id, candidate, token) = vote_crypto.decrypt(vote_crypto.server['private_key'], ciphertext)
	(verified, ciphertext) = vote_crypto.verify(registry[voter_id], ciphertext, signature)

	if not verified:
		raise Exception('Invalid signature, vote not authenticated')
		return (0, 0, 0)

	return (voter_id, candidate, token)

def voted_before(voter_id, token):			# Returns true if voter has already cast a vote in this election, else returns false
	if (voter_id in past_voters) and (token == past_voters[voter_id][1]):
		return True
	else:
		return False

def validate_candidate(candidate):		# Returns true if candidate is on list of candidates, else returns false
	if candidate in candidates:
		return True
	else:
		return False

def clientthread(conn):					# New thread for each client
	global visitors
	global past_voters

	# Send welcome message to client
	announcement = "Welcome to the 2020 Election!\nAlfred Ainsworth\nBoris Billingham\nCharlie Cadwallader"
	conn.send(announcement.encode())
	
	# Recieve message from client and decrypt and authorize it
	ciphertext=conn.recv(100000)
	(rec_voter_id, rec_candidate, rec_token) = receive(ciphertext.decode())
	voter_info = [rec_candidate, rec_token, datetime.datetime.now()]

	if (rec_voter_id == 0) and (rec_candidate == 0) and (rec_token == 0):	# If vote is not authenticated
		status = "\nUnauthenticated vote.\n"
		conn.send(status.encode())
		conn.close()
		return False

	if voted_before(rec_voter_id, rec_token):				# If voter has already voted before in this election
		status = "\nYou have already cast a ballot.\n"
		conn.send(status.encode())
		conn.close()
		return False

	if not validate_candidate(rec_candidate):			# If candidate is not among the official candidates
		status = "\nThat is not a valid candidate! Please try again.\n"
		conn.send(status.encode())
		conn.close()
		return False

	if rec_token != random_tokens[rec_voter_id]:		# Check if the received random token matches the one assigned for the voter
		status = "\nCheck your token.\n"
		conn.send(status.encode())
		conn.close()
		return False

	else:
		past_voters.update({rec_voter_id : voter_info})
		visitors += 1
		candidates[rec_candidate] += 1

		status = "\nYour vote has been received. Thanks for voting!\n"
		conn.send(status.encode())
		conn.close()

		if (visitors == 2):						# close connection, server after both votes are in
			format_results(candidates)			# output results
			
			time.sleep(10)						# briefly pause to display tally
			conn.close()

			s.close()
			sys.exit()		


if __name__ == '__main__':
	host = 'localhost'
	port = 50000

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.bind((host,port))
	except:
		sys.exit();

	print("\nCollecting votes...\n\n")
	s.listen(2)

	while 1:
		# Start new thread, program can handle mulitple clients simutaneously
		if visitors == 2:
			s.close()
			break;
		else:
			try:
				conn, addr = s.accept()
				start_new_thread(clientthread, (conn,))
			except:
				s.close()
				sys.exit()