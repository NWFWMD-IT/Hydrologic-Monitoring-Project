################################################################################
# Name:
#	load_hydro_data.py
#
# Purpose:
#	Load asset and configuration data to hydro geodatabase
#
# Environment:
#	ArcGIS Pro 3.1.0
#	Python 3.9.16, with:
#		arcpy 3.1 (build py39_arcgispro_41759)
#
# Notes:
#	Run this script as the Windows user HQ\hydro. The script will create
#	a Windows-authenticated connection to the target geodatabase and load
#	content to tables owned by the [hydro] user.
#
#	Theoretically, any user with write permission on the target tables could
#	perform this load. Because this script is only intended to be run in
#	a controlled environment during initial database deployment, however,
#	we require running as the schema owner, hydro, for simplicity. Any
#	staff or process that performs the deployment workflow will already have
#	the credentials for the Windows HQ\hydro user and, as the schema owner,
#	this user is guaranteed to have permissions to write to the target
#	tables.
#
#
#
#	MESSAGES
#
#	All messaging is processed through the `logging` module, including user
#	feedback, diagnostic messages, and errors. Output to all destinations
#	is UTF-8 encoded.
#
#	In script mode, this module uses the root logger.
#
# History:
#	2022-12-12 MCM Created
#
# To do:
#	none
#
# Copyright 2003-2022. Mannion Geosystems, LLC. http://www.manniongeo.com
################################################################################

#
# Modules
#


# Standard

import arcpy
import argparse
import json
import logging
import os
import sys
import tempfile
import uuid


# Custom

import constants as C
import mg



################################################################################
# Classes
################################################################################


class DataLogger:
	'''
	Data logger
	'''


	########################################################################
	# Class attributes
	########################################################################


	#
	# Public
	#


	# Properties in the target hydro geodatabase data model, to use as
	# instance attributes

	ATTRIBUTES = (
		'Type'
		,'SerialNumber'
		,'Comments'
	)



	########################################################################
	# Instance methods
	########################################################################


	#
	# Public
	#

	def __init__(
		self
		,type_
		,serial_number
	):

		logging.debug(f'Initializing {__class__.__name__}')



		# Store values passed by caller

		self._type = type_
		self._serial_number = serial_number



		# Create attributes for target values

		self._initialize_attributes()



		# Process source data into target values

		self.transform()



	def __str__(self):

		return json.dumps(
			asdict(
				object = self
				,attributes = self.__class__.ATTRIBUTES
			)
			,indent = mg.JSON_INDENT
		)



	def transform(self):

		# Run a transformation function to populate each output
		# attribute

		for f in (
			self.transform_serialnumber
			,self.transform_type
		):

			logging.debug(f'Executing: {f.__name__}')
			f()



	def transform_serialnumber(self):

		if isempty(self._serial_number):
		
			raise ValueError(f'Data Logger: Missing serial number')
			
		
		self.SerialNumber = self._serial_number.strip()



	def transform_type(self):

		if isempty(self._serial_number):
		
			raise ValueError(f'Data Logger: Missing type')
			
		
		self.Type = self._type.strip()



	#
	# Private
	#

	def _initialize_attributes(self):

		for a in self.__class__.ATTRIBUTES:

			setattr(
				self
				,a
				,None
			)



