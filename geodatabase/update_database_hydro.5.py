################################################################################
# Name:
#	update_database_hydro.5.py
#
# Purpose:
#	Update existing geodatabase to:
#		Move discharge data to a separate table (#237)
#
# Environment:
#	ArcGIS Pro 3.4.2
#	Python 3.11.10, with:
#		arcpy 3.4 (build py311_arcgispro_55347)
#
# Notes:
#	This script connects to the target `hydro` database using Windows
#	authentication. You must run this script from a Python session running
#	as the Windows user `hydro` on which the database user `hydro` is based.
#
# History:
#	2025-07-13 MCM Created
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
import json
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

def create_table_dischargemeasurement(
	gdb
	,indent_level = 0
):


	# Configuration

	table_name = 'DischargeMeasurement'
	alias = 'Discharge Measurement'

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
		('RecordStart'			,'DATE'		,None		,None	,None		,'Discharge Record Start'	,True		,False		,None					,None)
		,('RecordEnd'			,'DATE'		,None		,None	,None		,'Discharge Record End'		,True		,False		,None					,None)
		,('Volume'			,'DOUBLE'	,38		,2	,None		,'Discharge Volume'		,True		,False		,None					,None)
		,('Uncertainty'			,'DOUBLE'	,38		,2	,None		,'Discharge Uncertainty'	,True		,False		,None					,None)
		,('IsReviewed'			,'TEXT'		,None		,None	,3		,'Is Reviewed'			,True		,False		,'Yes/No'				,'Yes')
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
	
	
def create_rcs(
	gdb
	,indent_level = 0
):

	properties = (
		#origin table		destination table		name						type		forward label			backward label		message direction	cardinality		attributed	origin PK	origin FK			destination PK	destination FK		attributes
		('LocationVisit'	,'DischargeMeasurement'		,'LocationVisit_DischargeMeasurement'		,'SIMPLE'	,'Discharge Measurement'	,'Location Visit'	,'NONE'			,'ONE_TO_MANY'		,'NONE'		,'GlobalID'	,'LocationVisitGlobalID'	,None		,None			,None)
		,
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



def delete_fields_discharge(
	gdb
	,indent_level = 0
):

	table = os.path.join(
		gdb
		,'LocationVisit'
	)
	
	
	arcpy.management.DeleteField(
		in_table = table
		,drop_field = (
			'DischargeRecordStart'
			,'DischargeRecordEnd'
			,'DischargeVolume'
			,'DischargeUncertainty'
		)
	)



def delete_view_locationlastvisit(
	gdb
	,indent_level = 0
):

	view = os.path.join(
		gdb
		,'LocationLastVisit'
	)


	arcpy.management.Delete(
		in_data = view
	)
	


def migrate_data_discharge(
	gdb
	,indent_level = 0
):

	table_target = os.path.join(
		gdb
		,'DischargeMeasurement'
	)
	
	table_target_attach = os.path.join(
		gdb
		,'DischargeMeasurement__ATTACH'
	)
	
	table_source = os.path.join(
		gdb
		,'LocationVisit_EVW'
	)
	
	# We search the table instead of the multiversioned view because the
	# view does not include the EXIFINFO column. The SearchCursor will
	# include the approprite archive filter.
	
	table_source_attach = os.path.join(
		gdb
		,'LocationVisit__ATTACH'
	)
	
	
	
	# Create geodatabase editor for transaction control
	
	logging.info(
		'Creating geodatabase editor'
		,extra = {'indent_level': indent_level + 1}
	)
	
	editor = arcpy.da.Editor(gdb)
	
	
	logging.info(
		'Starting transaction'
		,extra = {'indent_level': indent_level + 1}
	)
	
	editor.startEditing(
		with_undo = False
		,multiuser_mode = False
	)
	
	
	
	# Process discharge records
	
	count_discharge = 0
	count_discharge_attachment = 0
	
	with arcpy.da.InsertCursor(
		in_table = table_target
		,field_names = ( # IMPORTANT: Row processing below is by field index order
			'LocationVisitGlobalID'
			,'RecordStart'
			,'RecordEnd'
			,'Volume'
			,'Uncertainty'
			,'IsReviewed'
		)
	) as cursor_target:
	
		with arcpy.da.InsertCursor(
			in_table = table_target_attach
			,field_names = ( # IMPORTANT: Row processing below is by field index order
				'CONTENT_TYPE'
				,'ATT_NAME'
				,'DATA_SIZE'
				,'DATA'
				,'KEYWORDS'
				,'EXIFINFO'
				,'REL_GLOBALID'
			)
		) as cursor_target_attach:
	
			with arcpy.da.SearchCursor(
				in_table = table_source
				,field_names = ( # IMPORTANT: Row processing below is by field index order
					'GlobalID'
					,'DischargeRecordStart'
					,'DischargeRecordEnd'
					,'DischargeVolume'
					,'DischargeUncertainty'
				)
				,where_clause = (
					'DischargeRecordStart IS NOT NULL'
					' OR DischargeRecordEnd IS NOT NULL'
					' OR DischargeVolume IS NOT NULL'
					' OR DischargeUncertainty IS NOT NULL'
					' OR EXISTS('
					'	SELECT'
					'		LocationVisit__ATTACH_EVW.REL_GLOBALID'
					'	FROM hydro.LocationVisit__ATTACH_EVW'
					' WHERE'
					'	LocationVisit__ATTACH_EVW.REL_GLOBALID = LocationVisit_EVW.GlobalID'
					"	AND LocationVisit__ATTACH_EVW.KEYWORDS = 'DischargeDataFiles'"
					' )'
				)
			) as cursor_source:
			
				for row_source in cursor_source:
				
					count_discharge += 1

					
					row_json = json.dumps(
						dict(
							zip(
								cursor_source.fields
								,row_source
							)
						)
						,indent = mg.JSON_INDENT
						,default = str
					)
					
					logging.info(
						f'Read discharge record : {count_discharge} : {row_json}'
						,extra = {'indent_level': indent_level}
					)
					
					
					
					# Write discharge row
					
					logging.info(
						f'Writitng discharge record : {count_discharge}'
						,extra = {'indent_level': indent_level + 1}
					)
					
					
					row_target = (
						row_source[0]
						,row_source[1]
						,row_source[2]
						,row_source[3]
						,row_source[4]
						,'No'
					)
					
					
					try:
					
						objectid_target = cursor_target.insertRow(row_target)
						
						
					except Exception as e:
					
						logging.error(
							f'Error writing discharge record: {e}'
							,extra = {'indent_level': indent_level + 1}
						)
						
						logging.info(
							'Rolling back transaction'
							,extra = {'indent_level': indent_level + 1}
						)
						
						editor.stopEditing(False)

						raise RuntimeError(e)

					
					logging.info(
						f'Wrote discharge record : OBJECTID {objectid_target}'
						,extra = {'indent_level': indent_level + 1}
					)
					
					
					
					# Process attachments
					
					with arcpy.da.SearchCursor(
						in_table = table_target
						,field_names = 'GlobalID' # IMPORTANT: Row processing below is by field index order
						,where_clause = f'OBJECTID = {objectid_target}'
					) as cursor_target_globalid:
					
						target_globalid = cursor_target_globalid.next()[0]
						
						
					
						with arcpy.da.SearchCursor(
							in_table = table_source_attach
							,field_names = ( # IMPORTANT: Row processing below is by field index order
								'CONTENT_TYPE'
								,'ATT_NAME'
								,'DATA_SIZE'
								,'DATA'
								,'KEYWORDS'
								,'EXIFINFO'
								,'GLOBALID'
							)
							,where_clause = (
								"GDB_TO_DATE = '9999-12-31 23:59:59'"
								f" AND REL_GLOBALID = '{cursor_source[0]}'"
								f" AND KEYWORDS = 'DischargeDataFiles'"
							)
						) as cursor_source_attach:
						
							for row_source_attach in cursor_source_attach:
							
								count_discharge_attachment += 1

								
								
								# Write discharge attachment
								
								logging.info(
									f'Writing discharge attachment : {count_discharge_attachment} : {row_source_attach[1]}'
									,extra = {'indent_level': indent_level + 1}
								)
								
								row_target_attachment = (
									row_source_attach[0]
									,row_source_attach[1]
									,row_source_attach[2]
									,row_source_attach[3]
									,row_source_attach[4]
									,row_source_attach[5]
									,target_globalid
								)
								
								
								try:
								
									objectid_target_attach = cursor_target_attach.insertRow(row_target_attachment)
									
									
								except Exception as e:
								
									logging.error(
										f'Error writing discharge attachment: {e}'
										,extra = {'indent_level': indent_level + 1}
									)
									
									logging.info(
										'Rolling back transaction'
										,extra = {'indent_level': indent_level + 1}
									)
									
									editor.stopEditing(False)
									
									raise RuntimeError(e)

								
								logging.info(
									f'Wrote discharge attachment : OBJECTID {objectid_target_attach}'
									,extra = {'indent_level': indent_level + 1}
								)
								
								
								
								# Delete LocationVisit attachment
								
								with arcpy.da.UpdateCursor(
									in_table = table_source_attach
									,field_names = 'GLOBALID'
									,where_clause = f"GLOBALID = '{row_source_attach[6]}'"
								) as cursor_source_attach_update:
								
									logging.info(
										f'Deleting source attachment : GLOBALID {row_source_attach[6]}'
										,extra = {'indent_level': indent_level + 1}
									)
								
									# UpdateCursor does not have .next(), so using `for`
									for row_update in cursor_source_attach_update:
									
										try:
										
											cursor_source_attach_update.deleteRow()
											
										
										except Exception as e:
										
											logging.error(
												f'Error deleting source attachment: {e}'
												,extra = {'indent_level': indent_level + 1}
											)
											
											logging.info(
												'Rolling back transaction'
												,extra = {'indent_level': indent_level + 1}
											)
											
											editor.stopEditing(False)
											
											raise RuntimeError(e)
									
				
				
	# Save edits
	
	logging.info(
		'Committing transaction'
		,extra = {'indent_level': indent_level}
	)
	
	editor.stopEditing(True)
	
	
	
	# Report statistics
	
	logging.info(
		'Completed discharge row migration'
		f'\n\tWrote {count_discharge} discharge records'
		f'\n\tWrote {count_discharge_attachment} discharge attachment records'
		,extra = {'indent_level': indent_level}
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
		'-d'
		,'--database'
		,dest = 'database'
		,help = 'SQL Server database name'
		,metavar = '<database>'
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
	,database
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
		,database = database
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

		input('Check geodatabase connection file, then press any key to return to error processing: ')
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
		f'Hydrologic Data Model Geodatabase Update 5\n'
		f'{mg.BANNER_DELIMITER_2}\n'
		f'Target database server:  {args.server}\n'
		f'Target database name:    {args.database}\n'
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
		) = _connect_gdb(
			args.server
			,args.database
		)
		
		
	except RuntimeError as e:
	
		logging.error(e)
		
		sys.exit(mg.EXIT_FAILURE)



	#
	# Delete view LocationLastVisit
	#
	
	logging.info('Deleting view LocationLastVisit')
	
	delete_view_locationlastvisit(
		gdb = gdb
		,indent_level = 1
	)
	
	
	
	#
	# Migrate discharge data
	#
	
	logging.info('Moving discharge data to standalone table')
	
	
	logging.info(
		'Creating discharge table'
		,extra = {'indent_level': 1}
	)
	
	create_table_dischargemeasurement(
		gdb = gdb
		,indent_level = 2
	)

	
	
	logging.info(
		'Creating relationship class'
		,extra = {'indent_level': 1}
	)
	
	create_rcs(
		gdb
		,indent_level = 2
	)



	logging.info(
		'Migrating discharge records and attachments'
		,extra = {'indent_level': 1}
	)
	
	migrate_data_discharge(
		gdb = gdb
		,indent_level = 2
	)



	logging.info(
		'Deleting discharge fields from LocationVisit'
		,extra = {'indent_level': 1}
	)
	
	delete_fields_discharge(
		gdb = gdb
		,indent_level = 2
	)



	#
	# Cleanup
	#

	logging.info('Done.')


################################################################################
# END
################################################################################
