#!/usr/bin/python
# Main python file that reads the input file and spawns all the threads
# Maybe printing should be handled from here too?
#
# Author: Dave Hoatlin

import sys	

def spawnCustomers(fileName):
	f = open(fileName)
	checkFirst = False
	customerCount = 1
	for line in f:
		values = line.split(' ')
		if not checkFirst:
			totalCustomers = values[0]
			print 'Total customers: ', values[0][:-1] #[:-1] to ignore newline character
			checkFirst = True
		else:
			print 'customer:', customerCount, 'arrival time:', values[0], 'Cut time:', values[1][:-1] #[:-1] to ignore newline character
			customerCount += 1
		#here i want to start a thread using values
		#startCust(values[0], values[1])

def spawnBarbers(totalBarbers):
	count = 0
	while (count < totalBarbers):
		#startBarber()
		count += 1

def spawnTimerAndCashier():
	print 'spawning timer/cashier'
	#startTimer
	#startCashier
	
def main():
	#starting the program
	args = sys.argv 
	i = 1 #first arg is file name
	barbers = False
	chairs = False
	waitingRoom = False
	while(i < len(args)):
		if(args[i] == '-b'):
			barbers = args[i+1]
			print 'barbers set'
			i += 2
		elif(args[i] == '-c'):
			chairs = args[i+1]
			print 'chairs set'
			i += 2
		elif(args[i] == '-w'):
			print 'waiting room set'
			waitingRoom = args[i+1]
			i += 2
		else:
			print 'command not recognized'
			sys.exit()
	if(barbers == False or chairs == False or waitingRoom == False):
		print 'must have -b -c and -w options set'
		sys.exit()
	spawnCustomers('fairIn.txt')
	
	
if __name__ == '__main__':
	main()


