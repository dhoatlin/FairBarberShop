#!/usr/bin/python
# Main python file that reads the input file and spawns all the threads
# Maybe printing should be handled from here too?
#
# Author: Dave Hoatlin

import sys, os, signal, threading, time
from threading import Thread

#semaphores we will need
semaphores = {}

#lists containing customers. using pop/append for first come first server
barberCusts = []
payCusts = []

#global dict containing color attributes
textColors = {'blue':'\033[1;34m', 'green':'\033[1;32m', 'yellow':'\033[1;33m',
			  'reset':'\033[0m'}

#track the number of remaining customers
customersRemaining = 0

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
		self.timeKeeper = timeKeeper
		self.id = id
		#self.wakeupSem = timeKeeper.wakeup(int(arrival))
		
	'''
	| customer procedure as defined by Hilzer
	|
	| var custNum
	| begin
	| wait(max_capacity)
	| enter shop
	| wait(mutex1)
	| count += 1
	| custNum = count
	| signal(mutex1)
	| wait(sofa)
	| sit on sofa
	| wait(barberChair)
	| leave sofa
	| signal(sofa)
	| sit in barberChair
	| wait(mutex2)
	| enqueue1(custNum)
	| signal(custReady)
	| signal(mutex2)
	| wait(finished(custNum))
	| signal(leaveBarberChair[custNum])
	| pay
	| wait(mutex3)
	| enqueue2(custNum)
	| signal(payment)
	| signal(mutex3)
	| wait(receipt(custNum))
	| exit shop
	| signal(max_capacity)
	| end
	'''
	def run(self):
		global semaphores, barberCusts, payCusts, customersRemaining

		#set wakeup time and wait until then
		#self.wakeupSem.acquire()
		time.sleep(int(self.arrival))
		string = str(self.timeKeeper.time) + ': customer: ' + str(self.id) + ' arrives'
		syncPrint('green', string)
		
		#enter barbershop (semaphore for waitroom)
		semaphores['waitingRoom'].acquire()
		string = str(self.timeKeeper.time) + ': customer: ' + str(self.id) + ' enters the barbershop'
		syncPrint('green', string)
		
		#wait for a chair to be available
		semaphores['chair'].acquire()
		semaphores['waitingRoom'].release()
		string = str(self.timeKeeper.time) + ': customer: ' + str(self.id) + ' sits in the waiting room'
		syncPrint('green', string)
		
		#take barber chair
		semaphores['barber'].acquire()
		semaphores['chair'].release()
		string = str(self.timeKeeper.time) + ': customer: ' + str(self.id) + ' in barber chair'
		syncPrint('green', string)
		
		#place in barber queue
		semaphores['queue1'].acquire()
		barberCusts.append(self)
		semaphores['ready'].release()
		semaphores['queue1'].release()
		
		#wait for haircut to finish
		semaphores['finish'][self.id].acquire()
		semaphores['leftBarber'][self.id].release()
		string = str(self.timeKeeper.time) + ': customer: ' + str(self.id) + ' left barber chair'
		syncPrint('green', string)

		#pay before leaving
		semaphores['queue2'].acquire()
		payCusts.append(self)
		semaphores['cashier'].release()
		semaphores['queue2'].release()
		semaphores['paid'][self.id].acquire()
		
		string = str(self.timeKeeper.time) + ': customer: ' + str(self.id) + ' has left the building'
		syncPrint('green', string)
		
		semaphores['remain'].acquire()
		customersRemaining -= 1
		semaphores['remain'].release()
		


class TimeKeeper(Thread):
	global customersRemaining
	
	time = 0
	waitRequests = []
	waitRequestsSem = threading.Semaphore(1)

	def __init__(self):
		Thread.__init__(self)
		signal.signal(signal.SIGALRM, self.handle)
		signal.setitimer(signal.ITIMER_REAL, 1, 1)
		
	def handle(self, signum, _):
		if(signum == signal.SIGALRM):
			self.time += 1
			#if there are requests waiting check incremenet timeElapsed
			if(self.waitRequests):
				self.waitRequestsSem.acquire()
				for request in self.waitRequests:
					request[1] += 1 #increment timeElapsed
					if(request[1] >= request[2]): #if timeElapsed surpases delay
						request[3].release()
						self.waitRequests.remove(request) #remove request
				self.waitRequestsSem.release()

	def run(self):
		while(True):
			if customersRemaining == 0:
				print 'timer leaving'
				break
			#if(customersRemaining == 0):
			#	break
			
	#add a request to the wakeup list and return the unique semaphore
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
'''
| wait(cust_ready)
| wait(mutex2)
| dequeue(b_cust)
| signal(mutex2)
| wait(coord)
| cut hair
| signal(coord)
| signal(finished[b_cust])
| wait(leave_b_chair[b_cust])
| signal(barber_chair)
'''
class Barber(Thread):
	timeKeeper = 0
	id = 0
	def __init__(self, timeKeeper, id):
		Thread.__init__(self)
		self.timeKeeper = timeKeeper
		self.id = id
		
	def run(self):
		global semaphores, barberCusts, customersRemaining
		while True:
			if customersRemaining == 0:
				print 'barber leaving'
				break
			#wait for a customer to be ready
			semaphores['ready'].acquire()
			semaphores['queue1'].acquire()
			cust = barberCusts.pop(0)
			semaphores['queue1'].release()
			
			#cutting hair
			string = str(self.timeKeeper.time) + ': barber: ' + str(self.id) + ' cutting hair'
			syncPrint('yellow', string)
			#cutSem = self.timeKeeper.wakeup(cust.cutTime)
			#cutSem.acquire()
			time.sleep(5)
			string = str(self.timeKeeper.time) + ': barber: ' + str(self.id) + ' done cutting hair'
			syncPrint('yellow', string)
			
			#wait for customer to leave
			semaphores['finish'][cust.id].release()
			semaphores['leftBarber'][cust.id].acquire()
			semaphores['barber'].release()
			
		
