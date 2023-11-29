################################################################################
# Name:
#	create_hydro_data_model.py
#
# Purpose:
#	Create geodatabase objects that compose the hydrologic monitoring data
#	model
#
# Environment:
#	ArcGIS Pro 3.2
#	Python 3.9.18, with:
#		arcpy 3.2 (build py39_arcgispro_49690)
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
#	2023-03-13 MCM Replaced OS_USERNAMES_SDE with dynamic domain name
#	               Removed attachments from DataLogger table (#70)
#	               Added Location Issue Type domain value (#71)
#	               Replaced static OS domain names with dynamic
#	2023-03-13 MCM Added comments columns for domains with "Other" values (#75)
#	               Added MeasuringPoint.IsActive column (#72)
#	2023-03-17 MCM Added LocationVisit.ADVMMaintenanceComments (#75)
#	               Added LocationVisit.ADVMDischargeRecordStart/End columns (#79)
#	               Corrected spelling of "desiccant" (#80)
#	2023-03-22 MCM Changed 'Incorrect inventory' to 'Update inventory' (#83)
#	               Added Location.FLUWID property (#84)
#	2023-04-17 MCM Added secondary battery / time columns (#94)
#	               Added DataLogger.LowVoltage (#89)
#	               Added MeasuringPoint.DisplayOrder (#86)
#	2023-05-18 MCM Removed 'Conductivity' value from Temperature Source domain (#68)
#	               Added StageMeasurement columns:
#	                 IsDischarge (#99)
#	                 ManualMethod / ManualMethodComments (#76)
#	               Added domain Stage Method (#76)
#	               Removed LocationVisit.DischargeStageStart/End (#99)
#	               Removed Location.HasADVMBattery column (#95)
#	               Removed LocationVisit.ADVMBattery* columns (#95)
#	2023-06-15 MCM Enhanced groundwater measurements (#77)
#	                 Added domain Groundwater Method
#	                 Added columns to GroundwaterMeasurement table:
#	                   ManualMethod
#	                   ManualMethodComments
#	                   ManualLevelHeld
#	                   ManualLevelWet
#	2023-06-20 MCM Changed Desiccant Maintenance domain value from
#	                 'Verified' to 'OK' (#106)
#	               Combined stage/groundwater desiccants into single
#	                 LocationVisit.DesiccantSensor column (#107)
#	2023-07-31 MCM Update domain values (#24)
#	2023-09-27 MCM Removed Hydro Staff domain (#124)
#	               Added LocationVisit.StaffComments column (#124)
#	2023-09-29 MCM Added `Location.HasSensor/MeasuringPoint` columns (#126)
#
# To do:
#	none
#
# Copyright 2003-2023. Mannion Geosystems, LLC. http://www.manniongeo.com
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
				('Other', 'Other')
				,
			)
		)
		,(
			'ADVM Beam Check Secondary Exception', 'TEXT', (
				('Did not clean', 'Did not clean')
				,('Other', 'Other')
			)
		)
		,(
			'ADVM Cleaned Exception', 'TEXT', (
				('No brush', 'No brush')
				,('Unable to pull ADVM', 'Unable to pull ADVM')
				,('Other', 'Other')
			)
		)
		,(
			'ADVM Maintenance', 'TEXT', (
				('Debris removed', 'Debris removed')
				,('Follow up - Maintenance', 'Follow up - Maintenance')
				,('Follow up - Remove debris', 'Follow up - Remove debris')
				,('Other', 'Other')
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
				('No standards', 'No standards')
				,('Sensor failed after calibration', 'Sensor failed after calibration')
				,('Unable to pull sensor', 'Unable to pull sensor')
				,('Other', 'Other')
			)
		)
		,(
			'Conductivity Serial Number', 'TEXT', (
				('252529', '252529')
				,('252531', '252531')
			)
		)
		,(
			'Conductivity Standard', 'LONG', (
				('100', '100')
				,('500', '500')
				,('1000', '1000')
				,('5000', '5000')
			)
		)
		,(
			'Data Logger Type', 'TEXT', (
				('High Sierra 3208', 'High Sierra 3208')
				,('In-Situ Level Troll 500', 'In-Situ Level Troll 500')
				,('In-Situ Level Troll 700', 'In-Situ Level Troll 700')
				,('In-Situ Rugged Baro Troll', 'In-Situ Rugged Baro Troll')
				,('In-Situ Rugged Troll 100', 'In-Situ Rugged Troll 100')
				,('Keller CTD', 'Keller CTD')
				,('Ott EcoLog1000', 'Ott EcoLog1000')
				,('Ott Orpheus Mini', 'Ott Orpheus Mini')
				,('Sontek Argonaut', 'Sontek Argonaut')
				,('Sutron 7310', 'Sutron 7310')
				,('Sutron 9210', 'Sutron 9210')
				,('Sutron CDMALink', 'Sutron CDMALink')
				,('Sutron SatLink Lite3', 'Sutron SatLink Lite3')
				,('Sutron SatLink3', 'Sutron SatLink3')
				,('Sutron XLink 100', 'Sutron XLink 100')
				,('Sutron XLink 500', 'Sutron XLink 500')
				,('WaterLog H500XL', 'WaterLog H500XL')
				,('WaterLog H522+', 'WaterLog H522+')
				,('WaterLog Storm3 ', 'WaterLog Storm3 ')
			)
		)
		,(
			'Desiccant Maintenance', 'TEXT', (
				('Verified', 'Verified')
				,('Replaced', 'Replaced')
				,('Needs replacement - No materials', 'Needs replacement - No materials')
				,('Other', 'Other')
			)
		)
		,(
			'Groundwater Adjustment Exception', 'TEXT', (
				('Before water quality sampling', 'Before water quality sampling')
				,('Cannot communicate with sensor', 'Cannot communicate with sensor')
				,('Low conductivity - No steel tape', 'Low conductivity - No steel tape')
				,('Safety', 'Safety')
				,('Weather', 'Weather')
				,('Other', 'Other')
			)
		)
		,(
			'Groundwater Method', 'TEXT', (
				('Electric tape', 'Electric tape')
				,('Steel tape', 'Steel tape')
				,('Piezo tube', 'Piezo tube')
				,('Other', 'Other')
			)
		)
		,(
			'Location Issue Type', 'TEXT', (
				('Transducer failure', 'Transducer failure')
				,('Data logger failure', 'Data logger failure')
				,('Follow up - Conduit adjustment/repair', 'Follow up - Conduit adjustment/repair')
				,('Invalid data - Battery change', 'Invalid data - Battery change')
				,('Invalid data - In-Situ low battery', 'Invalid data - In-Situ low battery')
				,('Invalid data - Station maintenance', 'Invalid data - Station maintenance')
				,('Inventory updated', 'Inventory updated')
				,('MP - Inaccessible due to high water', 'MP - Inaccessible due to high water')
				,('MP - Missing (washed away, etc.)', 'MP - Missing (washed away, etc.)')
				,('MP - No water at MP', 'MP - No water at MP')
				,('Solar panel damage', 'Solar panel damage')
				,('Vandalism - Data logger', 'Vandalism - Data logger')
				,('Vandalism - Enclosure', 'Vandalism - Enclosure')
				,('Vandalism - Solar panel', 'Vandalism - Solar panel')
				,('Vandalism - Transducer', 'Vandalism - Transducer')
				,('Other', 'Other')
			)
		)
		,(
			'Rainfall Exception', 'TEXT', (
				('Raining', 'Raining')
				,('No ladder', 'No ladder')
				,('Safety', 'Safety')
				,('Other', 'Other')
			)
		)
		,(
			'Reading Type', 'TEXT', (
				('Routine', 'Routine')
				,('Routine Before Sampling', 'Routine Before Sampling')
				,('Routine After Sampling', 'Routine After Sampling')
				,('After Calibration', 'After Calibration')
				,('Extreme - Min', 'Extreme - Min')
				,('Extreme - Max', 'Extreme - Max')
			)
		)
		,(
			'Sensor Type', 'TEXT', (
				('In-Situ Aqua Troll 500', 'In-Situ Aqua Troll 500')
				,('In-Situ Level Troll 500', 'In-Situ Level Troll 500')
				,('Keller Acculevel', 'Keller Acculevel')
				,('KPSI 500', 'KPSI 500')
				,('Ott PLS', 'Ott PLS')
				,('Ott PLS-C', 'Ott PLS-C')
				,('SonTek SL 1500', 'SonTek SL 1500')
				,('Sutron RLR', 'Sutron RLR')
				,('Teledyne Channel Master', 'Teledyne Channel Master')
				,('WaterLog Encoder H-3311', 'WaterLog Encoder H-3311')
				,('WaterLog Pulse Radar', 'WaterLog Pulse Radar')
			)
		)
		,(
			'Stage Adjustment Exception', 'TEXT', (
				('Cannot communicate with sensor', 'Cannot communicate with sensor')
				,('No water at transducer', 'No water at transducer')
				,('Safety', 'Safety')
				,('Weather', 'Weather')
				,('Wind', 'Wind')
				,('Other', 'Other')
			)
		)
		,(
			'Stage Method', 'TEXT', (
				('Staff', 'Staff')
				,('Tape up/down', 'Tape up/down')
				,('Wire weight', 'Wire weight')
				,('Other', 'Other')
			)
		)
		,(
			'Temperature Serial Number', 'TEXT', (
				('252529', '252529')
				,('252531', '252531')
				,('210843076', '210843076')
				,('210843093', '210843093')
				,('210910858', '210910858')
			)
		)
		,(
			'Temperature Source', 'TEXT', (
				('ADVM', 'ADVM')
				,('Transducer', 'Transducer')
			)
		)
		,(
			'Time Adjustment Exception', 'TEXT', (
				('Other', 'Other')
				,
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
		('NWFID'			,'TEXT'		,None		,None	,6		,'NWFID'			,True		,False		,None					,None)
		,('Name'			,'TEXT'		,None		,None	,128		,'Name'				,True		,False		,None					,None)
		,('Project'			,'LONG'		,None		,None	,None		,'Project Number'		,True		,False		,None					,None)
		,('FLUWID'			,'TEXT'		,None		,None	,16		,'FLUWID'			,True		,False		,None					,None)
		,('HasDataLogger'		,'TEXT'		,None		,None	,3		,'Has Data Logger'		,True		,False		,'Yes/No'				,None)
		,('HasSensor'			,'TEXT'		,None		,None	,3		,'Has Sensor'			,True		,False		,'Yes/No'				,None)
		,('HasMeasuringPoint'		,'TEXT'		,None		,None	,3		,'Has Measuring Point'		,True		,False		,'Yes/No'				,None)
		,('HasRainfall'			,'TEXT'		,None		,None	,3		,'Has Rainfall'			,True		,False		,'Yes/No'				,None)
		,('HasStage'			,'TEXT'		,None		,None	,3		,'Has Stage'			,True		,False		,'Yes/No'				,None)
		,('HasGroundwater'		,'TEXT'		,None		,None	,3		,'Has Groundwater'		,True		,False		,'Yes/No'				,None)
		,('HasConductivity'		,'TEXT'		,None		,None	,3		,'Has Conductivity'		,True		,False		,'Yes/No'				,None)
		,('HasADVM'			,'TEXT'		,None		,None	,3		,'Has ADVM'			,True		,False		,'Yes/No'				,None)
		,('HasDischarge'		,'TEXT'		,None		,None	,3		,'Has Discharge'		,True		,False		,'Yes/No'				,None)
		,('HasTemperature'		,'TEXT'		,None		,None	,3		,'Has Temperature'		,True		,False		,'Yes/No'				,None)
		,('HasWaterQuality'		,'TEXT'		,None		,None	,3		,'Has Water Quality'		,True		,False		,'Yes/No'				,None)
		,('Comments'			,'TEXT'		,None		,None	,1024		,'Comments'			,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user				read		write
		(f'{_get_domain()}\\arcgis'	,'GRANT'	,'GRANT')
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
		,('SensorAdjustmentDate'	,'DATE'		,None		,None	,None		,'Sensor Adjustment Date'	,True		,False		,None					,None)
		,('SensorAdjustmentException'	,'TEXT'		,None		,None	,32		,'Sensor Adjustment Exception'	,True		,False		,'Conductivity Adjustment Exception'	,None)
		,('SensorAdjustmentComments'	,'TEXT'		,None		,None	,1024		,'Sensor Adjustment Comments'	,True		,False		,None					,None)
		,('CalibrationStandard'		,'LONG'		,None		,None	,None		,'Calibration Standard'		,True		,False		,'Conductivity Standard'		,None)
		,('VerificationStandard'	,'LONG'		,None		,None	,None		,'Verification Standard'	,True		,False		,'Conductivity Standard'		,None)
		,('VerificationLevel'		,'LONG'		,None		,None	,None		,'Verification Sensor Level'	,True		,False		,None					,None)
		,('VerificationDate'		,'DATE'		,None		,None	,None		,'Verification Date'		,True		,False		,None					,None)
		,('LocationVisitGlobalID'	,'GUID'		,None		,None	,None		,'Related Location Visit'	,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user				read		write
		(f'{_get_domain()}\\arcgis'	,'GRANT'	,'GRANT')
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
	attachments = False

	table = os.path.join(
		gdb
		,table_name
	)

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('Type'				,'TEXT'		,None		,None	,64		,'Data Logger Type'		,True		,False		,'Data Logger Type'			,None)
		,('SerialNumber'		,'TEXT'		,None		,None	,32		,'Serial Number'		,True		,False		,None					,None)
		,('LowVoltage'			,'DOUBLE'	,38		,2	,None		,'Low Battery Limit (volts or percent)'	,True	,False		,None					,None)
		,('Comments'			,'TEXT'		,None		,None	,1024		,'Comments'			,True		,False		,None					,None)
		,('LocationGlobalID'		,'GUID'		,None		,None	,None		,'Related Location'		,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user				read		write
		(f'{_get_domain()}\\arcgis'	,'GRANT'	,'GRANT')
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
		,('ManualMethod'		,'TEXT'		,None		,None	,32		,'Manual Measurement Method'	,True		,False		,'Groundwater Method'			,None)
		,('ManualMethodComments'	,'TEXT'		,None		,None	,1024		,'Manual Measurement Method Comments'	,True	,False		,None					,None)
		,('ManualLevel'			,'DOUBLE'	,38		,2	,None		,'Manual Measurement (feet)'	,True		,False		,None					,None)
		,('ManualLevelHeld'		,'DOUBLE'	,38		,2	,None		,'Steel Tape Held At (feet)'	,True		,False		,None					,None)
		,('ManualLevelWet'		,'DOUBLE'	,38		,2	,None		,'Steel Tape Wet At (feet)'	,True		,False		,None					,None)
		,('WaterLevel'			,'DOUBLE'	,38		,2	,None		,'Computed Manual Water Level'	,True		,False		,None					,None)
		,('SensorLevel'			,'DOUBLE'	,38		,2	,None		,'Realtime Sensor Level'	,True		,False		,None					,None)
		,('SensorAdjustmentAmount'	,'DOUBLE'	,38		,2	,None		,'Sensor Adjustment Amount'	,True		,False		,None					,None)
		,('SensorAdjusted'		,'TEXT'		,None		,None	,3		,'Sensor Adjusted'		,True		,False		,'Yes/No'				,None)
		,('SensorAdjustmentDate'	,'DATE'		,None		,None	,None		,'Sensor Adjustment Date'	,True		,False		,None					,None)
		,('SensorAdjustmentException'	,'TEXT'		,None		,None	,32		,'Sensor Adjustment Exception'	,True		,False		,'Groundwater Adjustment Exception'	,None)
		,('SensorAdjustmentComments'	,'TEXT'		,None		,None	,1024		,'Sensor Adjustment Comments'	,True		,False		,None					,None)
		,('LocationVisitGlobalID'	,'GUID'		,None		,None	,None		,'Related Location Visit'	,True		,False		,None					,None)
		,('MeasuringPointGlobalID'	,'GUID'		,None		,None	,None		,'Related Measuring Point'	,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user				read		write
		(f'{_get_domain()}\\arcgis'	,'GRANT'	,'GRANT')
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
		('Type'				,'TEXT'		,None		,None	,64		,'Issue Type'			,True		,False		,'Location Issue Type'			,None)
		,('Comments'			,'TEXT'		,None		,None	,1024		,'Comments'			,True		,False		,None					,None)
		,('LocationVisitGlobalID'	,'GUID'		,None		,None	,None		,'Related Location Visit'	,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user				read		write
		(f'{_get_domain()}\\arcgis'	,'GRANT'	,'GRANT')
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
		,('Staff'				,'TEXT'		,None		,None	,1024		,'Visit Staff'				,True		,False		,None					,None)
		,('StaffComments'			,'TEXT'		,None		,None	,1024		,'Staff Comments'			,True		,False		,None					,None)
		,('InventoryVerified'			,'TEXT'		,None		,None	,3		,'Equipment Inventory Verified'		,True		,False		,'Yes/No'				,None)
		,('BatteryDOA'				,'TEXT'		,None		,None	,3		,'Battery DOA'				,True		,False		,'Yes/No'				,None)
		,('BatteryCondition'			,'TEXT'		,None		,None	,32		,'Battery Condition'			,True		,False		,'Battery Condition'			,None)
		,('BatteryVoltage'			,'DOUBLE'	,38		,2	,None		,'Battery Voltage'			,True		,False		,None					,None)
		,('BatteryCondition2'			,'TEXT'		,None		,None	,32		,'Battery Condition'			,True		,False		,'Battery Condition'			,None)
		,('BatteryVoltage2'			,'DOUBLE'	,38		,2	,None		,'Battery Voltage (new battery)'	,True		,False		,None					,None)
		,('BatteryReplaced'			,'TEXT'		,None		,None	,3		,'Battery Replaced (new battery)'	,True		,False		,'Yes/No'				,None)
		,('BatteryReplacementDate'		,'DATE'		,None		,None	,None		,'Battery Replacement Date'		,True		,False		,None					,None)
		,('BatteryReplacementException'		,'TEXT'		,None		,None	,32		,'Battery Replacement Exception'	,True		,False		,'Battery Replacement Exception'	,None)
		,('BatteryReplacementComments'		,'TEXT'		,None		,None	,1024		,'Battery Replacement Comments'		,True		,False		,None					,None)
		,('DesiccantEnclosure'			,'TEXT'		,None		,None	,32		,'Enclosure Desiccant'			,True		,False		,'Desiccant Maintenance'		,None)
		,('DesiccantSensor'			,'TEXT'		,None		,None	,32		,'Sensor Desiccant'			,True		,False		,'Desiccant Maintenance'		,None)
		,('DesiccantComments'			,'TEXT'		,None		,None	,1024		,'Desiccant Comments'			,True		,False		,None					,None)
		,('DataLoggerRecordStart'		,'DATE'		,None		,None	,None		,'Data Logger Record Start'		,True		,False		,None					,None)
		,('DataLoggerRecordEnd'			,'DATE'		,None		,None	,None		,'Data Logger Record End'		,True		,False		,None					,None)
		,('DataLoggerTime'			,'DATE'		,None		,None	,None		,'Data Logger Clock Time'		,True		,False		,None					,None)
		,('DataLoggerTimeActual'		,'DATE'		,None		,None	,None		,'Correct Current Time'			,True		,False		,None					,None)
		,('DataLoggerTimeAdjAmount'		,'LONG'		,None		,None	,None		,'Data Logger Time Adjustment (minutes)'	,True	,False		,None					,None)
		,('DataLoggerTimeAdjusted'		,'TEXT'		,None		,None	,3		,'Data Logger Time Adjusted'		,True		,False		,'Yes/No'				,None)
		,('DataLoggerTimeAdjDate'		,'DATE'		,None		,None	,None		,'Data Logger Time Adjustment Date'	,True		,False		,None					,None)
		,('DataLoggerTimeAdjException'		,'TEXT'		,None		,None	,32		,'Data Logger Time Adjustment Exception'	,True	,False		,'Time Adjustment Exception'		,None)
		,('DataLoggerTimeAdjComments'		,'TEXT'		,None		,None	,1024		,'Data Logger Time Adjustment Comments'	,True		,False		,None					,None)
		,('DataLoggerTime2'			,'DATE'		,None		,None	,None		,'Data Logger Clock Time (new battery)'	,True		,False		,None					,None)
		,('DataLoggerTimeActual2'		,'DATE'		,None		,None	,None		,'Correct Current Time (new battery)'	,True		,False		,None					,None)
		,('DataLoggerTimeAdjAmount2'		,'LONG'		,None		,None	,None		,'Data Logger Time Adjustment (minutes; new battery)'	,True	,False	,None					,None)
		,('DataLoggerTimeAdjusted2'		,'TEXT'		,None		,None	,3		,'Data Logger Time Adjusted (new battery)'	,True	,False		,'Yes/No'				,None)
		,('DataLoggerTimeAdjDate2'		,'DATE'		,None		,None	,None		,'Data Logger Time Adjustment Date (new battery)'	,True	,False	,None					,None)
		,('DataLoggerTimeAdjException2'		,'TEXT'		,None		,None	,32		,'Data Logger Time Adjustment Exception (new battery)'	,True	,False	,'Time Adjustment Exception'		,None)
		,('DataLoggerTimeAdjComments2'		,'TEXT'		,None		,None	,1024		,'Data Logger Time Adjustment Comments (new battery)'	,True	,False	,None					,None)
		,('RainfallBucketCleaned'		,'TEXT'		,None		,None	,3		,'Rainfall Bucket Cleaned'		,True		,False		,'Yes/No'				,None)
		,('RainfallBucketException'		,'TEXT'		,None		,None	,32		,'Rainfall Bucket Exception'		,True		,False		,'Rainfall Exception'			,None)
		,('RainfallBucketComments'		,'TEXT'		,None		,None	,1024		,'Rainfall Bucket Comments'		,True		,False		,None					,None)
		,('RainfallMechanismChecked'		,'TEXT'		,None		,None	,3		,'Tipping Mechanism Checked'		,True		,False		,'Yes/No'				,None)
		,('RainfallMechanismException'		,'TEXT'		,None		,None	,32		,'Tipping Mechanism Exception'		,True		,False		,'Rainfall Exception'			,None)
		,('RainfallMechanismComments'		,'TEXT'		,None		,None	,1024		,'Rainfall Mechanism Comments'		,True		,False		,None					,None)
		,('ADVMRecordStart'			,'DATE'		,None		,None	,None		,'ADVM Record Start'			,True		,False		,None					,None)
		,('ADVMRecordEnd'			,'DATE'		,None		,None	,None		,'ADVM Record End'			,True		,False		,None					,None)
		,('ADVMDischarge RecordStart'		,'DATE'		,None		,None	,None		,'ADVM Discharge Record Start'		,True		,False		,None					,None)
		,('ADVMDischarge RecordEnd'		,'DATE'		,None		,None	,None		,'ADVM Discharge Record End'		,True		,False		,None					,None)
		,('ADVMBeamCheckedInitial'		,'TEXT'		,None		,None	,3		,'ADVM Initial Beam Checked'		,True		,False		,'Yes/No'				,None)
		,('ADVMBeamCheckInitialException'	,'TEXT'		,None		,None	,32		,'ADVM Initial Beam Check Exception'	,True		,False		,'ADVM Beam Check Initial Exception'	,None)
		,('ADVMBeamCheckInitialComments'	,'TEXT'		,None		,None	,1024		,'ADVM Initial Beam Check Comments'	,True		,False		,None					,None)
		,('ADVMBeamCheckedSecondary'		,'TEXT'		,None		,None	,3		,'ADVM Secondary Beam Checked'		,True		,False		,'Yes/No'				,None)
		,('ADVMBeamCheckSecondaryException'	,'TEXT'		,None		,None	,32		,'ADVM Secondary Beam Check Exception'	,True		,False		,'ADVM Beam Check Secondary Exception'	,None)
		,('ADVMBeamCheckSecondaryComments'	,'TEXT'		,None		,None	,1024		,'ADVM Secondary Beam Check Comments'	,True		,False		,None					,None)
		,('ADVMCleaned'				,'TEXT'		,None		,None	,3		,'ADVM Cleaned'				,True		,False		,'Yes/No'				,None)
		,('ADVMCleanedException'		,'TEXT'		,None		,None	,32		,'ADVM Cleaned Exception'		,True		,False		,'ADVM Cleaned Exception'		,None)
		,('ADVMCleanedComments'			,'TEXT'		,None		,None	,1024		,'ADVM Cleaned Comments'		,True		,False		,None					,None)
		,('ADVMMaintenance'			,'TEXT'		,None		,None	,32		,'ADVM Additional Maintenace'		,True		,False		,'ADVM Maintenance'			,None)
		,('ADVMMaintenanceComments'		,'TEXT'		,None		,None	,1024		,'ADVM Maintenance Comments'		,True		,False		,None					,None)
		,('DischargeRecordStart'		,'DATE'		,None		,None	,None		,'Discharge Record Start'		,True		,False		,None					,None)
		,('DischargeRecordEnd'			,'DATE'		,None		,None	,None		,'Discharge Record End'			,True		,False		,None					,None)
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
		#user				read		write
		(f'{_get_domain()}\\arcgis'	,'GRANT'	,'GRANT')
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
		('Name'				,'TEXT'		,None		,None	,64		,'Name'				,True		,False		,None					,None)
		,('AquariusID'			,'GUID'		,None		,None	,None		,'Aquarius ID'			,True		,False		,None					,None)
		,('Description'			,'TEXT'		,None		,None	,1024		,'Description'			,True		,False		,None					,None)
		,('Elevation'			,'DOUBLE'	,38		,2	,None		,'Elevation'			,True		,False		,None					,None)
		,('IsActive'			,'TEXT'		,None		,None	,3		,'Is Active'			,True		,False		,'Yes/No'				,None)
		,('DisplayOrder'		,'LONG'		,None		,None	,None		,'Display Order'		,True		,False		,None					,None)
		,('Comments'			,'TEXT'		,None		,None	,1024		,'Comments'			,True		,False		,None					,None)
		,('LocationGlobalID'		,'GUID'		,None		,None	,None		,'Related Location'		,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user				read		write
		(f'{_get_domain()}\\arcgis'	,'GRANT'	,'GRANT')
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
		#user				read		write
		(f'{_get_domain()}\\arcgis'	,'GRANT'	,'GRANT')
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
		('Type'				,'TEXT'		,None		,None	,32		,'Sensor Type'			,True		,False		,'Sensor Type'				,None)
		,('SerialNumber'		,'TEXT'		,None		,None	,32		,'Serial Number'		,True		,False		,None					,None)
		,('Comments'			,'TEXT'		,None		,None	,1024		,'Comments'			,True		,False		,None					,None)
		,('DataLoggerGlobalID'		,'GUID'		,None		,None	,None		,'Related Data Logger'		,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user				read		write
		(f'{_get_domain()}\\arcgis'	,'GRANT'	,'GRANT')
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
		,('IsDischarge'			,'TEXT'		,None		,None	,3		,'Discharge Related'		,True		,False		,'Yes/No'				,None)
		,('ManualMethod'		,'TEXT'		,None		,None	,32		,'Manual Measurement Method'	,True		,False		,'Stage Method'				,None)
		,('ManualMethodComments'	,'TEXT'		,None		,None	,1024		,'Manual Measurement Method Comments'	,True	,False		,None					,None)
		,('ManualLevel'			,'DOUBLE'	,38		,2	,None		,'Manual Measurement (feet)'	,True		,False		,None					,None)
		,('WaterLevel'			,'DOUBLE'	,38		,2	,None		,'Computed Manual Water Level'	,True		,False		,None					,None)
		,('SensorLevel'			,'DOUBLE'	,38		,2	,None		,'Realtime Sensor Level'	,True		,False		,None					,None)
		,('SensorAdjustmentAmount'	,'DOUBLE'	,38		,2	,None		,'Sensor Adjustment Amount'	,True		,False		,None					,None)
		,('SensorAdjusted'		,'TEXT'		,None		,None	,3		,'Sensor Adjusted'		,True		,False		,'Yes/No'				,None)
		,('SensorAdjustmentDate'	,'DATE'		,None		,None	,None		,'Sensor Adjustment Date'	,True		,False		,None					,None)
		,('SensorAdjustmentException'	,'TEXT'		,None		,None	,32		,'Sensor Adjustment Exception'	,True		,False		,'Stage Adjustment Exception'		,None)
		,('SensorAdjustmentComments'	,'TEXT'		,None		,None	,1024		,'Sensor Adjustment Comments'	,True		,False		,None					,None)
		,('LocationVisitGlobalID'	,'GUID'		,None		,None	,None		,'Related Location Visit'	,True		,False		,None					,None)
		,('MeasuringPointGlobalID'	,'GUID'		,None		,None	,None		,'Related Measuring Point'	,True		,False		,None					,None)
	)

	subtypes = None

	privileges = (
		#user				read		write
		(f'{_get_domain()}\\arcgis'	,'GRANT'	,'GRANT')
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
		#user				read		write
		(f'{_get_domain()}\\arcgis'	,'GRANT'	,'GRANT')
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
	if user.upper() != 'HYDRO': # Only check user, not domain, so developers can run in arbitrary environment
	
		raise RuntimeError( # Error message is hardwired to HQ domain; developers can ignore domain name
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
	


def _get_domain():

	domain = os.environ['USERDOMAIN']
	
	
	if domain in ( # Development Windows Workgroup
		'APOLLO'
		,'CITRA'
		,'PORTER'
		,'STOUT'
	):
	
		return 'CITRA'
		
		
	else:
	
		return domain
		
	
	
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