class Location:
	'''
	Hydro monitoring location

	Accepts content from multiple sources, correlates, and
	transforms/validates for use with hydro monitoring geodatabase
	'''


	########################################################################
	# Class attributes
	########################################################################


	#
	# Public
	#


	# Properties in the target hydro geodatabase data model, to use as
	# instance attributes

	ATTRIBUTES = (
		'shape'
		,'NWFID'
		,'Name'
		,'Project'
		,'HasDataLogger'
		,'HasRainfall'
		,'HasStage'
		,'HasGroundwater'
		,'HasConductivity'
		,'HasADVM'
		,'HasADVMBattery'
		,'HasDischarge'
		,'HasTemperature'
		,'HasWaterQuality'
		,'Comments'
	)



	########################################################################
	# Instance methods
	########################################################################


	#
	# Public
	#

	def __init__(
		self
		,data_aq_stations # SourceData instance
		,data_district_monitoring # SourceData instance
	):

		logging.debug(f'Initializing {__class__.__name__}')



		# Store source data values

		self.data_aq_stations = data_aq_stations
		self.data_district_monitoring = data_district_monitoring



		# Create attributes for target values

		self._initialize_attributes()



		# Initialize related objects

		self.data_logger = None
		self.sensors = []



		# Check basic integrity before running transformers

		if self.data_district_monitoring.Monitoring_Type is None:

			raise ValueError(f'District Monitoring: Missing monitoring type')



		# Process source data into target values

		self.transform()



	def __str__(self):


		# Location

		message = json.dumps(
			asdict(
				object = self
				,attributes = self.__class__.ATTRIBUTES
			)
			,indent = mg.JSON_INDENT
		)



		# Data Logger

		if self.data_logger is None:

			message += '\nData Logger: None'

		else:

			message += '\nData Logger:'
			message += f'\n{self.data_logger}'



		# Sensors
		
		if len(self.sensors) == 0:
		
			message += '\nSensors: None'
			
			
		else:
		
			message += '\nSensors:'
			
			for sensor in self.sensors:
			
				message += f'\n{sensor}'



		# Return
		
		return message



	def transform(self):

		# Run a transformation function to populate each output
		# attribute

		for f in (
			# Location properties
			self.transform_hasadvm
			,self.transform_hasadvmbattery
			,self.transform_hasconductivity
			,self.transform_hasdatalogger
			,self.transform_hasdischarge
			,self.transform_hasgroundwater
			,self.transform_hasrainfall
			,self.transform_hasstage
			,self.transform_hastemperature
			,self.transform_haswaterquality
			,self.transform_name
			,self.transform_nwfid
			,self.transform_project
			,self.transform_shape
			# Related data
			,self.transform__datalogger
			,self.transform__sensors
		):

			logging.debug(f'Executing: {f.__name__}')
			f()



	def transform__datalogger(self):
		'''
		Locations may have zero or one Data Loggers. Loggers must have
		both a type and serial number.
		'''

		type_ = self.data_district_monitoring.Type_of_Recorder
		serial_number = self.data_district_monitoring.Recorder_Serial__



		if (
			not isempty(type_)
			and not isempty(serial_number)
		):

			logging.debug('Found Data Logger')
			
			self.data_logger = DataLogger(
				type_ = type_.strip()
				,serial_number = serial_number.strip()
			)


		elif(
			isempty(type_)
			^ isempty(serial_number)
		):

			raise ValueError(
				'District Monitoring: Data Logger must have both type and serial number'
				f'\nType: {mg.none2blank(type_)}'
				f'\nSerial number: {mg.none2blank(serial_number)}'
			)


		else:

			logging.debug('No Data Logger record')



	def transform_hasadvm(self):

		if 'vel.ind' in mg.none2blank(self.data_district_monitoring.Monitoring_Type).lower():

			self.HasADVM = 'Yes'

		else:

			self.HasADVM = 'No'



	def transform_hasadvmbattery(self):

		# This source data is not available yet; set all values to NULL
		# for now

		self.HasADVMBattery = None



	def transform_hasconductivity(self):

		if 'cond' in mg.none2blank(self.data_district_monitoring.Monitoring_Type).lower():

			self.HasConductivity = 'Yes'

		else:

			self.HasConductivity = 'No'



	def transform_hasdatalogger(self):

		if isempty(self.data_district_monitoring.Type_of_Recorder):

			self.HasDataLogger = 'No'

		else:

			self.HasDataLogger = 'Yes'



	def transform_hasdischarge(self):

		if 'discharge' in mg.none2blank(self.data_district_monitoring.Monitoring_Type).lower():

			self.HasDischarge = 'Yes'

		else:

			self.HasDischarge = 'No'



	def transform_hasgroundwater(self):

		if 'gw level' in mg.none2blank(self.data_district_monitoring.Monitoring_Type).lower():

			self.HasGroundwater = 'Yes'

		else:

			self.HasGroundwater = 'No'



	def transform_hasrainfall(self):

		if 'rainfall' in mg.none2blank(self.data_district_monitoring.Monitoring_Type).lower():

			self.HasRainfall = 'Yes'

		else:

			self.HasRainfall = 'No'



	def transform_hasstage(self):

		monitoring_type = mg.none2blank(self.data_district_monitoring.Monitoring_Type).lower()


		if 'd-stage' in monitoring_type: # Discontinued stage type

			self.HasStage = 'No'

		elif 'stage' in monitoring_type: # All instances except 'd-stage'

			self.HasStage = 'Yes'

		else:

			self.HasStage = 'No'



	def transform_hastemperature(self):

		if 'temp' in mg.none2blank(self.data_district_monitoring.Monitoring_Type).lower():

			self.HasTemperature = 'Yes'

		else:

			self.HasTemperature = 'No'



	def transform_haswaterquality(self):

		if 'wq' in mg.none2blank(self.data_district_monitoring.Monitoring_Type).lower():

			self.HasWaterQuality = 'Yes'

		else:

			self.HasWaterQuality = 'No'



	def transform_name(self):

		if not isempty(self.data_district_monitoring.Station_Name):
		
			self.Name = self.data_district_monitoring.Station_Name.strip()



	def transform_nwfid(self):

		if isempty(self.data_aq_stations.LocationIdentifier):
		
			raise ValueError('Aquarius: Missing location identifier')
			
			
		self.NWFID = f'{self.data_aq_stations.LocationIdentifier:>06}'



	def transform_project(self):

		if not isempty(self.data_district_monitoring.Project_Number):
		
			try:
			
				self.Project = int(self.data_district_monitoring.Project_Number)
				
			except Exception as e:
			
				logging.warning(f'Location {self.data_aq_stations.LocationIdentifier}: Failed to process project number: {self.data_district_monitoring.Project_Number}')



	def transform__sensors(self):
		'''
		Locations may have zero or more sensors. Sensors are stored in
		two places in the District Monitoring spreadsheet:
		
			o Tipping bucket
				o Zero or one
				
			o Other sensors
				o Zero or many
				o Multiple sensors are pipe delimited
				
		All sensors must have a type and a serial number
		'''
		
		
		# Tipping bucket

		tb_type = self.data_district_monitoring.Type_of_Tipping_Bucket
		tb_serial_number = self.data_district_monitoring.T_B__Serial__


		if (
			not isempty(tb_type)
			and not isempty(tb_serial_number)
		):

			logging.debug('Found tipping bucket')
			
			self.sensors.append(
				Sensor(
					type_ = tb_type.strip()
					,serial_number = tb_serial_number.strip()
				)
			)


		elif(
			isempty(tb_type)
			^ isempty(tb_serial_number)
		):

			raise ValueError(
				'District Monitoring: Tipping bucket must have both type and serial number'
				f'\nType: {mg.none2blank(tb_type)}'
				f'\nSerial number: {mg.none2blank(tb_serial_number)}'
			)


		else:

			logging.debug('No tipping bucket record')
			
			
			
		# Other sensors
		
		sensor_types = self.data_district_monitoring.Type_of_Sensor
		sensor_serial_numbers = self.data_district_monitoring.Sensor_Serial__


		if (
			not isempty(sensor_types)
			and not isempty(sensor_serial_numbers)
		):
		
			logging.debug('Found sensor records')
			
		
			sensor_type_list = sensor_types.split('|')
			sensor_serial_number_list = sensor_serial_numbers.split('|')
		
			
			if len(sensor_type_list) != len(sensor_serial_number_list):
			
				raise ValueError(
					'District Monitoring: Sensor list must have type and serial number for each sensor'
					f'\nTypes: {mg.none2blank(sensor_types)}'
					f'\nSerial numbers: {mg.none2blank(sensor_serial_numbers)}'
				)
			
			
			for i in range(len(sensor_type_list)):
			
				logging.debug(f'Adding Sensor {i}')
			
				self.sensors.append(
					Sensor(
						type_ = sensor_type_list[i].strip()
						,serial_number = sensor_serial_number_list[i].strip()
					)
				)


		elif(
			isempty(sensor_types)
			^ isempty(sensor_serial_numbers)
		):

			raise ValueError(
				'District Monitoring: Sensor list must have type and serial number for each sensor'
				f'\nTypes: {mg.none2blank(sensor_types)}'
				f'\nSerial numbers: {mg.none2blank(sensor_serial_numbers)}'
			)


		else:
		
			logging.debug('No sensor records')



	def transform_shape(self):
		'''
		Experimenting with different shape formats. Keeping all code for
		reference and commenting out parts that don't currently apply.
		'''

		# PointGeometry
		#
		# self.shape = getattr( # Need to use getattr() because '@' is required by ArcGIS but syntactically disallowed by Python
			# self.data_aq_stations
			# ,'SHAPE@'
		# )



		# Sequence

		self.shape = self.data_aq_stations.Shape



	#
	# Private
	#

	def _initialize_attributes(self):

		for a in self.__class__.ATTRIBUTES:

			setattr(
				self
				,a
				,None
			)



