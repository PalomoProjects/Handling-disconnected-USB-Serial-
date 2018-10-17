#!/usr/bin/env python
#encoding: utf-8 #para acentos 

import thread, os, glob, time

import requests
import json
import urllib2
import unicodedata
import serial


#COMANDOS BOARDROID******************************
CMD_PLUG_PORT = '\xF1\x06\x00\x00\x00\x00\x00\x00\x00\x00\xF2\xF8'

CDM_VEND_MACHINE = '\xF1\x31\x32\x33\x34\x35\x36\x37\x38\x39\xF2\x00'
#************************************************


#*****************FINDING PORT*******************************
#In this function I send a cmd enquiry for detect the correct hardware
def find_port_mdb(PortString):
		array = [ ]
		try:
			sermdb_aux = serial.Serial(PortString, 115200, timeout = 0.1)
			if sermdb_aux.isOpen()==True:	
				sermdb_aux.write(CMD_PLUG_PORT)
				time.sleep(1)
				AUX_String = str(sermdb_aux.read(14).encode('hex'))
				wordLen=len(AUX_String)
				for i in range(0,wordLen/2):
					array.append(AUX_String[i*2] + AUX_String[(i*2)+1])
				if((wordLen/2)>=12):
					if((array[0]=='02')and(array[1]=='06')and(array[12]=='03')and(array[13]=='09')):
						sermdb_aux.close()
						return PortString
				else:
					sermdb_aux.close()
					return 'None'
		except serial.serialutil.SerialException:
			return 'None'
#*****************FINDING PORT*******************************




#*************THIS FUNCTION IS FOR MANAGE THE BOARD RESPONSE*****************************************
def get_data_BoardDroid(strSer1):
	array = [ ]
	wordLed=len(strSer1)
	for i in range(0,wordLed/2):
		array.append(strSer1[i*2] + strSer1[(i*2)+1])
    
	if((wordLed/2)>=14):
		if((array[0]=='02')and(array[1]=='a1')):
    		#Action 1
			return 1
		elif((array[0]=='02')and(array[1]=='b1')):
    		#Action 2
			return 2
#************* END FUNCION*****************************************************************************        




while 1:
	ResultLinkHardware = 'None'

	#this lines is for looking a new ports attached
	while ResultLinkHardware == 'None':
		temp_list = glob.glob ('/dev/ttyUSB*')
		for a_port in temp_list:
			ResultLinkHardware = find_port_mdb(a_port)
	print 'Hardware anclado: ' + ResultLinkHardware

	ser1 = serial.Serial(ResultLinkHardware, 115200)
	RX1= ''
	ser1.isOpen()

	try:
		#this os.stat return the status of the path, is the path /dev/ttyUSB is desconected the exeption is released
		while os.stat(ResultLinkHardware):
			#try:
			data = json.load(urllib2.urlopen('http://192.168.15.7/tiendatest/consult.php?action=sales'))
			if data['estatus'] == 'PENDIENTE':
				print 'Recepción de Venta, Dispensado...'
				
				SelData = int(data['selection'])
				SelData -= 10 
				#print SelData
				checksum = (int('0xC8',16) + SelData + int('0xF2',16)) & int('0xFF',16)
				checksum = hex(checksum).split('x')[1]
				if(len(checksum)==1):
					checksum = '0' + checksum
				#HexSel = hex(SelData)
				HexSel = hex(SelData).split('x')[1]
				if(len(HexSel)==1):
					HexSel = '0' + HexSel

				cmd_aux = 'F1C8' + HexSel + '00' + '00' + '00' + '00' + '00' + '00' + '00' + 'F2' + checksum
				#print str(cmd_aux)
				ser1.write(cmd_aux.decode('hex'))

				FlagDispense = True
				while FlagDispense == True:
					RX1 = str(ser1.read(14).encode('hex'))#MDB
					if(RX1!=''):
						if get_data_BoardDroid(RX1) == 1:
							#Si dispenso
							URLString = "http://url..." + data['idsales']
							data = {'status':   'OK'}
							req = urllib2.Request(URLString,data)
							req.add_header('Content-Type', 'application/json')
							req.get_method = lambda: 'PUT'
							response = urllib2.urlopen(req, json.dumps(data))
							html = response.read()
							print html
						else:
							#No dispenso
							print "The operation fail"
						FlagDispense = False
						RX1=''

				
			elif data['estatus'] == 'VACIO':
				print 'Waiting for ction' 
			#except Exception as e:
			#	print str(e)

			time.sleep(1)	
		
	except OSError as e:
		#In this line we catch the error
		print 'Error the path was disconnect: ' + e.filename
	

	