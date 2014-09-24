# Bethany's Geolocator.

# This code takes a csv, tab-delineated text file, and/or a JSON file, searches for the points on the map (in this case airports),
# and dumps them into a JSON file/map and also a CSV file. It is designed for FAA and NTSB reports, which contain similar information
# and the agencies often track the same type of events (specifically airport ramp incidents), but the information in their reports doesn't 
# merge well. The output of this code allows you to compare apples to apples (for the most part).
# I am working on a program to also merge OSHA data with these files (as OSHA is the third agency that oversees ramp accidents).


from geopy.geocoders import GoogleV3
import time
import csv
import json
# import python-Levenshtein

def createListFromTSV(tsvFile, myDelimiter='\t'):
	'''This function takes a tab-delineated file (tsvFile) and returns a list of dictionaries.'''
	with open(tsvFile,"rU") as f:
		if myDelimiter == '\t':
			fileReader = csv.DictReader(f,delimiter='\t')
		else:
			fileReader = csv.DictReader(f, delimiter=myDelimiter)
#		print type(fileReader)
		fileList = []
		for line in fileReader:
			fileList.append(line)
		return fileList
#		print fileList

# NEXT STEP: separate out writing headers from writing to file, change to append. At some point should combine TSV/CSV functions

def createListFromCSV(csvFile):
	with open(csvFile, "rU") as f:
		fileReader = csv.DictReader(f)
		fileList = []
		for line in fileReader:
			fileList.append(line)
		return fileList

def createDictFromJSON(jsonFile):
	with open(jsonFile,"r") as json_file:
		fileDict = json.loads(json_file.read())
		pythonDict = fileDict['features']
		return pythonDict

def createHeaderList(tsvFile, myDelimiter='\t'):
	'''This function creates a list of headers from a tab-delineated file (tsvfile).'''
	with open(tsvFile,"rU") as myFile:
		lines = myFile.read().split("\n")
		if lines <2:
			lines = myFile.read().split("\r")
		headers = lines[0].split(myDelimiter)
		if headers <2:
			headers = lines[0].split(" | ")
		return headers

def createCSVHeaderList(csvFile):
	with open(csvFile, "rU") as myFile:
		lines = myFile.read().split("\n")
		if lines <2:
			lines = myFile.read().split("\r")
		headers = lines[0].split(",")
		return headers

# def writeHeadersToFile(file, destFile,myDelimiter=','):
#	with open(destFile

def writeDictToCSV(myList, destFile, headers,myDelimiter=','):
	'''This function writes a list of dictionaries to a csvFile.'''
	with open(destFile, "w") as outfile:
		destination = csv.DictWriter(outfile,headers,delimiter=myDelimiter)
		destination.writeheader()
		for thing in myList:
			destination.writerow(thing)

def appendDictToFile(myList, destFile, headers,myDelimiter=','):
	'''This function writes a list of dictionaries to a file - the default is CSV.'''
	with open(destFile, "a") as outfile:
		destination = csv.DictWriter(outfile,headers,delimiter=myDelimiter)
		destination.writeheader()
		for thing in myList:
			destination.writerow(thing)

def findAddressForAirport(**kwargs):
	airportColumnName = kwargs.get('airportColumnName')
	airportLocationColumnName = kwargs.get('airportLocationColumnName')
	fileName = kwargs.get('fileName')
	markerColor = kwargs.get('markerColor','#ffa500') # default color is orange I think.
	myDelimiter = kwargs.get('myDelimiter','\t')
	geolocator = GoogleV3()
	if fileName[-4:]=='.csv':
		fileList = createListFromCSV(fileName)
	elif fileName[-4:]=='.txt':
		fileList = createListFromTSV(fileName,delimiter=myDelimiter)
#		if fileList < 2:
#			print "fileList is: ",fileList
	else:
		print '''File type not recognized. Reformat to CSV 
		and/or tab-delineated file and try again.'''
	airportFatalitiesList = []
	for item in fileList:
		airportName = item.get(airportColumnName)
		if airportName == "Unknown":
			if type(item.get('City')) == str:
				airportName = item.get('City')
		elif 'airport' not in airportName.lower():
			airportName = airportName+" Airport"
		else:
			airportName = airportName
		state = item.get(airportLocationColumnName)
