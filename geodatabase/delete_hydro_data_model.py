################################################################################
# Name:
#	delete_hydro_data_model.py
#
# Purpose:
#	Delete geodatabase objects that compose the hydrologic monitoring data
#	model
#
# Environment:
#	ArcGIS Pro 3.0.1
#	Python 3.9.11, with:
#		arcpy 3.0 (build py39_arcgispro_36045)
#
# Notes:
#	This script is designed to facilitate model deployment development by
#	allowing developers to partially delete the model before attempting to
#	recreate it. This saves time during frequent testing cycles compared to
#	executing a full deployment workflow, which includes creating the SQL
#	Server database and principals; enabling the geodatabase; and creating
#	all model objects.
#
#	In particular, this script includes a command line option to preserve
#	domains while deleting other model objects. Domain creation is
#	relatively slow because of the granular interface that arcpy provides
#	(e.g. separate call to add each coded domain value). Domains also tend
#	to be more stable than other geodatabase objects during the development
#	process, so preserving them while recreating more complex objects like
#	feature classes is common.
#
#	Additionally, developers can selectively comment in/out relevant code
#	here to target individual objects or object types.
#
# History:
#	2022-07-18 MCM Created
#	2022-09-18 MCM Switched to OS authentication (Hydro 17/18)
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
import datetime
import logging
import os
import sys
import tempfile


# Custom

import mg



#
# Constants
#


# General

CONNECTION_FILE_NAME = 'connection.sde'



# Geodatabase object names

ATTACHMENT_TABLE_NAMES = (
	'Location_ATTACH'
	,
)

ATTRIBUTE_TABLE_NAMES = (
	'ConductivityMeasurement'
	,'DataLogger'
	,'GroundwaterMeasurement'
	,'LocationIssue'
	,'LocationVisit'
	,'MeasuringPoint'
	,'RainfallTips'
	,'Sensor'
	,'StageMeasurement'
	,'TemperatureMeasurement'
	,'VisitStaff'
)

DOMAIN_NAMES = (
	'ADVM Beam Check Initial Exception'
	,'ADVM Beam Check Secondary Exception'
	,'ADVM Cleaned Exception'
	,'ADVM Maintenance'
	,'Battery Condition'
	,'Battery Replacement Exception'
	,'Conductivity Adjustment Exception'
	,'Conductivity Serial Number'
	,'Conductivity Standard'
	,'Data Logger Type'
	,'Dessicant Maintenance'
	,'Groundwater Adjustment Exception'
	,'Hydro Staff'
	,'Location Issue Type'
	,'Rainfall Exception'
	,'Reading Type'
	,'Sensor Type'
	,'Stage Adjustment Exception'
	,'Temperature Serial Number'
	,'Temperature Source'
	,'Temperature Units'
	,'Time Adjustment Type'
	,'Yes/No'
	# Obsolete
	,'Battery Replacement Time Adjustment'
)

FC_NAMES = (
	'Location'
	,
)

HISTORY_TABLE_NAMES = (
	'Location_H'
	,
)



################################################################################
# Object deletion functions
################################################################################

def delete_domains(
	gdb
	,domain_names # tuple
	,indent_level = 0
):

	for domain_name in domain_names:
	
		try:
		
			logging.info(
				domain_name
				,extra = {'indent_level': indent_level}
			)
			
			r = arcpy.management.DeleteDomain(
				in_workspace = gdb
				,domain_name = domain_name
			)
			
			
			if r.maxSeverity > 0:
			
				logging.error(
					f'Failed to delete with message:\n{r.getMessages()}'
					,extra = {'indent_level': indent_level + 1}
				)
				
				
		except Exception as e:
			
				logging.error(
					f'Failed to delete with message:\n{e}'
					,extra = {'indent_level': indent_level + 1}
				)




def delete_fcs(
	gdb
	,fc_names # tuple
	,indent_level = 0
):

	for fc_name in fc_names:
	
		fc = os.path.join(
			gdb
			,fc_name
		)
		
		
	
		try:
		
			logging.info(
				fc_name
				,extra = {'indent_level': indent_level}
			)
			
			r = arcpy.management.Delete(
				in_data = fc
				,data_type = 'FeatureClass'
			)
			
			
			if r.maxSeverity > 0:
			
				logging.error(
					f'Failed to delete with message:\n{r.getMessages()}'
					,extra = {'indent_level': indent_level + 1}
				)
				
				
		except Exception as e:
			
				logging.error(
					f'Failed to delete with message:\n{e}'
					,extra = {'indent_level': indent_level + 1}
				)




def delete_tables(
	gdb
	,table_names # tuple
	,indent_level = 0
):

	for table_name in table_names:
	
		table = os.path.join(
			gdb
			,table_name
		)
		
		
	
		try:
		
			logging.info(
				table_name
				,extra = {'indent_level': indent_level}
			)
			
			r = arcpy.management.Delete(
				in_data = table
				,data_type = 'Table'
			)
			
			
			if r.maxSeverity > 0:
			
				logging.error(
					f'Failed to delete with message:\n{r.getMessages()}'
					,extra = {'indent_level': indent_level + 1}
				)
				
				
		except Exception as e:
			
				logging.error(
					f'Failed to delete with message:\n{e}'
					,extra = {'indent_level': indent_level + 1}
				)




################################################################################
# Utility functions
################################################################################


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
	
	
	
	if not username.upper() in (
		'HQ\HYDRO' # NWFWMD production
		,'CITRA\HYDRO' # MannionGeo development
		,'PORTER\HYDRO' # MannionGeo development
	):
	
		raise RuntimeError(
			'Invalid Windows credentials'
			f'\nThis script must run in a Python session as the HQ\sde user, but is running as {username}'
		)



def _configure_arguments():
	'''
	Configure arguments when running in script mode
	
	Returns configured argparse.ArgumentParser
	'''

	ap = argparse.ArgumentParser(
		conflict_handler = 'resolve' # Allow overwriting built-in -h/--help to add to custom argument group
		,description = 'Delete hydrologic monitoring data model from a geodatabase'
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
		,'--keep-domains'
		,dest = 'keep_domains'
		,help = 'Do not delete domains'
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
		,out_name = CONNECTION_FILE_NAME
		,database_platform = 'SQL_SERVER'
		,instance = server
		,account_authentication = 'OPERATING_SYSTEM_AUTH'
		,database = 'hydro'
	)
	
	
	gdb = os.path.join(
		temp_dir.name
		,CONNECTION_FILE_NAME
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
		f'Hydrologic Data Model Deletion\n'
		f'{mg.BANNER_DELIMITER_2}\n'
		f'Target database server:  {args.server}\n'
		f'Log level:               {args.log_level}\n'
		f'Keep domains:            {args.keep_domains}\n'
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
	# Delete feature classes
	#
	
	logging.info('Deleting feature classes')
	
	delete_fcs(
		gdb = gdb
		,fc_names = FC_NAMES
		,indent_level = 1
	)


	
	#
	# Delete attribute tables
	#
	
	logging.info('Deleting attribute tables')
	
	delete_tables(
		gdb = gdb
		,table_names = ATTRIBUTE_TABLE_NAMES
		,indent_level = 1
	)
	
	
	
	#
	# Delete domains
	#
	
	if args.keep_domains:
	
		logging.warning(
			'Skipping domains'
		)
		
	
	else:
	
		logging.info('Deleting domains')

		delete_domains(
			gdb = gdb
			,domain_names = DOMAIN_NAMES
			,indent_level = 1
		)
	

	
	#
	# Cleanup
	#

	logging.info('Done.')




################################################################################
# END
################################################################################
