################################################################################
# Name:
#	create_hydro_data_model.py
#
# Purpose:
#	Create geodatabase objects that compose the hydrologic monitoring data
#	model
#
# Environment:
#	ArcGIS Pro 3.0.4
#	Python 3.9.11, with:
#		arcpy 3.0 (build py39_arcgispro_36045)
#
# Notes:
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
#	2022-07-18 MCM Created
#	2022-09-18 MCM Switched to OS authentication (Hydro 17/18)
#	2022-11-21 MCM Upgraded attachment format (Hydro 55)
#	               Added LocationVisit.InventoryVerifed column (Hydro 59)
#	2022-12-07 MCM Moved VisitStaff table to delimited text column
#	                LocationVisit.Staff (Hydro 60)
#	2022-12-14 MCM Moved literals to constant OS_USERNAMES
#	               Removed extraneous `datetime` import
#	2023-02-13 MCM Added Location.HasADVMBattery (Hydro 67)
#	               Removed column TemperatureMeasurement.ManualLevelUnits
#	                 and domain Temperature Units (Hydro 68)
#	2023-02-22 MCM Moved constants to constants.py
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
import logging
import os
import sys
import tempfile


# Custom

import constants as C
import mg



################################################################################
# Object creation functions
################################################################################


####################
# Domains
####################

def create_domains(
	gdb
	,indent_level = 0
):


	#
	# Define domain properties
	#


	logging.debug('Defining domain properties')


	# Coded value domains

	logging.debug('Defining coded value domains')
	domains_cv = (
		# name, data type, (coded value, ...)
		(
			'ADVM Beam Check Initial Exception', 'TEXT', (
				('Value 1', 'Value 1')
				,('Value 2', 'Value 2')
			)
		)
		,(
			'ADVM Beam Check Secondary Exception', 'TEXT', (
				('Value 1', 'Value 1')
				,('Value 2', 'Value 2')
			)
		)
		,(
			'ADVM Cleaned Exception', 'TEXT', (
				('Value 1', 'Value 1')
				,('Value 2', 'Value 2')
			)
		)
		,(
			'ADVM Maintenance', 'TEXT', (
				('Value 1', 'Value 1')
				,('Value 2', 'Value 2')
			)
		)
		,(
			'Battery Condition', 'TEXT', (
				('Good', 'Good')
				,('Poor', 'Poor')
			)
		)
		,(
			'Battery Replacement Exception', 'TEXT', (
				('No materials', 'No materials')
				,('Has solar panel', 'Has solar panel')
				,('Other', 'Other')
			)
		)
		,(
			'Conductivity Adjustment Exception', 'TEXT', (
				('Missing standard', 'Missing standard')
				,('Sensor failed', 'Sensor failed')
				,('Time', 'Time')
				,('Unable to pull sensor', 'Unable to pull sensor')
				,('Other', 'Other')
			)
		)
		,(
			'Conductivity Serial Number', 'TEXT', (
				('Serial number 1', 'Serial number 1')
				,('Serial number 2', 'Serial number 2')
			)
		)
		,(
			'Conductivity Standard', 'LONG', (
				('1', '1')
				,('10', '10')
				,('100', '100')
				,('1000', '1000')
			)
		)
		,(
			'Data Logger Type', 'TEXT', (
				('Type 1', 'Type 1')
				,('Type 2', 'Type 2')
			)
		)
		,(
			'Dessicant Maintenance', 'TEXT', (
				('Verified', 'Verified')
				,('Replaced', 'Replaced')
				,('Needs replacement - No materials', 'Needs replacement - No materials')
				,('Other', 'Other')
			)
		)
		,(
			'Groundwater Adjustment Exception', 'TEXT', (
				('Before water quality sample', 'Before water quality sample')
				,('Low conductivity', 'Low conductivity')
				,('Time', 'Time')
				,('Weather', 'Weather')
				,('Other', 'Other')
			)
		)
		,(
			'Hydro Staff', 'TEXT', (
				('Katie Price', 'Katie Price')
				,('Steve Costa', 'Steve Costa')
			)
		)
		,(
			'Location Issue Type', 'TEXT', (
				('Conduit', 'Conduit')
				,('Incorrect inventory', 'Incorrect inventory')
				,('Invalid punch', 'Invalid punch')
				,('Solar panel', 'Solar panel')
				,('Vandalism', 'Vandalism')
				,('Other', 'Other')
			)
		)
		,(
			'Rainfall Exception', 'TEXT', (
				('No ladder', 'No ladder')
				,('Raining', 'Raining')
				,('Other', 'Other')
			)
		)
		,(
			'Reading Type', 'TEXT', (
				('Routine', 'Routine')
				,('Routine before', 'Routine before')
				,('Routine after', 'Routine after')
				,('After calibration', 'After calibration')
				,('Reset before', 'Reset before')
				,('Reset after', 'Reset after')
				,('Cleaning before', 'Cleaning before')
				,('Cleaning after', 'Cleaning after')
				,('Other', 'Other')
			)
		)
		,(
			'Sensor Type', 'TEXT', (
				('Type 1', 'Type 1')
				,('Type 2', 'Type 2')
			)
		)
		,(
			'Stage Adjustment Exception', 'TEXT', (
				('Environmental', 'Environmental')
				,('Safety', 'Safety')
				,('Time', 'Time')
				,('Weather', 'Weather')
				,('Wind', 'Wind')
				,('Other', 'Other')
			)
		)
		,(
			'Temperature Serial Number', 'TEXT', (
				('Serial number 1', 'Serial number 1')
				,('Serial number 2', 'Serial number 2')
			)
		)
		,(
			'Temperature Source', 'TEXT', (
				('ADVM', 'ADVM')
				,('Conductivity', 'Conductivity')
				,('Transducer', 'Transducer')
			)
		)
		,(
			'Time Adjustment Type', 'TEXT', (
				('Drift', 'Drift')
				,('Clock default', 'Clock default')
			)
		)
		,(
			'Yes/No', 'TEXT', (
				('Yes', 'Yes')
				,('No', 'No')
			)
		)
	)



	#
	# Create domains
	#


	# Coded value

	for d in domains_cv:

		domain_name = d[0]
		data_type = d[1]
		coded_values = d[2]


		mg.create_domain_cv(
			gdb = gdb
			,coded_values = coded_values
			,name = domain_name
			,data_type = data_type
			,indent_level = indent_level
		)




