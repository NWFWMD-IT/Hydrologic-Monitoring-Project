################################################################################
# Name:
#	enable_geodatabase_hydro.py
#
# Purpose:
#	Enable geodatabae functionality in the [hydro] database
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
#	2022-07-18 MCM Created
#	2022-09-18 MCM Switched to OS authentication (Hydro 17/18)
#	2022-12-14 MCM Moved literals to constant OS_USERNAMES
#	2023-02-22 MCM Moved constants to constants.py
#	2023-03-13 MCM Replaced OS_USERNAMES_SDE with dynamic domain name
#	2025-07-13 MCM Add -d <database> argument to support development
#	                 infrastructure
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
import tempfile
import sys



# Custom

import constants as C
import mg



################################################################################
# Functions
################################################################################


#
# Public
#



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
	if user.upper() != 'SDE': # Only check user, not domain, so developers can run in arbitrary environment
	
		raise RuntimeError( # Error message is hardwired to HQ domain; developers can ignore domain name
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
		,description = 'Enable geodatabase features in the [hydro] geodatabase'
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
		'-d'
		,'--database'
		,dest = 'database'
		,help = 'SQL Server database name'
		,metavar = '<database>'
		,required = True
	)

	g.add_argument(
		'-a'
		,'--authorization-file'
		,dest = 'auth_file'
		,help = 'Authorization file'
		,metavar = '<auth_file>'
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
		'-h'
		,'--help'
		,action = 'help'
	)
	
	
	
	return ap
	


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
		f'Enable Geodatabase Features for [hydro] Database\n'
		f'{mg.BANNER_DELIMITER_2}\n'
		f'SQL Server hostname:     {args.server}\n'
		f'SQL Server database:     {args.database}\n'
		f'Authorization file:      {args.auth_file}\n'
		f'Log level:               {args.log_level}\n'
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
	
	
	
	#
	# Check Windows credentials
	#
	
	try:
	
		_check_credentials()
		
	
	except RuntimeError as e:
	
		logging.error(e)
		
		sys.exit(mg.EXIT_FAILURE)
		


	#
	# Enable geodatabase
	#
	
	with tempfile.TemporaryDirectory() as temp_dir:
	
		logging.debug(f'Temporary directory: {temp_dir}')
	
		logging.info('Creating database connection')
		arcpy.management.CreateDatabaseConnection(
			out_folder_path = temp_dir
			,out_name = C.CONNECTION_FILE_NAME
			,database_platform = 'SQL_SERVER'
			,instance = args.server
			,account_authentication = 'OPERATING_SYSTEM_AUTH'
			,database = args.database
		)
		
		
		gdb = os.path.join(
			temp_dir
			,C.CONNECTION_FILE_NAME
		)
		logging.debug(f'Connection file: {gdb}')



		logging.info('Enabling enterprise geodatabase')
		arcpy.management.EnableEnterpriseGeodatabase(
			input_database = gdb
			,authorization_file = args.auth_file
		)
	

	
	#
	# Cleanup
	#
	
	logging.info('Done.')



################################################################################
# END
################################################################################
