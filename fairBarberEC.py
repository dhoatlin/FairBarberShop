#!/usr/bin/python
'''
Fair barber shop is a program that uses semaphores to manage several different
threads. Incoming customers wait for a barber to cut their hair and then leave
after completion.

AUTHOR: Dave Hoatlin
DATE: 3.31.11

'''

import sys, os, signal, threading, time
from threading import Thread

#semaphores we will need
semaphores = {}

#lists containing customers. using pop/append for first come first server
barberCusts = []
payCusts = []

#global dict containing color attributes
textColors = {'blue':'\033[1;34m', 'green':'\033[1;32m', 'yellow':'\033[1;33m',
			  'red':'\033[1;31m', 'reset':'\033[0m'}

'''
Customer is an object that runs in its own thread. It will wait until its
designated arrival time. from there it will wait for a barber to be ready and
then leave after paying the cashier
'''
class Customer(Thread):
	#some object specific globals
	arrival = 0
	cutTime = 0
	id = 0
	wakeupSem = 0
	timeKeeper = 0
	
	#initialize the customer object
	def __init__(self, arrival, cutTime, id, timeKeeper):
		Thread.__init__(self)
		self.arrival = arrival
		self.cutTime = cutTime
		self.timeKeeper = timeKeeper
		self.id = id
		self.wakeupSem = timeKeeper.wakeup(int(arrival))
		
	'''
	| customer procedure as defined by Hilzer
	|
	| This will begin when the thread is started
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
		self.wakeupSem.acquire()
		string = str(self.timeKeeper.time - 1) + ': customer: ' + str(self.id) + ' arrives'
		syncPrint('green', string)
		
		#enter barbershop (semaphore for waitroom)
		semaphores['waitingRoom'].acquire()
		string = str(self.timeKeeper.time - 1) + ': customer: ' + str(self.id) + ' enters the barbershop'
		syncPrint('green', string)
		
		#wait for a chair to be available
		semaphores['chair'].acquire()
		semaphores['waitingRoom'].release()
		string = str(self.timeKeeper.time - 1) + ': customer: ' + str(self.id) + ' sits in the waiting room'
		syncPrint('green', string)
		
		#take barber chair
		semaphores['barber'].acquire()
		semaphores['chair'].release()
		string = str(self.timeKeeper.time - 1) + ': customer: ' + str(self.id) + ' in barber chair'
		syncPrint('green', string)
		
		#place in barber queue
		semaphores['queue1'].acquire()
		barberCusts.append(self)
		semaphores['ready'].release()
		semaphores['queue1'].release()
		
		#wait for haircut to finish
		semaphores['finish'][self.id].acquire()
		semaphores['leftBarber'][self.id].release()
		string = str(self.timeKeeper.time - 1) + ': customer: ' + str(self.id) + ' left barber chair'
		syncPrint('green', string)

		#pay before leaving
		semaphores['queue2'].acquire()
		payCusts.append(self)
		semaphores['cashier'].release()
		semaphores['queue2'].release()
		semaphores['paid'][self.id].acquire()
		
		#leave the building and end the thread
		string = str(self.timeKeeper.time - 1) + ': customer: ' + str(self.id) + ' has left the building'
		syncPrint('green', string)
		

'''
Timekeeper is an object that runs in its own thread. It sets up an interval
timer that sends a signal every second. TimeKeeper stores its own time value
and increments it whenever SIGALRM is handled. It also tracks all the wakeup
requests from the other threads and signals them when the delay time has
expired
'''
class TimeKeeper(Thread):
	
	time = 0
	waitRequests = []
	waitRequestsSem = threading.Semaphore(1)
	waitSems = []

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
						request[3][0].release()
						request[3][1] = False
						self.waitSems[request[3][2]][1] = False #waitSems[index][inUse] = false
						self.waitRequests.remove(request) #remove request
				self.waitRequestsSem.release()

	def run(self):
		while(True):
			continue #run forever
			
	#add a request to the wakeup list and return the unique semaphore
	def wakeup(self, delay):
		timeElapsed = 0
		wakeTime = int(delay) + self.time
		
		#add to request list
		self.waitRequestsSem.acquire()
		foundSem = False
		
		#if waitsSems is not empty
		if(self.waitSems):
			for sem in self.waitSems:
				#if a semaphore is not in use, reuse it
				if not sem[1]:
					self.waitRequests.append([wakeTime, timeElapsed, int(delay), sem])
					sem[1] = True
					foundSem = True
					waitSem = sem[0]
					self.waitRequests.sort() #sorting by wakeup time
					break #found a semaphore, so we can leave
		
		#if no free sems found or waitSems is empty	add a new sem	
		if not foundSem or not self.waitSems:
			self.waitSems.append([threading.Semaphore(0), True, len(self.waitSems) - 1]) #adding [sem, inUse, index]
			self.waitRequests.append([wakeTime, timeElapsed, int(delay), self.waitSems[-1]])
			waitSem = self.waitSems[-1][0]
			self.waitRequests.sort()
			
		self.waitRequestsSem.release()
		return waitSem
'''
| Barber is an object that runs in its own thread. It waits for a customer to be
| ready for a haircut and then cuts it for the specified duration.
|
| barber procedure as defined by Hilzer
|
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
	#object specific globals
	timeKeeper = 0
	id = 0
	
	#initialize the barber
	def __init__(self, timeKeeper, id):
		Thread.__init__(self)
		self.timeKeeper = timeKeeper
		self.id = id
		
	#run the hilzer procedure when the thread starts
	def run(self):
		#file specific globals
		global semaphores, barberCusts
		
		#handle new customers forever
		while True:
			#wait for a customer to be ready
			semaphores['ready'].acquire()
			semaphores['queue1'].acquire()
			cust = barberCusts.pop(0)
			semaphores['queue1'].release()
			
			#cutting hair
			string = str(self.timeKeeper.time - 1) + ': barber: ' + str(self.id) + ' cutting hair'
			syncPrint('yellow', string)
			cutSem = self.timeKeeper.wakeup(cust.cutTime)
			cutSem.acquire()
			string = str(self.timeKeeper.time - 1) + ': barber: ' + str(self.id) + ' done cutting hair'
			syncPrint('yellow', string)
			
			#wait for customer to leave
			semaphores['finish'][cust.id].release()
			semaphores['leftBarber'][cust.id].acquire()
			semaphores['barber'].release()