#		print "Airport name and state are: ",airportName, state
		geoQuery = airportName+" in "+state
		print "Searching for",geoQuery
		time.sleep(0.5)
		try:
			address, (latitude, longitude) = geolocator.geocode(geoQuery,exactly_one=True)
		except:
			print "[ERR] FAILED TO GET LOCATION FOR ", airportName
			# NEXT STEP: Add instructions to see if the original NTSB file (or another file/location?) has longitude and latitude info.
# NEXT STEP: Figure out why geocoding stops after 4 records in NTSB files (stops at ANC14FA050)
		else:
			originalAirportName = item.get(airportColumnName)
			if originalAirportName == "Unknown":
				airportName = "Unknown or unnamed airport"
			if type(item.get('Airport Code')) == str:
				airportName = airportName+"("+item.get('Airport Code')+")"
			result = { "type": "Feature", "geometry": {"type":"Point",
			"coordinates":[longitude, latitude] },
			"properties" : { "marker-color":markerColor,
			"marker-symbol":"circle",
			"1. Airport Name":airportName,
			"2. Address":address } }
			airportFatalitiesList.append(result)
			if type(item.get('Gov Agency that tracked')) == str:
				result['properties']['3. Accident Date'] = item.get('Date')
				if item.get('Name(s) of victims') != '':
					result['properties']["4. Victim's name"] = item.get('Name(s) of victims')
				result['properties']['5. Company'] = item.get('Company').encode('utf-8')
				result['properties']['6. Investigated by'] = item.get('Gov Agency that tracked')
				result['properties']['7. Unique ID'] = item.get('Unique ID')
				result['properties']['9. Source URL'] = item.get('URL')
			elif type(item.get('AIDS Report Number')) == str:
				result['properties']['5. AIDS Report Number'] = item.get('AIDS Report Number')
				result["properties"]['3. Accident Date'] = item.get('Local Event Date')
				result["properties"]['4. Operator'] = item.get('Operator')
				result["properties"]['6. Total Fatalities'] = int(item.get('Total Fatalities'))
				result["properties"]['7. Total Injuries'] = int(item.get('Total Injuries'))
				result["properties"]['9. Description'] = item.get('Event Remarks')
				result['properties']['8. Investigation URL'] = item.get('URL')
			elif type(item.get('Accident Number')) == str:
				result["properties"]['6. NTSB Event Id'] = item.get('Event Id')
				result['properties']['5. NTSB Accident Number'] = item.get('Accident Number')
				result['properties']['4. Accident Date'] = item.get('Event Date')
				result['properties']['0. Airport Code'] = item.get('Airport Code')
				result['properties']['7. Total Fatalities'] = int(item.get('Total Fatal Injuries'))
				seriousInjuries = item.get('Total Serious Injuries')
				if seriousInjuries == '':
					seriousInjuries = '0'
				minorInjuries = item.get('Total Minor Injuries')
				if minorInjuries == '':
					minorInjuries = '0'
#				print "seriousInjuries in line 140ish are:",seriousInjuries, "and its type is:",type(seriousInjuries)
#				print "minorInjuries in line 141ish are:", minorInjuries,"and its type is:",type(minorInjuries)
				totalInjuries = int(seriousInjuries) + int(minorInjuries)
				result['properties']['8. Total Injuries'] = totalInjuries
				result['properties']['9. Investigation URL'] = item.get('URL')
				if type(item.get('Description')) == str:
					result['properties']['11. Event Description'] = item.get('Description')
				if type(item.get('NTSB Cause Finding')) == str:
					result['properties']['10. NTSB Cause Finding'] = item.get('NTSB Cause Finding')
			else:
				print '''Check file type - FAA files should have 'AIDS Report Number' column and
NTSB files should have 'Accident Number' column. Other types of files with airport
names included in the file have not been coded yet.'''
	return airportFatalitiesList