class Metrics:
	'''
	Store and report statistics for data processing progress
	'''


	########################################################################
	# Properties
	########################################################################


	####################
	# Counts
	####################


	#
	# Locations
	#


	# Succeeded

	@property
	def location_succeeded(self):

		return self._location_succeeded


	@location_succeeded.setter
	def location_succeeded(
		self
		,count
	):

		self._location_succeeded = count



	# Failed

	@property
	def location_failed(self):

		return self._location_failed


	@location_failed.setter
	def location_failed(
		self
		,count
	):

		self._location_failed = count



	# Total

	@property
	def location_total(self):

		return self.location_succeeded + self.location_failed



	########################################################################
	# Instance methods
	########################################################################


	#
	# Public
	#

	def __init__(self):

		logging.debug(f'Initializing {__class__.__name__}')


		# Initialize counters

		self.location_succeeded = 0
		self.location_failed = 0



	def __str__(self):

		template_count_header = '\n\t{type:<20s}{total:>12s}{succeeded:>12s}{failed:>12s}'
		template_count        = '\n\t{type:<20s}{total:>12,d}{succeeded:>12,d}{failed:>12,d}'


		message = 'Data Processing Metrics'

		message += template_count_header.format(
			type = ''
			,total = 'Total'
			,succeeded = 'Succeeded'
			,failed = 'Failed'
			,excluded = 'Excluded'
		)

		message += template_count.format(
			type = 'Location'
			,total = self.location_total
			,succeeded = self.location_succeeded
			,failed = self.location_failed
		)



		return message