'''
| Cashier is an object that runs in its own thread. It waits for a customer to
| be ready to pay and handles them in 0 seconds
|
| cashier procedure as defined by Hilzer
|
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
	#object specific globals
	timeKeeper = 0
	id = 0
	
	#initialize cashier
	def __init__(self, timeKeeper, id):
		Thread.__init__(self)
		self.timeKeeper = timeKeeper
		self.id = id
	
	#run the procedure when the thread starts
	def run(self):
		#file specific globals
		global semaphores, payCusts
		
		#handle customers forever
		while True:
			
			#wait for a customer
			semaphores['cashier'].acquire()
			semaphores['queue2'].acquire()
			cust = payCusts.pop(0)
			semaphores['queue2'].release()
			
			#accept payment
			string = str(self.timeKeeper.time - 1) + ': cashier received payment from customer ' + str(cust.id)
			syncPrint('blue', string)
			semaphores['paid'][cust.id].release()

#create all the customer threads
def spawnCustomers(custData, timeKeeper):
	count = 0
	customers = []
	for customer in custData:
		cust = Customer(customer[0], customer[1], count, timeKeeper)
		customers.append(cust)
		
		#start the thread
		cust.start()
		count += 1
	return customers
	
#create all the barber threads
def spawnBarbers(totalBarbers, timeKeeper):
	count = 0
	barbers = []
	while (count < totalBarbers):
		barber = Barber(timeKeeper, count)
		barbers.append(barber)
		
		#daemon value set to true, will terminate when nonDaemon threads are all
		#complete
		barber.setDaemon(True)
		
		#start the thread
		barber.start()
		count += 1
	return barbers

#create all the cashier threads
def spawnCashiers(totalCashiers, timeKeeper):
	count = 0
	cashiers = []
	while(count < totalCashiers):
		cashier = Cashier(timeKeeper, count)
		cashiers.append(cashier)
		
		#daemon value set to true, will terminate when nonDaemon threads are all
		#complete
		cashier.setDaemon(True)
		
		#start the thread
		cashier.start()
		count += 1
	return cashiers

#create the timer thread
def startTimer():
	timer = TimeKeeper()
	
	#daemon value set to true, will terminate when nonDaemon threads are all
	#complete
	timer.setDaemon(True)
	
	#start the thread
	timer.start()
	return timer

#interperate the commands
def handleCommands(args):
	i = 1 #first arg is file name
	barbers = False
	chairs = False
	waitingRoom = False
	inputFile = False
	
	#check every arg passed for the args we want to use
	#exit if command not recognized
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
	
	#check that all commands were received, if not exit
	if(barbers == False or chairs == False or waitingRoom == False or inputFile == False):
		print 'must have -b -c -w and -i options set'
		sys.exit()
		
	#return dictionary of commands
	return {'barbers':barbers, 'chairs':chairs, 'waitingRoom':waitingRoom,
			'inputFile':inputFile}	

#create all the semaphores we will need
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
	
	#unique semaphores for each customer
	while count < int(totalCustomers):
		finishSems.append(threading.Semaphore(0))
		leftBarberSem.append(threading.Semaphore(0))
		paidSem.append(threading.Semaphore(0))
		count += 1
		
	#return a dictionary of all the semaphores
	return {'barber':barberSem, 'chair':chairSem, 'waitingRoom':waitingRoomSem,
			'ready':readySem, 'finish':finishSems, 'print':printSem,
			'queue1':queueSem1, 'queue2':queueSem2, 'leftBarber':leftBarberSem,
			'cashier':cashierSem, 'paid':paidSem, 'remain':custRemainSem}

#parse the input file to grab each customer
def parseInput(filename):
	f = open(filename)
	checkFirst = False
	customerData = []
	totalCustomers = 0
	#for every line in the file
	for line in f:
		#split all the values on this line
		values = line.split(' ')
		
		#if we are on the first line
		if not checkFirst:
			totalCustomers = values[0][:-1] #[:-1] to ignore newline character
			print 'Total customers: ', totalCustomers 
			checkFirst = True
		
		#otherwise grab the customer arrival and cut duration
		else:
			customerData.append((values[0], values[1][:-1]))
	return totalCustomers, customerData

#syncronizes printing and also converts the string to color
def syncPrint(color, text):
	global textColors, semaphores
	semaphores['print'].acquire()
	print textColors[color] + text + textColors['reset']
	semaphores['print'].release()

#main method that runs when program is started
def main():
	#globals specific to the file
	global semaphores, customersRemaining
	
	#interpreting command line args
	args = sys.argv
	commands = handleCommands(args)
	
	#parse input file
	inputs = parseInput(commands['inputFile'])
	
	#creating semaphores
	semaphores = createSemaphores(commands['barbers'], commands['chairs'],
								  commands['waitingRoom'], inputs[0])
	
	syncPrint('red', 'The shop has opened for business.')
	
	#start the threads
	timer = startTimer()
	barbers = barberThreads = spawnBarbers(int(commands['barbers']), timer)
	customers = custThreads = spawnCustomers(inputs[1], timer)
	cashiers = cashierThreads = spawnCashiers(1, timer)

	#wait for customer threads to finish
	while len(custThreads) > 0:
		for thread in custThreads:
			if not thread.isAlive():
				thread.join()
				custThreads.remove(thread) #remove from pool of threads
	
	#remaining threads will terminate on their own because of the daemon feature
	syncPrint('red', 'The shop has closed.')

#run main method if program started from command line
if __name__ == '__main__':
	main()