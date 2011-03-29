#!/usr/bin/python
# Main python file that reads the input file and spawns all the threads
# Maybe printing should be handled from here too?
#
# Author: Dave Hoatlin

import sys, os, signal, threading

class Customer:
	arrival = 0
	cutTime = 0
	id = 0
	def __init__(self, arrival, cutTime, id):
		self.arrival = arrival
		self.cutTime = cutTime
		self.id = id
		
	def run(self):
		print 'running customer:', self.id, 'with arrival time:', self.arrival, 'and cut time:', self.cutTime
		#enter barbershop (semaphore for waitroom) 
		#enter chair (semaphore for chairs) signal waitroom semaphore
		#cut hair (semaphore for barbers) signal chair semaphore
		#pay (semaphore for cashier) signal barber semaphore
		#leave barbershop signal cashier semaphore
		print 'customer:', self.id, 'has left'
		
class TimeKeeper:
	time = 0
	
	def handle(self, signum, _):
		print signum
		if(signum == 14): #14 is int value of SIGALRM
			self.time += 1
			print self.time
	def __init__(self):
		signal.signal(signal.SIGALRM, self.handle)
		signal.setitimer(signal.ITIMER_REAL, 1, 1)
		
	def run(self):
		while(True):
			a = True
	
class Barber:
	def __init__(self):
		print 'barber created'
		
	def run(self):
		time = 0
		#wait for chair to be occupied(semaphore for chairs)
		
	
class Cashier:
	def run(self):
		time = 0

def spawnCustomers(fileName):
	f = open(fileName)
	checkFirst = False
	count = 0
	for line in f:
		values = line.split(' ')
		if not checkFirst:
			totalCustomers = values[0]
			print 'Total customers: ', values[0][:-1] #[:-1] to ignore newline character
			checkFirst = True
		else:
			pid = os.fork()
			if(pid == 0):
				cust = Customer(values[0], values[1][:-1], count)
				cust.run()
				exit()
			count += 1
		#here i want to start a thread using values
		#startCust(values[0], values[1])

def spawnBarbers(totalBarbers):
	count = 0
	while (count < totalBarbers):
		pid = os.fork()
		if(pid == 0):
			barber = Barber()
			barber.run()
			exit()
		count += 1

def startTimer():
	pid = os.fork()
	if(pid == 0):
		timer = TimeKeeper()
		timer.run()
		exit()
	else:
		print 'timer created'
	
def handleCommands(args):
	i = 1 #first arg is file name
	barbers = False
	chairs = False
	waitingRoom = False
	inputFile = False
	while(i < len(args)):
		if(args[i] == '-b'):
			barbers = int(args[i+1])
			print 'barbers set'
			i += 2
		elif(args[i] == '-c'):
			chairs = int(args[i+1])
			print 'chairs set'
			i += 2
		elif(args[i] == '-w'):
			print 'waiting room set'
			waitingRoom = int(args[i+1])
			i += 2
		elif(args[i] == '-i'):
			print 'input file recieved'
			inputFile = args[i+1]
			i += 2
		else:
			print 'command not recognized'
			sys.exit()
	if(barbers == False or chairs == False or waitingRoom == False or inputFile == False):
		print 'must have -b -c -w and -i options set'
		sys.exit()
	return {'barbers':barbers, 'chairs':chairs, 'waitingRoom':waitingRoom, 'inputFile':inputFile}	

def createSemaphores(barbers, chairs, waitingRoom):
	barberSem = threading.BoundedSemaphore(barbers)
	chairSem = threading.BoundedSemaphore(chairs)
	waitingRoomSem = threading.BoundedSemaphore(waitingRoom)
	return {'barber':barberSem, 'chair':chairSem, 'waitingRoom':waitingRoomSem}

def main():
	#interpreting command line args
	args = sys.argv
	commands = handleCommands(args)
	
	#creating semaphores
	semaphores = createSemaphores(commands['barbers'], commands['chairs'], commands['waitingRoom'])
	
	print 'making', commands['barbers'], 'barbers'
	print 'making', commands['chairs'], 'chairs'
	print 'making waiting room with size', commands['waitingRoom']
	
	spawnBarbers(int(commands['barbers']))
	#spawnCustomers('fairIn.txt')
	#startTimer()
	while True:
		a = True
	
	
if __name__ == '__main__':
	main()
	