class Sensor:
	'''
	Sensor
	'''


	########################################################################
	# Class attributes
	########################################################################


	#
	# Public
	#


	# Properties in the target hydro geodatabase data model, to use as
	# instance attributes

	ATTRIBUTES = (
		'Type'
		,'SerialNumber'
		,'Comments'
	)



	########################################################################
	# Instance methods
	########################################################################


	#
	# Public
	#

	def __init__(
		self
		,type_
		,serial_number
	):

		logging.debug(f'Initializing {__class__.__name__}')



		# Store values passed by caller

		self._type = type_
		self._serial_number = serial_number



		# Create attributes for target values

		self._initialize_attributes()



		# Process source data into target values

		self.transform()



	def __str__(self):

		return json.dumps(
			asdict(
				object = self
				,attributes = self.__class__.ATTRIBUTES
			)
			,indent = mg.JSON_INDENT
		)



	def transform(self):

		# Run a transformation function to populate each output
		# attribute

		for f in (
			self.transform_serialnumber
			,self.transform_type
		):

			logging.debug(f'Executing: {f.__name__}')
			f()



	def transform_serialnumber(self):

		if isempty(self._serial_number):
		
			raise ValueError(f'Sensor: Missing serial number')
			
		
		self.SerialNumber = self._serial_number.strip()



	def transform_type(self):

		if isempty(self._type):
		
			raise ValueError(f'Sensor: Missing type')
			
		
		self.Type = self._type.strip()



	#
	# Private
	#

	def _initialize_attributes(self):

		for a in self.__class__.ATTRIBUTES:

			setattr(
				self
				,a
				,None
			)



class SourceData:
	'''
	Collection of source values, accessible by name

	Constructor accepts an arcpy.da.SearchCursor (for column names) and
	a row fetched from that cursor, and sets attributes named from the
	former with values from latter. Attribute names are lower-case.
	Column names must be unique within the cursor. This is not required
	by the underlying database engine or APIs, but rather is necessary in
	order to fetch values unambiguously by column name. A duplicate column
	name raises ValueError.
	'''

	def __init__(
		self
		,cursor
		,row
	):

		logging.debug(f'Initializing {__class__.__name__}')



		self._attributes = []


		for i in range(len(cursor.fields)):

			name = cursor.fields[i]
			value = row[i]


			if name in self._attributes:

				raise ValueError(f'Column name {name} already exists')



			self._attributes.append(name)


			setattr(
				self
				,name
				,value
			)



	def __str__(self):

		return json.dumps(
			asdict(
				object = self
				,attributes = self._attributes
			)
			,indent = mg.JSON_INDENT
		)