####################
# Feature Classes
####################

def create_fcs(
	gdb
	,indent_level = 0
):

	create_fc_location(gdb, indent_level)



def create_fc_location(
	gdb
	,indent_level = 0
):


	# Configuration

	fc_name = 'Location'
	alias = 'Location'

	geometry = 'POINT'
	sr = C.SR_UTM16N_NAD83

	global_id = True
	editor_tracking = True
	archiving = True
	attachments = True
	attachments_upgrade = True

	fc = os.path.join(
		gdb
		,fc_name
	)

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('NWFID'			,'TEXT'		,None		,None	,32		,'NWFID'			,True		,False		,None					,None)
		,('Name'			,'TEXT'		,None		,None	,128		,'Name'				,True		,False		,None					,None)
		,('Project'			,'LONG'		,None		,None	,None		,'Project Number'		,True		,False		,None					,None)
		,('HasDataLogger'		,'TEXT'		,None		,None	,3		,'Has Data Logger'		,True		,False		,'Yes/No'				,None)
		,('HasRainfall'			,'TEXT'		,None		,None	,3		,'Has Rainfall'			,True		,False		,'Yes/No'				,None)
		,('HasStage'			,'TEXT'		,None		,None	,3		,'Has Stage'			,True		,False		,'Yes/No'				,None)
		,('HasGroundwater'		,'TEXT'		,None		,None	,3		,'Has Groundwater'		,True		,False		,'Yes/No'				,None)
		,('HasConductivity'		,'TEXT'		,None		,None	,3		,'Has Conductivity'		,True		,False		,'Yes/No'				,None)
		,('HasADVM'			,'TEXT'		,None		,None	,3		,'Has ADVM'			,True		,False		,'Yes/No'				,None)
		,('HasADVMBattery'		,'TEXT'		,None		,None	,3		,'Has ADVM Battery'		,True		,False		,'Yes/No'				,None)
		,('HasDischarge'		,'TEXT'		,None		,None	,3		,'Has Discharge'		,True		,False		,'Yes/No'				,None)
		,('HasTemperature'		,'TEXT'		,None		,None	,3		,'Has Temperature'		,True		,False		,'Yes/No'				,None)
		,('HasWaterQuality'		,'TEXT'		,None		,None	,3		,'Has Water Quality'		,True		,False		,'Yes/No'				,None)
		,('Comments'			,'TEXT'		,None		,None	,1024		,'Comments'			,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user		read		write
		('HQ\\arcgis'	,'GRANT'	,'GRANT')
		,
	)



	# Create feature class

	mg.create_fc(
		gdb = gdb
		,fc_name = fc_name
		,alias = alias
		,geometry = geometry
		,sr = sr
		,attributes = attributes
		,subtypes = subtypes
		,global_id = global_id
		,editor_tracking = editor_tracking
		,archiving = archiving
		,attachments = attachments
		,attachments_upgrade = attachments_upgrade
		,privileges = privileges
		,indent_level = indent_level
	)



####################
# Attribute tables
####################

def create_tables(
	gdb
	,indent_level = 0
):

	create_table_conductivitymeasurement(gdb, indent_level)
	create_table_datalogger(gdb, indent_level)
	create_table_groundwatermeasurement(gdb, indent_level)
	create_table_locationissue(gdb, indent_level)
	create_table_locationvisit(gdb, indent_level)
	create_table_measuringpoint(gdb, indent_level)
	create_table_rainfalltips(gdb, indent_level)
	create_table_sensor(gdb, indent_level)
	create_table_stagemeasurement(gdb, indent_level)
	create_table_temperaturemeasurement(gdb, indent_level)