def addToMergedList(**kwargs):
	fileName = kwargs.get('fileName')
	geocodingResultList = kwargs.get('geocodingResultList')
	destFile = kwargs.get('destFile')
	myDelimiter = kwargs.get('myDelimiter', ',')
	headers = kwargs.get('headers')
	airportList = createListFromCSV('airportCodes.csv')
	if fileName[-4:] == '.csv':
		originalFileList = createListFromCSV(fileName)
		originalFileHeadersList = createCSVHeaderList(fileName)
	elif fileName[-4:] == '.txt':
		originalFileList = createListFromTSV(fileName)
		originalFileHeadersList = createHeaderList(fileName)
	else:
		print """I'm sorry, this file type is not supported.
Please put information into either a CSV or a tab-delineated text file and try again."""	
	newFileList = []
	if "Aircraft Registration Nbr" in originalFileHeadersList:
		# then you know it must be an FAA file.
		geocodingResultDict = {}
		for item in geocodingResultList:
			uniqueID = item['properties']['5. AIDS Report Number']
			print "FAA unique ID in line 173ish is: ", uniqueID
			geocodingResultDict[uniqueID] = item
#		print "FAA geocodingResultDict in line 175ish is: ", geocodingResultDict
		for record in originalFileList:
			recordDict = {}
			recordDict['FAA AIDS Report Number'] = record.get('AIDS Report Number')
			recordDict['Event Date'] = record.get('Local Event Date')
			recordDict['Airport Name'] = record.get('Event Airport')
#add code to find the airport code
			recordDict['Event City'] = record.get('Event City')
			recordDict['Event State'] = record.get('Event State')
			recordDict['Air Carrier'] = record.get('Operator')
			recordDict['Aircraft Registration Number'] = record.get('Aircraft Registration Nbr')
			recordDict['Accident Description'] = record.get('Event Remarks')
			recordDict['Total Fatalities'] = record.get('Total Fatalities')
			recordDict['Total Injuries'] = record.get('Total Injuries')
			recordDict['Aircraft Damage'] = record.get('Aircraft damage')
			recordDict['Flight Phase'] = record.get('Flight phase')
			recordDict['Report URL'] = record.get('URL')
			uniqueID = recordDict['FAA AIDS Report Number']
			print "uniqueID in line 193ish is:",uniqueID
			recordCoordinates = geocodingResultDict[uniqueID]['geometry'].get('coordinates')
			recordDict['Latitude'] = recordCoordinates[1]
			recordDict['Longitude'] = recordCoordinates[0]
			recordDict['Airport Address'] = geocodingResultDict[uniqueID]['properties'].get('2. Address')
			newFileList.append(recordDict)
#		print "newFileList in line 198ish is: ", newFileList
		appendDictToFile(newFileList, destFile, headers,myDelimiter)
	elif "Accident Number" in originalFileHeadersList:
		#then you know it's an NTSB file
		geocodingResultDict = {}
		for item in geocodingResultList:
			uniqueID = item['properties']['5. NTSB Accident Number']
			geocodingResultDict[uniqueID] = item
#		print "NTSB geocodingResultDict	in line 215ish is:",geocodingResultDict
		for record in originalFileList:
			recordDict = {}
			recordDict['NTSB Event Id'] = record.get('Event Id')
			recordDict['NTSB Accident Number'] = record.get('Accident Number')
			recordDict['Event Date'] = record.get('Event Date')
			recordDict['Airport Name'] = record.get('Airport Name')
			recordDict['Airport Code'] = record.get('Airport Code')
#			recordDict['Event City'] and recordDict['Event State'] - coding needed to divide Location column
			recordDict['Air Carrier'] = record.get('Air Carrier')
			recordDict['Aircraft Registration Number'] = record.get('Registration Number')
			recordDict['Accident Description'] = record.get('Description')
			recordDict['FAR Description'] = record.get('FAR Description')
			recordDict['Total Fatalities'] = record.get('Total Fatal Injuries')
			minorInjuries = record.get('Total Minor Injuries')
			if minorInjuries == '':
				minorInjuries = '0'
			seriousInjuries = record.get('Total Serious Injuries')
			if seriousInjuries == '':
				seriousInjuries = '0'
			totalInjuries = int(minorInjuries) + int(seriousInjuries)