################################################################################
# Functions
################################################################################


#
# Public
#


def asdict(
	object
	,attributes
):
	'''
	Convert complex objects to dictionaries with simple types that can be
	encoded as JSON by json module

	This helper function factors out common code from several classes
	defined in this module. It accepts an object and a sequence of attribute
	names, and returns a dict of the attribute names and their values.

	The conversion logic is simple:

		If an attribute value has its own attribute named 'asdict', we
		assume that the value is a complex object that needs additional
		simplification and call value.asdict() to get a dict with simple
		types that are compatible with the json module.

		Otherwise, if the value does not have an attribute named
		'asdict', we assume that it can be encoded directly by the
		json module and add it to the dict without furhter processing.
	'''

	d = {}


	for a in attributes:

		value = getattr(
			object
			,a
		)



		if hasattr( # Complex type
			value
			,'asdict'
		):

			d[a] = value.asdict()


		else: # Simple type

			if isinstance( # Convert datetime to string, for subsequent JSON conversions
				value
				,datetime.datetime
			):

				value = value.strftime(mg.JSON_FORMAT_DATE)


			if isinstance( # Display human-friendly representation of geometry
				value
				,arcpy.Geometry
			):

				value = json.loads(value.JSON)


			d[a] = value



	# Return

	return d



def isempty(
	value
):

	if value is None:
	
		return True
		
		
	elif isinstance(
		value
		,str
	):
	
		if len(value.strip()) == 0:
		
			return True
			
		else:
		
			return False
			
			
	else:
	
		return False



def load_data(
	target_gdb
	,source_aq_stations
	,source_district_monitoring
	,feedback
):
	'''
	Read data from source files and load to target geodatabase
	'''


	#
	# Initialize metrics
	#

	metrics = Metrics()



	#
	# Read District Monitoring source data to memory
	#
	# Performance is prohibitively poor when accessing directly from Excel
	# (at least for this workbook). Cache the relevant worksheet to a table
	# in an in-memory workspace.
	#

	source_district_monitoring_table = os.path.join(
		source_district_monitoring
		,'T_Comprehensive_Monitoring$_' # 'T_' prefix and '_' suffix added for use with geoprocessing tools
	)
	logging.debug(f'District Monitoring source table: {source_district_monitoring_table}')


	table_district_monitoring_memory_name = f't{uuid.uuid4().hex}' # Random table name
	table_district_monitoring_memory = f'memory/{table_district_monitoring_memory_name}'
	logging.debug(f'District Monitoring in-memory table: {table_district_monitoring_memory}')


	logging.info('Loading District Monitoring source data to memory')

	arcpy.conversion.TableToTable(
		in_rows = source_district_monitoring_table
		,out_path = 'memory'
		,out_name = table_district_monitoring_memory_name
	)



	#
	# Process data
	#

	logging.info('Starting Location processing')

	with arcpy.da.SearchCursor( # Main Locations loop
		in_table = source_aq_stations
		,field_names = '*'
		# ,where_clause = 'LocationIdentifier in (8495, 8505, 8544)' # DEBUG
		,spatial_reference = C.SR_UTM16N_NAD83
	) as cursor_aq_stations:


		# Fetch Location

		for row_aq_stations in cursor_aq_stations:

			data_aq_stations = SourceData(
				cursor_aq_stations
				,row_aq_stations
			)
			logging.debug(f'Fetched Aquarius Location {data_aq_stations.LocationIdentifier}')
			logging.datadebug(f'Source data: Aquarius Locations:\n{data_aq_stations}')



			# Fetch related District monitoring data

			logging.debug(f'Fetching related District Monitoring record for Location ID {data_aq_stations.LocationIdentifier}')

			district_monitoring_count = 0


			with arcpy.da.SearchCursor( # District Monitoring record for this Location
				in_table = table_district_monitoring_memory
				,field_names = '*'
				,where_clause = f'Station_ID = {data_aq_stations.LocationIdentifier}'
			) as cursor_district_monitoring:

				logging.debug(f'Created cursor for District Monitoring memory table')

				data_district_monitoring = None


				for row_district_monitoring in cursor_district_monitoring:

					district_monitoring_count += 1

					logging.debug(f'Found matching District Monitoring record for Location ID {data_aq_stations.LocationIdentifier}')

					if district_monitoring_count > 1:

						raise ValueError(f'District Monitoring: Multiple records found for Location ID {data_aq_stations.LocationIdentifier}')


					data_district_monitoring = SourceData(
						cursor_district_monitoring
						,row_district_monitoring
					)
					logging.datadebug(f'Source data: District Monitoring:\n{data_district_monitoring}')



			if data_district_monitoring is None:

				logging.warning(f'Skipping Location ID {data_aq_stations.LocationIdentifier}: District Monitoring: No data found')

				metrics.location_failed += 1


			else:

				try:

					location = Location(
						data_aq_stations = data_aq_stations
						,data_district_monitoring = data_district_monitoring
					)
					logging.data(f'Location:\n{location}')


					metrics.location_succeeded += 1


				except ValueError as e:

					logging.warning(f'Skipping Location ID {data_aq_stations.LocationIdentifier}: {e}')

					metrics.location_failed += 1



			if metrics.location_total % feedback == 0:

				logging.info(metrics)



	#
	# Final feedback messages
	#

	logging.info('Finished processing Locations')

	logging.info(metrics)