def create_table_conductivitymeasurement(
	gdb
	,indent_level = 0
):


	# Configuration

	table_name = 'ConductivityMeasurement'
	alias = 'Conductivity Measurement'

	global_id = True
	editor_tracking = True
	archiving = True
	attachments = False

	table = os.path.join(
		gdb
		,table_name
	)

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('MeasureDate'			,'DATE'		,None		,None	,None		,'Measurement Date'		,True		,False		,None					,None)
		,('ReadingType'			,'TEXT'		,None		,None	,32		,'Reading Type'			,True		,False		,'Reading Type'				,None)
		,('SerialNumber'		,'TEXT'		,None		,None	,32		,'Serial Number'		,True		,False		,'Conductivity Serial Number'		,None)
		,('ManualLevel'			,'LONG'		,None		,None	,None		,'Manual Measurement'		,True		,False		,None					,None)
		,('SensorLevel'			,'LONG'		,None		,None	,None		,'Realtime Sensor Level'	,True		,False		,None					,None)
		,('SensorAdjustmentAmount'	,'LONG'		,None		,None	,None		,'Sensor Adjustment Amount'	,True		,False		,None					,None)
		,('SensorAdjusted'		,'TEXT'		,None		,None	,3		,'Sensor Adjusted'		,True		,False		,'Yes/No'				,None)
		,('SensorAdjustmentException'	,'TEXT'		,None		,None	,32		,'Sensor Adjustment Exception'	,True		,False		,'Conductivity Adjustment Exception'	,None)
		,('SensorAdjustmentDate'	,'DATE'		,None		,None	,None		,'Sensor Adjustment Date'	,True		,False		,None					,None)
		,('CalibrationStandard'		,'LONG'		,None		,None	,None		,'Calibration Standard'		,True		,False		,'Conductivity Standard'		,None)
		,('VerificationStandard'	,'LONG'		,None		,None	,None		,'Verification Standard'	,True		,False		,'Conductivity Standard'		,None)
		,('VerificationLevel'		,'LONG'		,None		,None	,None		,'Verification Sensor Level'	,True		,False		,None					,None)
		,('VerificationDate'		,'DATE'		,None		,None	,None		,'Verification Date'		,True		,False		,None					,None)
		,('LocationVisitGlobalID'	,'GUID'		,None		,None	,None		,'Related Location Visit'	,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user		read		write
		('HQ\\arcgis'	,'GRANT'	,'GRANT')
		,
	)



	# Create table

	mg.create_table(
		gdb = gdb
		,table_name = table_name
		,alias = alias
		,attributes = attributes
		,subtypes = subtypes
		,global_id = global_id
		,editor_tracking = editor_tracking
		,archiving = archiving
		,attachments = attachments
		,privileges = privileges
		,indent_level = indent_level
	)



def create_table_datalogger(
	gdb
	,indent_level = 0
):


	# Configuration

	table_name = 'DataLogger'
	alias = 'Data Logger'

	global_id = True
	editor_tracking = True
	archiving = True
	attachments = True
	attachments_upgrade = True

	table = os.path.join(
		gdb
		,table_name
	)

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('DataLoggerType'		,'TEXT'		,None		,None	,32		,'Data Logger Type'		,True		,False		,'Data Logger Type'			,None)
		,('SerialNumber'		,'TEXT'		,None		,None	,32		,'Serial Number'		,True		,False		,None					,None)
		,('Comments'			,'TEXT'		,None		,None	,1024		,'Comments'			,True		,False		,None					,None)
		,('LocationGlobalID'		,'GUID'		,None		,None	,None		,'Related Location'		,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user		read		write
		('HQ\\arcgis'	,'GRANT'	,'GRANT')
		,
	)



	# Create table

	mg.create_table(
		gdb = gdb
		,table_name = table_name
		,alias = alias
		,attributes = attributes
		,subtypes = subtypes
		,global_id = global_id
		,editor_tracking = editor_tracking
		,archiving = archiving
		,attachments = attachments
		,attachments_upgrade = attachments_upgrade
		,privileges = privileges
		,indent_level = indent_level
	)



