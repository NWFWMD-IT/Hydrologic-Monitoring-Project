################################################################################
# Name:
#	update_database_hydro.2.py
#
# Purpose:
#	Update existing geodatabase to:
#
#		- Add column `LocationIssue.IsActive` (#202)
#		- Add column `LocationLastVisit.IssueCount` (#202)
#		- Delete column `RainfallTips.FalseTipRemoved` (#222)
#
# Environment:
#	ArcGIS Pro 3.4.2
#	Python 3.11.10, with:
#		arcpy 3.4 (build py311_arcgispro_55347)
#
# Notes:
#	This script connects to the target `hydro` database using Windows
#	authentication. You must run this script from a Python session running
#	as the Windows `sde` user on which the database `sde` user is based.
#
# History:
#	2025-04-25 MCM Created
#
# To do:
#	none
#
# Copyright 2003-2025. Mannion Geosystems, LLC. http://www.manniongeo.com
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
import create_hydro_data_model
import mg



################################################################################
# Schema change functions
################################################################################

def update_table_locationissue(
	gdb
	,indent_level = 0
):

	table = os.path.join(
		gdb
		,'LocationIssue'
	)
	
	
	
	#
	# Add column
	#
	
	logging.info(
		'Adding columns'
		,extra = {'indent_level': indent_level}
	)
	

	attributes = (
		#name				,type		,precision	,scale	,length		,alias				,nullable	,required	,domain					,default
		('IsActive'			,'TEXT'		,None		,None	,3		,'Is Active'			,True		,False		,'Yes/No'				,'Yes')
		,
	)
	
	
	mg.add_fields(
		table = table
		,fields_spec = attributes
		,indent_level = indent_level + 1
	)



def update_table_locationvisit(
	gdb
	,indent_level = 0
):

	table = os.path.join(
		gdb
		,'LocationVisit'
	)
	
	

	#
	# Drop columns
	#
	
	logging.info(
		'Dropping columns'
		,extra = {'indent_level': indent_level}
	)
	
	
	
	logging.info(
		'BatteryNeedsReplacement'
		,extra = {'indent_level': indent_level + 1}
	)
	
	arcpy.management.DeleteField(
		in_table = table
		,drop_field = 'BatteryNeedsReplacement'
		,method = 'DELETE_FIELDS'
	)



def update_table_rainfalltips(
	gdb
	,indent_level = 0
):

	table = os.path.join(
		gdb
		,'RainfallTips'
	)
	
	

	#
	# Drop columns
	#
	
	logging.info(
		'Dropping columns'
		,extra = {'indent_level': indent_level}
	)
	
	
	
	logging.info(
		'FalseTipRemoved'
		,extra = {'indent_level': indent_level + 1}
	)
	
	arcpy.management.DeleteField(
		in_table = table
		,drop_field = 'FalseTipRemoved'
		,method = 'DELETE_FIELDS'
	)



def update_view_locationlastvisit(
	gdb
	,indent_level = 0
):

	view = os.path.join(
		gdb
		,'LocationLastVisit'
	)
	
	
	
	#
	# Drop view
	#
	
	logging.info(
		'Dropping view'
		,extra = {'indent_level': indent_level}
	)

	arcpy.management.Delete(
		in_data = view
	)
	
	
	
	#
	# Create view
	#
	
	logging.info(
		'Creating view'
		,extra = {'indent_level': indent_level}
	)
	
	create_hydro_data_model.create_view_locationlastvisit(
		gdb = gdb
		,indent_level = indent_level + 1
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
		,description = 'Update hydrologic monitoring geodatabase with schema changeset 2'
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
	
	
	if domain.upper() in ( # Development Windows Workgroup
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
		f'Hydrologic Data Model Geodatabase Update 2\n'
		f'{mg.BANNER_DELIMITER_2}\n'
		f'Target database server:  {args.server}\n'
		f'Log level:               {args.log_level}\n'
		f'Log file:                {args.log_file_name}\n'
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
	# Update tables
	#
	
	
	# LocationIssue
	
	logging.info('Updating table: LocationIssue')
	
	update_table_locationissue(
		gdb = gdb
		,indent_level = 1
	)
	
	
	
	# LocationVisit
	
	logging.info('Updating table: LocationVisit')
	
	update_table_locationvisit(
		gdb = gdb
		,indent_level = 1
	)
	
	
	
	# RainfallTips
	
	logging.info('Updating table: RainfallTips')
	
	update_table_rainfalltips(
		gdb = gdb
		,indent_level = 1
	)



	#
	# Update Views
	#
	
	
	# LocationLastVisit
	
	update_view_locationlastvisit(
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