#
# Private
#

def _check_credentials():
	'''
	The target SQL Server instance uses Windows authentication, so we need
	to ensure that this Python process is running as the correct user
	'''

	domain = os.environ.get('USERDOMAIN')
	user = os.environ.get('USERNAME')

	username = f'{domain}\\{user}' # Leave default string case, for display



	logging.debug('Checking OS username')
	if not username.upper() in C.OS_USERNAMES_HYDRO:

		raise RuntimeError(
			'Invalid Windows credentials'
			f'\nThis script must run in a Python session as the HQ\hydro user, but is running as {username}'
		)



def _configure_arguments():
	'''
	Configure arguments when running in script mode

	Returns configured argparse.ArgumentParser
	'''

	ap = argparse.ArgumentParser(
		conflict_handler = 'resolve' # Allow overwriting built-in -h/--help to add to custom argument group
		,description = 'Load asset and configuration data to hydro geodatabase'
	)



	g = ap.add_argument_group( # Avoid all named arguments being listed as 'optional' in help
		'Arguments'
	)



	g.add_argument(
		'-s'
		,'--server'
		,dest = 'server'
		,help = 'SQL Server hostname'
		,metavar = '<server>'
		,required = True
	)

	g.add_argument(
		'-L'
		,'--log-level'
		,choices = (
			'CRITICAL'
			,'ERROR'
			,'WARNING'
			,'INFO'
			,'DEBUG'
			,'DATA'
			,'DATADEBUG'
		)
		,default = 'INFO'
		,dest = 'log_level'
		,help = 'Logging level (default: INFO)'
		,required = False
		,type = str.upper
	)

	g.add_argument(
		'-l'
		,'--log-file'
		,dest = 'log_file_name'
		,help = 'Diagnostic log file name'
		,metavar = '<log_file>'
		,required = False
	)

	g.add_argument(
		'-f'
		,'--feedback'
		,default = 0
		,dest = 'feedback'
		,help = 'Feedback interval for progress metrics (number of Locations processed)'
		,metavar = '<feedback>'
		,required = False
		,type = int
	)

	g.add_argument(
		'-h'
		,'--help'
		,action = 'help'
	)


	# Positional arguments
	#
	# Positional arguments are always required, so `required` is not
	# permitted. Argument name is the destination, so `dest` is not
	# permitted. 

	g.add_argument(
		'source_aq_stations'
		# ,dest = 'source_aq_stations'
		,help = 'AQ_STATIONS feature class'
		,metavar = '<source_aq_stations>'
		# ,required = True
	)

	g.add_argument(
		'source_district_monitoring'
		# ,dest = 'source_district_monitoring'
		,help = 'District monitoring spreadsheet'
		,metavar = '<source_district_monitoring>'
		# ,required = True
	)



	return ap