'''
| wait(payment)
| wait(mutex3)
| dequeue2(c_cust)
| signal(mutex3)
| wait(coord)
| accept pay
| signal(coord)
| signal(receipt[c_cust])
'''
class Cashier(Thread):
	timeKeeper = 0
	id = 0
	def __init__(self, timeKeeper, id):
		Thread.__init__(self)
		self.timeKeeper = timeKeeper
		self.id = id
	
	def run(self):
		global semaphores, payCusts, customersRemaining
		while True:
			#check if customers are left
			if customersRemaining <= 0:
				print 'cashier leaving'
				break
			#wait for a customer
			semaphores['cashier'].acquire()
			semaphores['queue2'].acquire()
			cust = payCusts.pop(0)
			semaphores['queue2'].release()
			
			#accept payment
			string = str(self.timeKeeper.time) + ': cashier received payment from customer ' + str(cust.id)
			syncPrint('blue', string)
			semaphores['paid'][cust.id].release()
		
		

def spawnCustomers(custData, timeKeeper):
	count = 0
	customers = []
	for customer in custData:
		cust = Customer(customer[0], customer[1], count, timeKeeper)
		customers.append(cust)
		cust.start()
		count += 1
	return customers
	
def spawnBarbers(totalBarbers, timeKeeper):
	count = 0
	barbers = []
	while (count < totalBarbers):
		barber = Barber(timeKeeper, count)
		barbers.append(barber)
		barber.start()
		count += 1
	return barbers

def spawnCashiers(totalCashiers, timeKeeper):
	count = 0
	cashiers = []
	while(count < totalCashiers):
		cashier = Cashier(timeKeeper, count)
		cashiers.append(cashier)
		cashier.start()
		count += 1
	return cashiers

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
	cashierSem = threading.Semaphore(0)
	readySem = threading.Semaphore(0)
	printSem = threading.Semaphore(1)
	queueSem1 = threading.Semaphore(1)
	queueSem2 = threading.Semaphore(1)
	custRemainSem = threading.Semaphore(1)
	finishSems = []
	leftBarberSem = []
	paidSem = []
	count = 0
	while count < int(totalCustomers):
		finishSems.append(threading.Semaphore(0))
		leftBarberSem.append(threading.Semaphore(0))
		paidSem.append(threading.Semaphore(0))
		count += 1
	return {'barber':barberSem, 'chair':chairSem, 'waitingRoom':waitingRoomSem,
			'ready':readySem, 'finish':finishSems, 'print':printSem,
			'queue1':queueSem1, 'queue2':queueSem2, 'leftBarber':leftBarberSem,
			'cashier':cashierSem, 'paid':paidSem, 'remain':custRemainSem}

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

def syncPrint(color, text):
	global textColors, semaphores
	semaphores['print'].acquire()
	print textColors[color] + text + textColors['reset']
	semaphores['print'].release()

def main():
	global semaphores, customersRemaining
	#interpreting command line args
	args = sys.argv
	commands = handleCommands(args)
	
	inputs = parseInput('fairQuick.txt')

	customersRemaining = int(inputs[0])
	
	#creating semaphores
	semaphores = createSemaphores(commands['barbers'], commands['chairs'], commands['waitingRoom'], inputs[0])
	
	timer = startTimer()
	barbers = barberThreads = spawnBarbers(int(commands['barbers']), timer)
	customers = custThreads = spawnCustomers(inputs[1], timer)
	cashiers = cashierThreads = spawnCashiers(1, timer)

	liveThreads = False
	while len(custThreads) > 0:
		for thread in custThreads:
			if not thread.isAlive():
				thread.join()
				custThreads.remove(thread) #remove from pool of threads
				
	print 'waiting for barbers'
	while len(barberThreads) > 0:
		for thread in barberThreads:
			if not thread.isAlive():
				thread.join()
				barberThreads.remove(thread)
			
	
	print 'waiting for cashiers'
	while len(cashierThreads) > 0:
		for thread in cashierThreads:
			if not thread.isAlive():
				thread.join()
				cashierThreads.remove(thread)
	
	print 'waiting for timer'
	timer.join()
if __name__ == '__main__':
	main()
	
		


	

