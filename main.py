#!/usr/bin/python
# Main python file that reads the input file and spawns all the threads
# Maybe printing should be handled from here too?
#
# Author: Dave Hoatlin

def spawnCustomers(fileName):
	f = open(filename)
	for line in f:
		values = line.split(' ')
		#here i want to start a thread using values
		#startCust(values[0], values[1])

def spawnBarbers(totalBarbers):
	count = 0
	while (count < totalBarbers):
		#startBarber()
		count += 1

def spawnTimerAndCashier():
	#startTimer
	#startCashier