def _configure_log_file(
	file_name
	,formatter = None
):
	'''
	Add log file handler to existing root logger
	Fail if file already exists
	'''

	try:

		logging.debug('Adding log FileHandler')
		handler = logging.FileHandler(
			file_name
			,mode = 'x'
			,encoding = 'utf-8'
		)


	except FileExistsError:

		logging.error(f'Log file \'{file_name}\' already exists')

		raise



	if formatter is not None:

		logging.debug('Setting log FileHandler Formatter')
		handler.setFormatter(formatter)



	logging.debug('Adding FileHandler to Logger')
	logging.getLogger().addHandler(handler)



def _connect_gdb(
	server
):
	'''
	Create temporary geodatabase connection using OS authentication

	Returns tempfile.TemporaryDirectory object, along with geodatabase
	connection file. You must retain a reference to the returned
	TemporaryDirectory, else it will go out-of-scope and automatically
	delete itself - including the connection file it contains. Retaining
	a reference to the file, itself, is not sufficient to prevent automatic
	cleanup.
	'''


	# Check Windows credentials

	try:

		_check_credentials()


	except RuntimeError as e:

		raise



	# Create connection

	temp_dir = tempfile.TemporaryDirectory()
	logging.debug(f'Created temporary directory {temp_dir.name}')



	arcpy.management.CreateDatabaseConnection(
		out_folder_path = temp_dir.name
		,out_name = C.CONNECTION_FILE_NAME
		,database_platform = 'SQL_SERVER'
		,instance = server
		,account_authentication = 'OPERATING_SYSTEM_AUTH'
		,database = 'hydro'
	)


	gdb = os.path.join(
		temp_dir.name
		,C.CONNECTION_FILE_NAME
	)
	logging.debug(f'Created database connection file: {gdb}')



	# Validate geodatabase connection
	#
	# Creating connection file does not appear to test connection, just
	# write properties to file

	logging.debug('Validating geodatabase connection')
	try:

		# Describe raises:
		#	IOError if target is not a recognized object type
		#	OSError if target does not exist

		d = arcpy.Describe(gdb)
		logging.debug(f'Describe type: {d.dataType}')



		# Referencing workspaceType raises AttributeError if target is not a workspace

		if not d.workspaceType == 'RemoteDatabase':

			# Explicitly raise exception if target is not an enterprise geodatabase

			raise TypeError(f'Expected RemoteDatabase type; got {d.workspaceType} type')


	except (
		IOError
		,OSError
		,AttributeError
		,TypeError
	) as e:

		raise RuntimeError('Invalid enterprise geodatabase') from e



	# Return connection file AND TemporaryDirectory; see function header
	# comments for details

	return(
		gdb
		,temp_dir
	)



def _initialize_logging(
	level = logging.NOTSET
):
	'''
	Configure basic console logging

	When running in script mode, this function is called early to establish
	a basic communication channel with the user. The intent is to perform
	minimial configuration here - both to reduce the possiblity of errors
	before the channel is ready, and to avoid expensive processing if the
	script exits early (e.g. invalid argument) - while also building some
	of the foundation for more robust logging that may be specified in
	the script's runtime arguments.

	Use the `logging` module's root logger, and send all messages to stdout.
	Log at the most verbose level (NOTSET) to avoid suppressing useful
	messages in case of early problems, with the expectation that the
	script will choose a more reasonable level after processing arguments.
	Define custom formatting now, to avoid early messages looking
	differently than later ones.

	The custom implementations includes attributes and methods that mimic
	those of the built-in levels, including:

		Logging level macros

			logging.DATA
			logging.DATADEBUG

		Wrapper functions, at module level

			logging.data('message')
			logging.datadebug('message')

		Wrapper functions, at root logger level

			l = logging.getLogger()
			l.data('message')
			l.datadebug('message')

	Returns formatter, for use with other handlers.
	'''


	# Configure custom DATA level

	logging.DATA = mg.LOG_LEVEL_DATA

	logging.addLevelName(
		logging.DATA
		,'DATA'
	)

	logging.data = _logging_data
	logging.getLogger().data = _logging_data



	# Configure custom DATADEBUG level

	logging.DATADEBUG = mg.LOG_LEVEL_DATADEBUG

	logging.addLevelName(
		logging.DATADEBUG
		,'DATADEBUG'
	)

	logging.datadebug = _logging_datadebug
	logging.getLogger().datadebug = _logging_datadebug



	# Formatter

	f = mg.FormatterIndent(
		fmt = mg.LOG_FORMAT
		,datefmt = mg.LOG_FORMAT_DATE
	)



	# Handler

	h = logging.StreamHandler(sys.stdout)

	h.setFormatter(f)



	# Logger

	l = logging.getLogger()

	l.setLevel(level)
	l.addHandler(h)



	# Return

	return f