def create_table_groundwatermeasurement(
	gdb
	,indent_level = 0
):


	# Configuration

	table_name = 'GroundwaterMeasurement'
	alias = 'Groundwater Measurement'

	global_id = True
	editor_tracking = True
	archiving = True
	attachments = False

	table = os.path.join(
		gdb
		,table_name
	)

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('MeasureDate'			,'DATE'		,None		,None	,None		,'Measurement Date'		,True		,False		,None					,None)
		,('ReadingType'			,'TEXT'		,None		,None	,32		,'Reading Type'			,True		,False		,'Reading Type'				,None)
		,('ManualLevel'			,'DOUBLE'	,38		,2	,None		,'Manual Measurement (feet)'	,True		,False		,None					,None)
		,('WaterLevel'			,'DOUBLE'	,38		,2	,None		,'Computed Manual Water Level'	,True		,False		,None					,None)
		,('SensorLevel'			,'DOUBLE'	,38		,2	,None		,'Realtime Sensor Level'	,True		,False		,None					,None)
		,('SensorAdjustmentAmount'	,'DOUBLE'	,38		,2	,None		,'Sensor Adjustment Amount'	,True		,False		,None					,None)
		,('SensorAdjusted'		,'TEXT'		,None		,None	,3		,'Sensor Adjusted'		,True		,False		,'Yes/No'				,None)
		,('SensorAdjustmentException'	,'TEXT'		,None		,None	,32		,'Sensor Adjustment Exception'	,True		,False		,'Groundwater Adjustment Exception'	,None)
		,('SensorAdjustmentDate'	,'DATE'		,None		,None	,None		,'Sensor Adjustment Date'	,True		,False		,None					,None)
		,('LocationVisitGlobalID'	,'GUID'		,None		,None	,None		,'Related Location Visit'	,True		,False		,None					,None)
		,('MeasuringPointGlobalID'	,'GUID'		,None		,None	,None		,'Related Measuring Point'	,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user		read		write
		('HQ\\arcgis'	,'GRANT'	,'GRANT')
		,
	)



	# Create table

	mg.create_table(
		gdb = gdb
		,table_name = table_name
		,alias = alias
		,attributes = attributes
		,subtypes = subtypes
		,global_id = global_id
		,editor_tracking = editor_tracking
		,archiving = archiving
		,attachments = attachments
		,privileges = privileges
		,indent_level = indent_level
	)



def create_table_locationissue(
	gdb
	,indent_level = 0
):


	# Configuration

	table_name = 'LocationIssue'
	alias = 'Location Issue'

	global_id = True
	editor_tracking = True
	archiving = True
	attachments = True
	attachments_upgrade = True

	table = os.path.join(
		gdb
		,table_name
	)

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('Type'				,'TEXT'		,None		,None	,32		,'Issue Type'			,True		,False		,'Location Issue Type'			,None)
		,('Comments'			,'TEXT'		,None		,None	,1024		,'Comments'			,True		,False		,None					,None)
		,('LocationVisitGlobalID'	,'GUID'		,None		,None	,None		,'Related Location Visit'	,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user		read		write
		('HQ\\arcgis'	,'GRANT'	,'GRANT')
		,
	)



	# Create table

	mg.create_table(
		gdb = gdb
		,table_name = table_name
		,alias = alias
		,attributes = attributes
		,subtypes = subtypes
		,global_id = global_id
		,editor_tracking = editor_tracking
		,archiving = archiving
		,attachments = attachments
		,attachments_upgrade = attachments_upgrade
		,privileges = privileges
		,indent_level = indent_level
	)



