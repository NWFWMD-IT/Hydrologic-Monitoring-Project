################################################################################
# Name:
#	create_hydro_data_model.py
#
# Purpose:
#	Create geodatabase objects that compose the hydrologic monitoring data
#	model
#
# Environment:
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
import sys


# Custom

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
		'-g'
		,'--geodatabase'
		,dest = 'gdb'
		,help = 'Path to ArcGIS geodatabase connection file (.sde)'
		,metavar = '<geodatabase>'
		,required = True
	)
	
	g.add_argument(
		'-l'
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
		f'Target database:         {args.gdb}\n'
		f'Log level:               {args.log_level}\n'
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
	
	
	
	# Validate target geodatabase
	
	try:

		# Describe raises:
		#	IOError if target is not a recognized object type
		#	OSError if target does not exist

		d = arcpy.Describe(args.gdb)


		# Referencing workspaceType raises AttributeError if target is not a workspace

		if not d.workspaceType == u'RemoteDatabase':

			# Explicitly raise exception if target is not an enterprise geodatabase

			raise TypeError(f'Expected RemoteDatabase type; got {d.workspaceType} type')


	except (
		IOError
		,OSError
		,AttributeError
		,TypeError
	) as e:

		raise RuntimeError(f'Invalid enterprise geodatabase\n{e}')
	
	
	
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
	
	
	
	# Warn if domain creation is disabled
	
	if args.disable_domains:
	
		logging.warning(
			'Domain creation is disabled; use the output model for\n'
			'*** TESTING PURPOSES ONLY ***'
		)







	#
	# CREATE DATA MODEL
	#
	
	
	
	#
	# Cleanup
	#





################################################################################
# END
################################################################################
