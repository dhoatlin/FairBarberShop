#!/usr/bin/python
# Main python file that reads the input file and spawns all the threads
# Maybe printing should be handled from here too?
#
# Author: Dave Hoatlin

import sys, os, signal, threading
from threading import Thread

#semaphores we will need
semaphores = {}

#list of customer pids
customers = []

#lists containing customers. using pop/append for first come first server
waitRoomCusts = []
chairCusts = []

#global dict containing color attributes
textColors = {}

class Customer(Thread):
	arrival = 0
	cutTime = 0
	id = 0
	wakeupSem = 0
	timeKeeper = 0
	def __init__(self, arrival, cutTime, id, timeKeeper):
		Thread.__init__(self)
		self.arrival = arrival
		self.cutTime = cutTime
		self.id = id
		self.wakeupSem = timeKeeper.wakeup(int(arrival))
		
		#tell the timeKeeper when to wake this customer
		
		
	def run(self):
		global semaphores, waitRoomCusts, chairCusts
		#print 'running customer:', self.id, 'with arrival time:', self.arrival, 'and cut time:', self.cutTime
		
		#set wakeup time and wait until then
		self.wakeupSem.acquire()
		print 'customer:', self.id, 'woken up'
		#enter barbershop (semaphore for waitroom)
		semaphores['waitingRoom'].acquire()
		waitRoomCusts.append(self)
		print 'customer:', self.id, 'in waiting room'
		
		#wait to be in the front of the line for a waiting room chair
		while True:
			if(waitRoomCusts[0] == self):
				break
		
		#wait for a chair to be available
		semaphores['chair'].acquire()
		semaphores['waitingRoom'].release()
		waitRoomCusts.pop(0)
		chairCusts.append(self)
		print 'customer:', self.id, 'in waiting chair'
		
		
		
		#wait to be next in line
		while True:
			if(chairCusts[0] == self):
				break
			
		#take barber chair
		semaphores['barber'].acquire()
		semaphores['ready'].release()
		semaphores['chair'].release()
		print 'customer:', self.id, 'in barber chair'
		semaphores['finish'][self.id].acquire()
		print 'customer:', self.id, 'left barber chair'
		semaphores['barber'].release()

		#enter chair (semaphore for chairs) signal waitroom semaphore
		#cut hair (semaphore for barbers) signal chair semaphore
		#pay (semaphore for cashier) signal barber semaphore
		#leave barbershop signal cashier semaphore
		
		#print 'customer:', self.id, 'has left'


class TimeKeeper(Thread):
	time = 0
	waitRequests = []
	waitRequestsSem = threading.Semaphore(1)

	def __init__(self):
		Thread.__init__(self)
		signal.signal(signal.SIGALRM, self.handle)
		signal.setitimer(signal.ITIMER_REAL, 1, 1)
		
	def handle(self, signum, _):
		if(signum == 14): #14 is int value of SIGALRM
			self.time += 1
			print self.time
			#if there are requests waiting check incremenet timeElapsed
			if(self.waitRequests):
				self.waitRequestsSem.acquire()
				for request in self.waitRequests:
					request[1] += 1 #increment timeElapsed
					if(request[1] >= request[2]): #if timeElapsed surpases delay
						request[3].release()
						self.waitRequests.pop(0) #remove request
				self.waitRequestsSem.release()

	def run(self):
		while(True):
			a = True
			
	#add a process to the wakeup list and return the unique semaphore
	def wakeup(self, delay):
		waitSem = threading.Semaphore(0)
		timeElapsed = 0
		wakeTime = int(delay) + self.time
		
		#add to request list
		self.waitRequestsSem.acquire()
		self.waitRequests.append([wakeTime, timeElapsed, delay, waitSem])
		self.waitRequests.sort() #sorting by wakeup time
		self.waitRequestsSem.release()
		return waitSem
	
class Barber(Thread):
	timeKeeper = 0
	def __init__(self, timeKeeper):
		Thread.__init__(self)
		self.timeKeeper = timeKeeper
		
	def run(self):
		global semaphores, chairCusts
		while True:
			#wait for a customer to be ready
			semaphores['ready'].acquire()
			cust = chairCusts.pop()
			
			#delay for the duration of the cut
			print 'cutting hair'
			cutSem = self.timeKeeper.wakeup(cust.cutTime)
			cutSem.acquire()
			print 'done cutting hair'
			cutSem.release()
			semaphores['finish'][cust.id].release()
		
		
	
class Cashier(Thread):
	def __init__(self):
		Thread.__init__(self)
	
	def run(self):
		time = 0
		

def spawnCustomers(custData, timeKeeper):
	count = 0
	for customer in custData:
		cust = Customer(customer[0], customer[1], count, timeKeeper)
		cust.start()
		count += 1
	
def spawnBarbers(totalBarbers, timeKeeper):
	count = 0
	while (count < totalBarbers):
		barber = Barber(timeKeeper)
		barber.start()
		count += 1

def startTimer():
	timer = TimeKeeper()
	timer.start()
	return timer
	
def handleCommands(args):
	i = 1 #first arg is file name
	barbers = False
	chairs = False
	waitingRoom = False
	inputFile = False
	while(i < len(args)):
		if(args[i] == '-b'):
			barbers = int(args[i+1])
			i += 2
		elif(args[i] == '-c'):
			chairs = int(args[i+1])
			i += 2
		elif(args[i] == '-w'):
			waitingRoom = int(args[i+1])
			i += 2
		elif(args[i] == '-i'):
			inputFile = args[i+1]
			i += 2
		else:
			print 'command not recognized'
			sys.exit()
	if(barbers == False or chairs == False or waitingRoom == False or inputFile == False):
		print 'must have -b -c -w and -i options set'
		sys.exit()
	return {'barbers':barbers, 'chairs':chairs, 'waitingRoom':waitingRoom, 'inputFile':inputFile}	

def createSemaphores(barbers, chairs, waitingRoom, totalCustomers):
	barberSem = threading.BoundedSemaphore(barbers)
	chairSem = threading.BoundedSemaphore(chairs)
	waitingRoomSem = threading.BoundedSemaphore(waitingRoom)
	readySem = threading.Semaphore(0)
	finishSems = []
	count = 0
	while count < int(totalCustomers):
		finishSems.append(threading.Semaphore(0))
		count += 1
	return {'barber':barberSem, 'chair':chairSem, 'waitingRoom':waitingRoomSem, 'ready':readySem,
			'finish':finishSems}

def parseInput(filename):
	f = open(filename)
	checkFirst = False
	customerData = []
	totalCustomers = 0
	for line in f:
		values = line.split(' ')
		if not checkFirst:
			totalCustomers = values[0][:-1] #[:-1] to ignore newline character
			print 'Total customers: ', totalCustomers 
			checkFirst = True
		else:
			customerData.append((values[0], values[1][:-1]))
	return totalCustomers, customerData

def main():
	global semaphores
	#interpreting command line args
	args = sys.argv
	commands = handleCommands(args)
	
	inputs = parseInput('fairIn.txt')
	
	#creating semaphores
	semaphores = createSemaphores(commands['barbers'], commands['chairs'], commands['waitingRoom'], inputs[0])
	
	timer = startTimer()
	spawnBarbers(int(commands['barbers']), timer)
	
	spawnCustomers(inputs[1], timer)
	
	while True:
		a = True
	
	
if __name__ == '__main__':
	main()
	
		


	