def create_table_locationvisit(
	gdb
	,indent_level = 0
):


	# Configuration

	table_name = 'LocationVisit'
	alias = 'Location Visit'

	global_id = True
	editor_tracking = True
	archiving = True
	attachments = True
	attachments_upgrade = True

	table = os.path.join(
		gdb
		,table_name
	)

	attributes = (
		#name					,type		,precision	,scale	,length		,alias					,nullable	,required	,domain					,default
		('VisitDate'				,'DATE'		,None		,None	,None		,'Visit Date'				,True		,False		,None					,None)
		,('Staff'				,'TEXT'		,None		,None	,1024		,'Visit Staff'				,True		,False		,'Hydro Staff'				,None)
		,('InventoryVerified'			,'TEXT'		,None		,None	,3		,'Equipment Inventory Verified'		,True		,False		,'Yes/No'				,None)
		,('BatteryDOA'				,'TEXT'		,None		,None	,3		,'Battery DOA'				,True		,False		,'Yes/No'				,None)
		,('BatteryCondition'			,'TEXT'		,None		,None	,32		,'Battery Condition'			,True		,False		,'Battery Condition'			,None)
		,('BatteryVoltage'			,'DOUBLE'	,38		,2	,None		,'Battery Voltage'			,True		,False		,None					,None)
		,('BatteryReplaced'			,'TEXT'		,None		,None	,3		,'Battery Replaced'			,True		,False		,'Yes/No'				,None)
		,('BatteryReplacementException'		,'TEXT'		,None		,None	,32		,'Battery Replacement Exception'	,True		,False		,'Battery Replacement Exception'	,None)
		,('BatteryReplacementDate'		,'DATE'		,None		,None	,None		,'Battery Replacement Date'		,True		,False		,None					,None)
		,('DessicantEnclosure'			,'TEXT'		,None		,None	,32		,'Enclosure Dessicant'			,True		,False		,'Dessicant Maintenance'		,None)
		,('DessicantStage'			,'TEXT'		,None		,None	,32		,'Stage Sensor Dessicant'		,True		,False		,'Dessicant Maintenance'		,None)
		,('DessicantGroundwater'		,'TEXT'		,None		,None	,32		,'Groundwater Sensor Dessicant'		,True		,False		,'Dessicant Maintenance'		,None)
		,('DataLoggerRecordStart'		,'DATE'		,None		,None	,None		,'Data Logger Record Start'		,True		,False		,None					,None)
		,('DataLoggerRecordEnd'			,'DATE'		,None		,None	,None		,'Data Logger Record End'		,True		,False		,None					,None)
		,('DataLoggerTimeAdjustmentType'	,'TEXT'		,None		,None	,32		,'Data Logger Time Adjustment Type'	,True		,False		,'Time Adjustment Type'			,None)
		,('DataLoggerTimeAdjustmentAmount'	,'LONG'		,None		,None	,None		,'Data Logger Time Adjustment (minutes)'	,True	,False		,None					,None)
		,('DataLoggerTimeAdjustmentDate'	,'DATE'		,None		,None	,None		,'Data Logger Time Adjustment Date'	,True		,False		,None					,None)
		,('RainfallBucketCleaned'		,'TEXT'		,None		,None	,3		,'Rainfall Bucket Cleaned'		,True		,False		,'Yes/No'				,None)
		,('RainfallBucketException'		,'TEXT'		,None		,None	,32		,'Rainfall Bucket Exception'		,True		,False		,'Rainfall Exception'			,None)
		,('RainfallMechanismChecked'		,'TEXT'		,None		,None	,3		,'Tipping Mechanism Checked'		,True		,False		,'Yes/No'				,None)
		,('RainfallMechanismException'		,'TEXT'		,None		,None	,32		,'Tipping Mechanism Exception'		,True		,False		,'Rainfall Exception'			,None)
		,('ADVMBatteryDOA'			,'TEXT'		,None		,None	,3		,'ADVM Battery DOA'			,True		,False		,'Yes/No'				,None)
		,('ADVMBatteryCondition'		,'TEXT'		,None		,None	,32		,'ADVM Battery Condition'		,True		,False		,'Battery Condition'			,None)
		,('ADVMBatteryVoltage'			,'DOUBLE'	,38		,2	,None		,'ADVM Battery Voltage'			,True		,False		,None					,None)
		,('ADVMBatteryReplaced'			,'TEXT'		,None		,None	,3		,'ADVM Battery Replaced'		,True		,False		,'Yes/No'				,None)
		,('ADVMBatteryReplacementException'	,'TEXT'		,None		,None	,32		,'ADVM Battery Replacement Exception'	,True		,False		,'Battery Replacement Exception'	,None)
		,('ADVMBatteryReplacementDate'		,'DATE'		,None		,None	,None		,'ADVM Battery Replacement Date'	,True		,False		,None					,None)
		,('ADVMRecordStart'			,'DATE'		,None		,None	,None		,'ADVM Record Start'			,True		,False		,None					,None)
		,('ADVMRecordEnd'			,'DATE'		,None		,None	,None		,'ADVM Record End'			,True		,False		,None					,None)
		,('ADVMBeamCheckedInitial'		,'TEXT'		,None		,None	,3		,'ADVM Initial Beam Checked'		,True		,False		,'Yes/No'				,None)
		,('ADVMBeamCheckInitialException'	,'TEXT'		,None		,None	,32		,'ADVM Initial Beam Check Exception'	,True		,False		,'ADVM Beam Check Initial Exception'	,None)
		,('ADVMBeamCheckedSecondary'		,'TEXT'		,None		,None	,3		,'ADVM Secondary Beam Checked'		,True		,False		,'Yes/No'				,None)
		,('ADVMBeamCheckSecondaryException'	,'TEXT'		,None		,None	,32		,'ADVM Secondary Beam Check Exception'	,True		,False		,'ADVM Beam Check Secondary Exception'	,None)
		,('ADVMCleaned'				,'TEXT'		,None		,None	,3		,'ADVM Cleaned'				,True		,False		,'Yes/No'				,None)
		,('ADVMCleanedException'		,'TEXT'		,None		,None	,32		,'ADVM Cleaned Exception'		,True		,False		,'ADVM Cleaned Exception'		,None)
		,('ADVMMaintenance'			,'TEXT'		,None		,None	,32		,'ADVM Additional Maintenace'		,True		,False		,'ADVM Maintenance'			,None)
		,('DischargeRecordStart'		,'DATE'		,None		,None	,None		,'Discharge Record Start'		,True		,False		,None					,None)
		,('DischargeRecordEnd'			,'DATE'		,None		,None	,None		,'Discharge Record End'			,True		,False		,None					,None)
		,('DischargeStageStart'			,'DATE'		,None		,None	,None		,'Discharge Stage Start'		,True		,False		,None					,None)
		,('DischargeStageEnd'			,'DATE'		,None		,None	,None		,'Discharge Stage End'			,True		,False		,None					,None)
		,('DischargeVolume'			,'DOUBLE'	,38		,2	,None		,'Discharge Volume'			,True		,False		,None					,None)
		,('DischargeUncertainty'		,'DOUBLE'	,38		,2	,None		,'Discharge Uncertainty'		,True		,False		,None					,None)
		,('WaterQualitySensorPulled'		,'TEXT'		,None		,None	,3		,'Water Quality Sensor Pulled'		,True		,False		,'Yes/No'				,None)
		,('WaterQualitySensorPullDate'		,'DATE'		,None		,None	,None		,'Water Quality Sensor Pull Date'	,True		,False		,None					,None)
		,('WaterQualityPurgeStart'		,'DATE'		,None		,None	,None		,'Water Quality Purge Start'		,True		,False		,None					,None)
		,('WaterQualitySamplingEnd'		,'DATE'		,None		,None	,None		,'Water Quality Sampling End'		,True		,False		,None					,None)
		,('WaterQualitySensorReinstallDate'	,'DATE'		,None		,None	,None		,'Water Quality Sensor Reinstall Date'	,True		,False		,None					,None)
		,('LocationGlobalID'			,'GUID'		,None		,None	,None		,'Related Location'			,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user		read		write
		('HQ\\arcgis'	,'GRANT'	,'GRANT')
		,
	)



	# Create table

	mg.create_table(
		gdb = gdb
		,table_name = table_name
		,alias = alias
		,attributes = attributes
		,subtypes = subtypes
		,global_id = global_id
		,editor_tracking = editor_tracking
		,archiving = archiving
		,attachments = attachments
		,attachments_upgrade = attachments_upgrade
		,privileges = privileges
		,indent_level = indent_level
	)



def create_table_measuringpoint(
	gdb
	,indent_level = 0
):


	# Configuration

	table_name = 'MeasuringPoint'
	alias = 'Measuring Point'

	global_id = True
	editor_tracking = True
	archiving = True
	attachments = True
	attachments_upgrade = True

	table = os.path.join(
		gdb
		,table_name
	)

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('Name'				,'TEXT'		,None		,None	,32		,'Name'				,True		,False		,None					,None)
		,('AquariusID'			,'GUID'		,None		,None	,None		,'Aquarius ID'			,True		,False		,None					,None)
		,('Description'			,'TEXT'		,None		,None	,1024		,'Serial Number'		,True		,False		,None					,None)
		,('Elevation'			,'DOUBLE'	,38		,2	,None		,'Elevation'			,True		,False		,None					,None)
		,('Comments'			,'TEXT'		,None		,None	,1024		,'Comments'			,True		,False		,None					,None)
		,('LocationGlobalID'		,'GUID'		,None		,None	,None		,'Related Location'		,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user		read		write
		('HQ\\arcgis'	,'GRANT'	,'GRANT')
		,
	)



	# Create table

	mg.create_table(
		gdb = gdb
		,table_name = table_name
		,alias = alias
		,attributes = attributes
		,subtypes = subtypes
		,global_id = global_id
		,editor_tracking = editor_tracking
		,archiving = archiving
		,attachments = attachments
		,attachments_upgrade = attachments_upgrade
		,privileges = privileges
		,indent_level = indent_level
	)



def create_table_rainfalltips(
	gdb
	,indent_level = 0
):


	# Configuration

	table_name = 'RainfallTips'
	alias = 'Rainfall False Tips'

	global_id = True
	editor_tracking = True
	archiving = True
	attachments = False

	table = os.path.join(
		gdb
		,table_name
	)

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('FalseTipCount'		,'DOUBLE'	,38		,2	,None		,'False Tip Count (inches)'	,True		,False		,None					,None)
		,('FalseTipDate'		,'DATE'		,None		,None	,None		,'False Tip Date'		,True		,False		,None					,None)
		,('FalseTipRemoved'		,'TEXT'		,None		,None	,3		,'False Tip Removed'		,True		,False		,'Yes/No'				,None)
		,('LocationVisitGlobalID'	,'GUID'		,None		,None	,None		,'Related Location Visit'	,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user		read		write
		('HQ\\arcgis'	,'GRANT'	,'GRANT')
		,
	)



	# Create table

	mg.create_table(
		gdb = gdb
		,table_name = table_name
		,alias = alias
		,attributes = attributes
		,subtypes = subtypes
		,global_id = global_id
		,editor_tracking = editor_tracking
		,archiving = archiving
		,attachments = attachments
		,privileges = privileges
		,indent_level = indent_level
	)



def create_table_sensor(
	gdb
	,indent_level = 0
):


	# Configuration

	table_name = 'Sensor'
	alias = 'Sensor'

	global_id = True
	editor_tracking = True
	archiving = True
	attachments = False

	table = os.path.join(
		gdb
		,table_name
	)

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('SensorType'			,'TEXT'		,None		,None	,32		,'Sensor Type'			,True		,False		,'Sensor Type'				,None)
		,('SerialNumber'		,'TEXT'		,None		,None	,32		,'Serial Number'		,True		,False		,None					,None)
		,('Comments'			,'TEXT'		,None		,None	,1024		,'Comments'			,True		,False		,None					,None)
		,('DataLoggerGlobalID'		,'GUID'		,None		,None	,None		,'Related Data Logger'		,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user		read		write
		('HQ\\arcgis'	,'GRANT'	,'GRANT')
		,
	)



	# Create table

	mg.create_table(
		gdb = gdb
		,table_name = table_name
		,alias = alias
		,attributes = attributes
		,subtypes = subtypes
		,global_id = global_id
		,editor_tracking = editor_tracking
		,archiving = archiving
		,attachments = attachments
		,privileges = privileges
		,indent_level = indent_level
	)



def create_table_stagemeasurement(
	gdb
	,indent_level = 0
):


	# Configuration

	table_name = 'StageMeasurement'
	alias = 'Stage Measurement'

	global_id = True
	editor_tracking = True
	archiving = True
	attachments = False

	table = os.path.join(
		gdb
		,table_name
	)

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('MeasureDate'			,'DATE'		,None		,None	,None		,'Measurement Date'		,True		,False		,None					,None)
		,('ManualLevel'			,'DOUBLE'	,38		,2	,None		,'Manual Measurement (feet)'	,True		,False		,None					,None)
		,('WaterLevel'			,'DOUBLE'	,38		,2	,None		,'Computed Manual Water Level'	,True		,False		,None					,None)
		,('SensorLevel'			,'DOUBLE'	,38		,2	,None		,'Realtime Sensor Level'	,True		,False		,None					,None)
		,('SensorAdjustmentAmount'	,'DOUBLE'	,38		,2	,None		,'Sensor Adjustment Amount'	,True		,False		,None					,None)
		,('SensorAdjusted'		,'TEXT'		,None		,None	,3		,'Sensor Adjusted'		,True		,False		,'Yes/No'				,None)
		,('SensorAdjustmentException'	,'TEXT'		,None		,None	,32		,'Sensor Adjustment Exception'	,True		,False		,'Stage Adjustment Exception'		,None)
		,('SensorAdjustmentDate'	,'DATE'		,None		,None	,None		,'Sensor Adjustment Date'	,True		,False		,None					,None)
		,('LocationVisitGlobalID'	,'GUID'		,None		,None	,None		,'Related Location Visit'	,True		,False		,None					,None)
		,('MeasuringPointGlobalID'	,'GUID'		,None		,None	,None		,'Related Measuring Point'	,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user		read		write
		('HQ\\arcgis'	,'GRANT'	,'GRANT')
		,
	)



	# Create table

	mg.create_table(
		gdb = gdb
		,table_name = table_name
		,alias = alias
		,attributes = attributes
		,subtypes = subtypes
		,global_id = global_id
		,editor_tracking = editor_tracking
		,archiving = archiving
		,attachments = attachments
		,privileges = privileges
		,indent_level = indent_level
	)



def create_table_temperaturemeasurement(
	gdb
	,indent_level = 0
):


	# Configuration

	table_name = 'TemperatureMeasurement'
	alias = 'Temperature Measurement'

	global_id = True
	editor_tracking = True
	archiving = True
	attachments = False

	table = os.path.join(
		gdb
		,table_name
	)

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('MeasureDate'			,'DATE'		,None		,None	,None		,'Measurement Date'		,True		,False		,None					,None)
		,('ReadingType'			,'TEXT'		,None		,None	,32		,'Reading Type'			,True		,False		,'Reading Type'				,None)
		,('SerialNumber'		,'TEXT'		,None		,None	,32		,'Serial Number'		,True		,False		,'Temperature Serial Number'		,None)
		,('ManualLevel'			,'DOUBLE'	,38		,2	,None		,'Manual Measurement'		,True		,False		,None					,None)
		,('SensorLevel'			,'DOUBLE'	,38		,2	,None		,'Realtime Sensor Level'	,True		,False		,None					,None)
		,('SensorSource'		,'TEXT'		,None		,None	,32		,'Sensor Source'		,True		,False		,'Temperature Source'			,None)
		,('SensorFailed'		,'TEXT'		,None		,None	,3		,'Sensor Failed'		,True		,False		,'Yes/No'				,None)
		,('LocationVisitGlobalID'	,'GUID'		,None		,None	,None		,'Related Location Visit'	,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user		read		write
		('HQ\\arcgis'	,'GRANT'	,'GRANT')
		,
	)



	# Create table

	mg.create_table(
		gdb = gdb
		,table_name = table_name
		,alias = alias
		,attributes = attributes
		,subtypes = subtypes
		,global_id = global_id
		,editor_tracking = editor_tracking
		,archiving = archiving
		,attachments = attachments
		,privileges = privileges
		,indent_level = indent_level
	)



####################
# Relationship Classes
####################

def create_rcs(
	gdb
	,indent_level = 0
):

	properties = (
		#origin table		destination table		name						type		forward label			backward label		message direction	cardinality		attributed	origin PK	origin FK			destination PK	destination FK		attributes
		('DataLogger'		,'Sensor'			,'DataLogger_Sensor'				,'SIMPLE'	,'Sensor'			,'Data Logger'		,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'DataLoggerGlobalID'		,None		,None			,None)
		,('Location'		,'DataLogger'			,'Location__DataLogger'				,'SIMPLE'	,'Data Logger'			,'Location'		,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'LocationGlobalID'		,None		,None			,None)
		,('Location'		,'LocationVisit'		,'Location__LocationVisit'			,'SIMPLE'	,'Location Visit'		,'Location'		,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'LocationGlobalID'		,None		,None			,None)
		,('Location'		,'MeasuringPoint'		,'Location__MeasuringPoint'			,'SIMPLE'	,'Measuring Point'		,'Location'		,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'LocationGlobalID'		,None		,None			,None)
		,('LocationVisit'	,'LocationIssue'		,'LocationVisit__LocationIssue'			,'SIMPLE'	,'Location Issue'		,'Location Visit'	,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'LocationVisitGlobalID'	,None		,None			,None)
		,('LocationVisit'	,'RainfallTips'			,'LocationVisit__RainfallTips'			,'SIMPLE'	,'Rainfall Tips'		,'Location Visit'	,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'LocationVisitGlobalID'	,None		,None			,None)
		,('LocationVisit'	,'StageMeasurement'		,'LocationVisit__StageMeasurement'		,'SIMPLE'	,'Stage Measurement'		,'Location Visit'	,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'LocationVisitGlobalID'	,None		,None			,None)
		,('LocationVisit'	,'GroundwaterMeasurement'	,'LocationVisit__GroundwaterMeasurement'	,'SIMPLE'	,'Groundwater Measurement'	,'Location Visit'	,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'LocationVisitGlobalID'	,None		,None			,None)
		,('LocationVisit'	,'ConductivityMeasurement'	,'LocationVisit__ConductivityMeasurement'	,'SIMPLE'	,'Conductivity Measurement'	,'Location Visit'	,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'LocationVisitGlobalID'	,None		,None			,None)
		,('LocationVisit'	,'TemperatureMeasurement'	,'LocationVisit__TemperatureMeasurement'	,'SIMPLE'	,'Temperature Measurement'	,'Location Visit'	,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'LocationVisitGlobalID'	,None		,None			,None)
		,('MeasuringPoint'	,'GroundwaterMeasurement'	,'MeasuringPoint__GroundwaterMeasurement'	,'SIMPLE'	,'Groundwater Measurement'	,'Measuring Point'	,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'MeasuringPointGlobalID'	,None		,None			,None)
		,('MeasuringPoint'	,'StageMeasurement'		,'MeasuringPoint__StageMeasurement'		,'SIMPLE'	,'Stage Measurement'		,'Measuring Point'	,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'MeasuringPointGlobalID'	,None		,None			,None)
	)



	for rc in properties:
	
		mg.create_rc(
			gdb = gdb
			,origin_table_name = rc[0]
			,destination_table_name = rc[1]
			,rc_name = rc[2]
			,rc_type = rc[3]
			,forward_label = rc[4]
			,backward_label = rc[5]
			,message_direction = rc[6]
			,cardinality = rc[7]
			,attributed = rc[8]
			,origin_pk = rc[9]
			,origin_fk = rc[10]
			,destination_pk = rc[11]
			,destination_fk = rc[12]
			,attributes = rc[13]
			,indent_level = indent_level
		)



################################################################################
# Utility functions
################################################################################


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
		,description = 'Deploy hydrologic monitoring data model to a geodatabase'
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
		'-d'
		,'--disable-domains'
		,dest = 'disable_domains'
		,help = 'Disable domain creation (for development/debugging)'
		,action = 'store_true'
	)

	g.add_argument(
		'-h'
		,'--help'
		,action = 'help'
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

	Returns formatter, for use with other handlers.
	'''


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



def _print_banner(
	args
):
	'''
	Print banner containing argument information to log
	'''

	banner = (
		f'{mg.BANNER_DELIMITER_1}\n'
		f'Hydrologic Data Model Geodatabase Deployment\n'
		f'{mg.BANNER_DELIMITER_2}\n'
		f'Target database server:  {args.server}\n'
		f'Log level:               {args.log_level}\n'
		f'Log file:                {args.log_file_name}\n'
		f'Disable domain creation: {args.disable_domains}\n'
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



	#
	# Return
	#

	return args



################################################################################
# Main
################################################################################

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

		args = _process_arguments(log_formatter)


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
	# Create domains
	#

	if args.disable_domains:

		logging.warning(
			'Domain creation is disabled; use the output model for\n'
			'*** TESTING PURPOSES ONLY ***'
		)


	else:

		logging.info('Creating domains')

		create_domains(
			gdb = gdb
			,indent_level = 1
		)



	#
	# Create feature classes
	#

	logging.info('Creating feature classes')

	create_fcs(
		gdb = gdb
		,indent_level = 1
	)



	#
	# Create attribute tables
	#

	logging.info('Creating attribute tables')

	create_tables(
		gdb = gdb
		,indent_level = 1
	)



	#
	# Create relationship classes
	#

	logging.info('Creating relationship classes')

	create_rcs(
		gdb = gdb
		,indent_level = 1
	)



	#
	# Cleanup
	#

	logging.info('Done.')



################################################################################
# END
################################################################################