def _logging_data(
	msg
	,*args
	,**kwargs
):
	'''
	Create function for custom logging.DATA level

	This function will be bound to the logging module and the root logger
	the root logger to match the convenience functions for the built-in
	log levels. For example: logging.data('message')
	'''

	logging.log(
		logging.DATA
		,msg
		,*args
		,**kwargs
	)



def _logging_datadebug(
	msg
	,*args
	,**kwargs
):
	'''
	Create function for custom logging.DATADEBUG level

	This function will be bound to the logging module and the root logger
	the root logger to match the convenience functions for the built-in
	log levels. For example: logging.datadebug('message')
	'''

	logging.log(
		logging.DATADEBUG
		,msg
		,*args
		,**kwargs
	)



def _print_banner(
	args
):
	'''
	Print banner containing argument information to log
	'''

	banner = (
		f'{mg.BANNER_DELIMITER_1}\n'
		f'Hydrologic Data Model Data Loader\n'
		f'{mg.BANNER_DELIMITER_2}\n'
		f'Source data: Aquarius stations:    {args.source_aq_stations}\n'
		f'Source data: District monitoring:  {args.source_district_monitoring}\n'
		f'Target database server:            {args.server}\n'
		f'Log level:                         {args.log_level}\n'
		f'Log file:                          {args.log_file_name}\n'
		f'Feedback:                          {args.feedback}\n'
		f'{mg.BANNER_DELIMITER_1}'
	)



	# Print banner

	logging.info(banner)



def _process_arguments(
	log_formatter = None # Formatter to use with log file
):
	'''
	Process arguments for main block

	Act on arguments that can be handled immediately. Return arguments, as
	well as any objects created here that are needed elsewhere.

	Note: Refrain from sending log messges until the log level argument is
	processed, as not to report extraneous information to a user who
	requested a coarser level of detail.
	'''


	# Define arguments

	parser = _configure_arguments()



	# Fetch argument values

	args = parser.parse_args()



	#
	# Evaluate arguments
	#


	# Set log level

	logging.getLogger().setLevel(args.log_level)



	# Configure log file
	#
	# Do this as early as possible, so we can capture the most messages to
	# the log file; logging messages sent before log file coniguration will
	# go to console only

	if args.log_file_name is not None:

		logging.debug(f'Configuring log file {args.log_file_name}')
		_configure_log_file(
			args.log_file_name
			,log_formatter
		)



	# Standardize paths
	#
	# Relative paths break some arcpy functionality (e.g. accessing Excel
	# tables) so force all paths to absolute

	source_aq_stations = os.path.abspath(args.source_aq_stations)
	source_district_monitoring = os.path.abspath(args.source_district_monitoring)



	#
	# Return
	#

	return (
		args
		,source_aq_stations
		,source_district_monitoring
	)



if __name__ == '__main__':


	#
	# Setup
	#


	# Initialize logging infrastructure; do this early so we can communicate
	# with user
	#
	# Keep a reference to the formatter so we can use it with other handlers
	# (e.g. FileHandler)

	log_formatter = _initialize_logging()



	# Process arguments

	try:

		(
			args
			,source_aq_stations
			,source_district_monitoring
		) = _process_arguments(log_formatter)


	except Exception as e:

		logging.error(e)
		raise



	# Print banner

	_print_banner(args)



	# Connect to geodatabase

	logging.info('Connecting to geodatabase')

	try:

		(
			gdb
			,temp_dir
		) = _connect_gdb(args.server)


	except RuntimeError as e:

		logging.error(e)

		sys.exit(mg.EXIT_FAILURE)



	#
	# Load data
	#

	load_data(
		target_gdb = gdb
		,source_aq_stations = source_aq_stations
		,source_district_monitoring = source_district_monitoring
		,feedback = args.feedback
	)



	#
	# Cleanup
	#

	logging.info('Done.')


################################################################################
# END
################################################################################