#			print "Total injuries in line 237ish are: ",totalInjuries
			recordDict['Total Injuries'] = totalInjuries
			recordDict['Aircraft Damage'] = record.get('Aircraft Damage')
			recordDict['Flight Phase'] = record.get('Broad Phase of Flight')
			recordDict['Report URL'] = record.get('URL')
			uniqueID = record.get('Accident Number')
			try:
				recordDict['Airport Address'] = geocodingResultDict[uniqueID]['properties'].get('2. Address')
				recordCoordinates = geocodingResultDict[uniqueID]['geometry'].get('coordinates')
				recordDict['Longitude'] = recordCoordinates[0]
				recordDict['Latitude'] = recordCoordinates[1]
			except KeyError:
				print "Geocoding result for",uniqueID,"in line 249ish didn't work."
			newFileList.append(recordDict)
		appendDictToFile(newFileList, destFile, headers,myDelimiter)
	elif "Event Keyword" in originalFileHeadersList:
		# then you know it's an OSHA file
		# NEXT STEP: still have to code geolocating part for OSHA

	else:
		print "Still haven't coded for that yet (line 221ish)"
	
			
FAATestKwargsDict = { 'airportColumnName' : 'Event Airport',
'airportLocationColumnName' : 'Event State',
'fileName' : 'FAA_test.csv','markerColor' : "#ffff00" }

NTSBTestKwargsDict = { 'airportColumnName' : 'Airport Name',
'airportLocationColumnName' : 'Location',
'fileName' : 'NTSB_map_test.csv','markerColor' : "#ffa500" }

deathsKwargsList = { 'airportColumnName': 'Airport Name', 
'airportLocationColumnName': 'State', 
'fileName': 'airportRampFatalities.csv',
'markerColor': '#ff0000'}

mergedAirportFatalitiesListHeaders = ['FAA AIDS Report Number','NTSB Event Id','NTSB Accident Number',
'OSHA Inspection Id','OSHA Accident Id','Event Date','Report Opening Date','Airport Name', 'Airport Code',
'Airport Address', 'OSHA Address','Event City','Event State','Latitude','Longitude',
'Employer','Air Carrier','Inspection Type','Union Status','FAR Description','Aircraft Registration Number','Accident Description',
'NAICS','SIC','Total Fatalities','Total Injuries','Aircraft Damage','Flight Phase','Report URL']

# FAATestList = findAddressForAirport(**FAATestKwargsDict)

# addMergedFAATestKwargsDict = { 'fileName' : 'FAA_ramp_test_dest_file.csv',
# 'destFile' : 'mergedFileTest.csv', 'geocodingResultList' : FAATestList,
# 'headers' : mergedAirportFatalitiesListHeaders }

# addToMergedList(**addMergedFAATestKwargsDict)

NTSBTestList = findAddressForAirport(**NTSBTestKwargsDict)
addMergedNTSBTestKwargsDict = {'fileName' : 'NTSBTestResult3.csv',
'destFile' : 'mergedFileTest.csv', 'geocodingResultList' : NTSBTestList,
'headers' : mergedAirportFatalitiesListHeaders}

addToMergedList(**addMergedNTSBTestKwargsDict)

# airportFatalitiesList.append(findAddressForAirport(**NTSBTestKwargsDict))
# geo = { "type":"FeatureCollection", "features":airportFatalitiesList}
# with open("airportsList.json","w") as json_file:
# 	json_file.write(json.dumps(geo,indent=4,sort_keys=True))

# airportHeaders = airportFatalitiesList['properties'].iterkeys()
# writeDictToCSV(airportFatalitiesList, fatality_list.csv, airportHeaders)

