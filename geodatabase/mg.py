################################################################################
# Name:
#	mg.py
#
# Purpose:
#	Shared Python objects for Mannion Geosystems modules
#
# Environment:
#	ArcGIS Pro 3.4.2
#	Python 3.11.10, with:
#		arcpy 3.4 (build py311_arcgispro_55347)
#
# Notes:
#	MESSAGES
#
#	Diagnostic messages are sent using the built-in `logging` module.
#
#	To improve readability for multiline and hierarchical messages, this
#	module includes a custom `logging.Formatter` subclass,
#	`FormatterIndent`.
#
#	One feature of the `FormatterIndent` class is noteworthy here - you may
#	notice in this module that calls generating log messages
#	(e.g. `logging.info()`, `logging.error()`) use the optional `extra`
#	argument, as in the following example:
#
#		logging.info(
#			'Diagnostic message'
#			,extra = {'indent_level': 2}
#		)
#
#	The `extra` argument is supported by the built-in `logging` module,
#	but its payload - the contents of the dictionary - is interpreted by the
#	custom `FormatterIndent` class.
#
#	For details about the `extra` argument, see the Python documentation
#	for the `logging.debug()` function.
#
#	For details about the custom `FormatterIndent` class, including the
#	`indent_level` payload, see the comments within the class code below.
#
# History:
#	2022-07-18 MCM Created
#	2022-11-21 MCM Added attachment upgrade support (Hydro 55)
#	2023-02-23 MCM Added custom logging levels DATA and DATADEBUG
#	2023-03-13 MCM Changed `attachments_upgrade` default to True
#	2023-11-27 MCM Added asdict()
#	2024-10-22 MCM Added create_view()
#
# To do:
#	none
#
# Copyright 2003-2025. Mannion Geosystems, LLC. http://www.manniongeo.com
################################################################################


#
# Modules
#

import arcpy
import copy
import datetime
import inspect
import json
import logging
import os
import uuid



################################################################################
# Constants
################################################################################


#
# Exit codes
#

EXIT_FAILURE = -1



#
# Message formatting
#

BANNER_WIDTH = 80
BANNER_DELIMITER_1 = '=' * BANNER_WIDTH
BANNER_DELIMITER_2 = '-' * BANNER_WIDTH

JSON_FORMAT_DATE = '%Y-%m-%d %H:%M:%S'
JSON_INDENT = 4



#
# Diagnostic log
#

LOG_FORMAT = '%(asctime)s.%(msecs)-3d %(levelname)-9s %(message)s' # msecs occasionally returns two digits instead of three; right-pad with space character to preserve alignment, if necessary
LOG_FORMAT_DATE = '%Y-%m-%d %H:%M:%S'
LOG_INDENT_HEADER = 34 # For indenting multi-line messages; currently set to line header length
LOG_LEVEL_DATA = logging.DEBUG - 1
LOG_LEVEL_DATADEBUG = logging.DEBUG - 2



#
# Editor Tracking
#

LAST_EDITOR_NAME = 'Employee'
LAST_EDITOR_TIMESTAMP = 'EditTimestamp'



################################################################################
# Classes
################################################################################

class FormatterIndent(logging.Formatter):
	'''
	Format multiline log messges to left-align message content
	
	By default, multiline messages continue printing at character column
	zero after each newline, such as:
	
		2021-10-27 18:20:47.885 INFO      Multiline
		message
		
	This formatter pads (with spaces) subsequent lines to left-align with
	the message content on the first line:
	
		2021-10-27 18:20:47.885 INFO      Multiline
		                                  message
						  
	This improves readability for user-focused feedback, and facilitates
	importing console or log file output into other systems
	(e.g. spreadsheet, database table).
	
	
	
	INDENT LEVEL
	
	In addition to, but separately from, the multiline indentation described
	above, this log formatter also supports an "indent level" for indenting
	subordinate messages under a primary one. For example:
	
		2021-10-27 18:20:47.885 INFO      Starting primary task
		2021-10-27 18:20:48.483 INFO      	Secondary task 1 with a
							multiline message
		2021-10-27 18:20:48.775 INFO      	Secondary task 2
		2021-10-27 18:20:49.121 INFO      		Tertiary task

	Observe that the secondary tasks are indented below their primary task
	to facilitate readability.
	
	To specify the indent level, use the `extra` keword argument when
	sending a log message (e.g. logging.info(), logging.error()) as
	described in the `logging` module documentation for its `debug()`
	function:
	
		https://docs.python.org/3.9/library/logging.html#logging.debug
		
	To summarize, `extra` is one of three optional keyword arguments
	supported by the `logging.debug()` and related functions. The argument
	value is a dictionary, which can contain any arbitrary keyword/value
	pairs that custom classes such as this formatter may care to use.
	
	The following example shows how to generate the second secondary task
	message from the example output above:
	
		logging.info(
			'Secondary task 2'
			,extra = {'indent_level': 1}
		)
		
	For more indentation, choose a larger integer value for `indent_level`.
	'''

	def format(
		self
		,record
	):

		# Copy LogRecord to avoid propagating changes to Handlers that
		# use other Formatters
		#
		# Shallow copy is acceptable because we're only modifying an
		# str attribute

		r = copy.copy(record)
		
		if hasattr(
			r
			,'indent_level'
		):
		
			log_indent_line = '\t' * r.indent_level
			
		
		else:
		
			log_indent_line = ''
			
		
		
		r.msg = f'{log_indent_line}{r.msg}'
		
		
		
		r.msg = str(r.msg).replace(
			'\n'
			,f'\n{" " * LOG_INDENT_HEADER}{log_indent_line}'
		)


		return super().format(r)



################################################################################
# Functions
################################################################################

def add_fields(
	table
	,fields_spec
	,indent_level = 0
):
	'''
	`fields_spec` is a tuple-of-tuples in the following format:

		(
			#name		,type	,precision	,scale	,length	,alias			,nullable	,required	,domain		,default
			('Attribute1'	,'Text'	,''		,''	,16	,'Attribute One'	,True		,False		,'Domain 1'	,'Value 1')
			,...
		)
	'''

	subtype_domains = []



	for field_spec in fields_spec:

		(
			name
			,data_type
			,precision
			,scale
			,length
			,alias
			,is_nullable
			,is_required
			,domain
			,default
		) = field_spec



		logging.info(
			f'{name}'
			,extra = {'indent_level': indent_level}
		)



		if type(domain) is tuple:

			subtype_domains.append(
				(
					name
					,domain
				)
			)

			domain = ''



		arcpy.management.AddField(
			in_table = table
			,field_name = name
			,field_type = data_type
			,field_precision = precision
			,field_scale = scale
			,field_length = length
			,field_alias = alias
			,field_is_nullable = is_nullable
			,field_is_required = is_required
			,field_domain = domain
		)



		if default:

			arcpy.management.AssignDefaultToField(
				in_table = table
				,field_name = name
				,default_value = default
			)



	return subtype_domains



def add_subtypes(
	table
	,subtype_spec
	,indent_level = 0
):

	(
		field_name
		,subtypes
	) = subtype_spec



	logging.info(
		f'Setting subtype field to {field_name}'
		,extra = {'indent_level': indent_level}
	)



	arcpy.management.SetSubtypeField(
		in_table = table
		,field = field_name
	)



	for subtype in subtypes:

		(
			code
			,description
		) = subtype


		logging.info(
			f'{code}: {description}'
			,extra = {'indent_level': indent_level}
		)


		arcpy.management.AddSubtype(
			in_table = table
			,subtype_code = code
			,subtype_description = description
		)



def asdict(
	object
	,attributes
):
	'''
	Convert complex objects to dictionaries with simple types that can be
	encoded as JSON by json module

	This function accepts an object and a sequence of attribute names, and
	returns a dict of the attribute names and their values.

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

			if ( # Display human-friendly representation of binary
				isinstance(
					value
					,bytearray
				)
				or isinstance(
					value
					,bytes
				)
			):
			
				value = f'<binary: {len(value):,} bytes>'
				
			
			elif isinstance( # Convert datetime to string, for subsequent JSON conversions
				value
				,datetime.datetime
			):

				value = value.strftime(JSON_FORMAT_DATE)


			elif isinstance( # Display human-friendly representation of geometry
				value
				,arcpy.Geometry
			):

				value = json.loads(value.JSON)
				
				
			elif isinstance( # Convert UUID to string, for subsequent JSON conversions
				value
				,uuid.UUID
			):
			
				value = str(value)



			d[a] = value



	# Return

	return d



def assign_privileges(
	table
	,privileges_spec
	,indent_level = 0
):

	for privilege in privileges_spec:

		(
			username
			,read_privilege
			,write_privilege
		) = privilege


		logging.info(
			f'{username:15}{read_privilege:10}{write_privilege:10}'
			,extra = {'indent_level': indent_level}
		)


		arcpy.management.ChangePrivileges(
			table
			,username
			,read_privilege
			,write_privilege
		)



def create_domain_cv(
	gdb
	,coded_values
	,name
	,data_type
	,description = ''
	,split_policy = 'DEFAULT'
	,merge_policy = 'DEFAULT'
	,indent_level = 0
):

	logging.info(
		f'Creating domain {name}'
		,extra = {'indent_level': indent_level}
	)


	arcpy.management.CreateDomain(
		in_workspace = gdb
		,domain_name = name
		,domain_description = description
		,field_type = data_type
		,domain_type = 'CODED'
		,split_policy = split_policy
		,merge_policy = merge_policy
	)



	logging.info(
		'Adding coded values'
		,extra = {'indent_level': indent_level + 1}
	)

	for cv in coded_values:

		(
			code
			,description
		) = cv


		logging.info(
			f'{code}: {description}'
			,extra = {'indent_level': indent_level + 2}
		)


		arcpy.management.AddCodedValueToDomain(
			in_workspace = gdb
			,domain_name = name
			,code = code
			,code_description = description
		)



def create_fc(
	gdb
	,fc_name
	,alias
	,geometry
	,sr
	,attributes = None
	,subtypes = None
	,global_id = True
	,editor_tracking = True
	,archiving = True
	,attachments = True
	,attachments_upgrade = True
	,privileges = None
	,indent_level = 0
):


	# Log start message

	logging.info(
		f'Creating feature class {fc_name}'
		,extra = {'indent_level': indent_level}
	)



	# Create feature class

	arcpy.management.CreateFeatureclass(
		out_path = gdb
		,out_name = fc_name
		,geometry_type = geometry
		,spatial_reference = sr
	)



	fc = os.path.join(
		gdb
		,fc_name
	)



	# Set alias

	logging.info(
		f'Setting alias to {alias}'
		,extra = {'indent_level': indent_level + 1}
	)

	arcpy.AlterAliasName(
		table = fc
		,alias = alias
	)



	# Add attributes

	if attributes is not None:

		logging.info(
			'Adding attributes'
			,extra = {'indent_level': indent_level + 1}
		)

		subtype_domains = add_fields(
			table = fc
			,fields_spec = attributes
			,indent_level = indent_level + 2
		)

	else:

		subtype_domains = []



	# Add subtypes

	if subtypes is not None:

		logging.info(
			'Adding subtypes'
			,extra = {'indent_level': indent_level + 1}
		)

		add_subtypes(
			table = fc
			,subtype_spec = subtypes
			,indent_level = indent_level + 2
		)



	# Add subtype-specific domains

	if len(subtype_domains) > 0:

		logging.info(
			'Adding subtype-specific domains'
			,extra = {'indent_level': indent_level + 1}
		)

		set_subtype_domains(
			table = fc
			,domains_spec = subtype_domains
			,indent_level = indent_level + 2
		)



	# Add global IDs

	if global_id:

		logging.info(
			'Adding global ID'
			,extra = {'indent_level': indent_level + 1}
		)

		arcpy.management.AddGlobalIDs(
			in_datasets = fc
		)



	# Enable editor tracking

	if editor_tracking:

		logging.info(
			'Enabling editor tracking'
			,extra = {'indent_level': indent_level + 1}
		)

		arcpy.management.EnableEditorTracking(
			in_dataset = fc
			,last_editor_field = LAST_EDITOR_NAME
			,last_edit_date_field = LAST_EDITOR_TIMESTAMP
			,add_fields = True
			,record_dates_in = 'UTC'
		)



	# Enable archiving

	if archiving:

		logging.info(
			'Enabling archiving'
			,extra = {'indent_level': indent_level + 1}
		)

		arcpy.management.EnableArchiving(
			in_dataset = fc
		)



	# Enable attachments
	#
	# Ensure that GlobalIDs are enabled first, so attachments will use
	# them in %_ATTACHREL relationship class

	if attachments:

		logging.info(
			'Enabling attachments'
			,extra = {'indent_level': indent_level + 1}
		)

		arcpy.management.EnableAttachments(
			in_dataset = fc
		)
		
		
		
		if attachments_upgrade:
		
			logging.info(
				'Upgrading attachments format'
				,extra = {'indent_level': indent_level + 1}
			)
			
			arcpy.management.UpgradeAttachments(
				in_dataset = fc
			)



	# Assign privileges

	if privileges:

		logging.info(
			'Assigning privileges'
			,extra = {'indent_level': indent_level + 1}
		)


		assign_privileges(
			table = fc
			,privileges_spec = privileges
			,indent_level = indent_level + 2
		)



def create_rc(
	gdb
	,origin_table_name
	,destination_table_name
	,rc_name
	,rc_type
	,forward_label
	,backward_label
	,message_direction
	,cardinality
	,attributed
	,origin_pk
	,origin_fk
	,destination_pk = None
	,destination_fk = None
	,attributes = None
	,indent_level = 0
):
	'''
	`attributes` is a tuple in the format of the `add_fields()` function
	`fields_spec` argument
	'''


	# Log start message

	logging.info(
		f'Creating relationship class {rc_name}'
		,extra = {'indent_level': indent_level}
	)



	# DEBUG: Print arguments and values
	
	self_name = inspect.currentframe().f_code.co_name
	self = eval(self_name)
	args = inspect.getfullargspec(self).args
	
	logging.debug(
		'Arguments:'
		,extra = {'indent_level': indent_level + 1}
	)
	for arg in args:
	
		logging.debug(
			f'{arg:<30}{locals()[arg]}'
			,extra = {'indent_level': indent_level + 2}
		)
	


	# Derive fully qualified object names

	origin_table = os.path.join(
		gdb
		,origin_table_name
	)

	destination_table = os.path.join(
		gdb
		,destination_table_name
	)
	
	rc = os.path.join(
		gdb
		,rc_name
	)



	# Create relationship class

	arcpy.management.CreateRelationshipClass(
		origin_table = origin_table
		,destination_table = destination_table
		,out_relationship_class = rc
		,relationship_type = rc_type
		,forward_label = forward_label
		,backward_label = backward_label
		,message_direction = message_direction
		,cardinality = cardinality
		,attributed = attributed
		,origin_primary_key = origin_pk
		,origin_foreign_key = origin_fk
		,destination_primary_key = destination_pk
		,destination_foreign_key = destination_fk
	)
	
	
	
	# Add attributes
	
	if attributes is not None:
	
		logging.info(
			f'Creating relationship class {rc_name}'
			,extra = {'indent_level': indent_level + 1}
		)
		
		rc_table = os.path.join(
			gdb
			,rc_name
		)

		add_fields(
			table = rc_table
			,fields_spec = attributes
			,indent_level = indent_level + 2
		)
			
			
			
def create_table(
	gdb
	,table_name
	,alias
	,attributes = None
	,subtypes = None
	,global_id = True
	,editor_tracking = True
	,archiving = True
	,attachments = True
	,attachments_upgrade = True
	,privileges = None
	,indent_level = 0
):


	# Log start message

	logging.info(
		f'Creating table {table_name}'
		,extra = {'indent_level': indent_level}
	)



	# Create table

	arcpy.management.CreateTable(
		out_path = gdb
		,out_name = table_name
	)



	table = os.path.join(
		gdb
		,table_name
	)



	# Set alias

	logging.info(
		f'Setting alias to {alias}'
		,extra = {'indent_level': indent_level + 1}
	)

	arcpy.AlterAliasName(
		table = table
		,alias = alias
	)



	# Add attributes

	if attributes is not None:

		logging.info(
			'Adding attributes'
			,extra = {'indent_level': indent_level + 1}
		)

		subtype_domains = add_fields(
			table = table
			,fields_spec = attributes
			,indent_level = indent_level + 2
		)

	else:

		subtype_domains = []



	# Add subtypes

	if subtypes is not None:

		logging.info(
			'Adding subtypes'
			,extra = {'indent_level': indent_level + 1}
		)

		add_subtypes(
			table = table
			,subtype_spec = subtypes
			,indent_level = indent_level + 2
		)



	# Add subtype-specific domains

	if len(subtype_domains) > 0:

		logging.info(
			'Adding subtype-specific domains'
			,extra = {'indent_level': indent_level + 1}
		)

		set_subtype_domains(
			table = table
			,domains_spec = subtype_domains
			,indent_level = indent_level + 2
		)



	# Add global IDs

	if global_id:

		logging.info(
			'Adding global ID'
			,extra = {'indent_level': indent_level + 1}
		)

		arcpy.management.AddGlobalIDs(
			in_datasets = table
		)



	# Enable editor tracking

	if editor_tracking:

		logging.info(
			'Enabling editor tracking'
			,extra = {'indent_level': indent_level + 1}
		)

		arcpy.management.EnableEditorTracking(
			in_dataset = table
			,last_editor_field = LAST_EDITOR_NAME
			,last_edit_date_field = LAST_EDITOR_TIMESTAMP
			,add_fields = True
			,record_dates_in = 'UTC'
		)



	# Enable archiving

	if archiving:

		logging.info(
			'Enabling archiving'
			,extra = {'indent_level': indent_level + 1}
		)

		arcpy.management.EnableArchiving(
			in_dataset = table
		)



	# Enable attachments
	#
	# Ensure that GlobalIDs are enabled first, so attachments will use
	# them in %_ATTACHREL relationship class

	if attachments:

		logging.info(
			'Enabling attachments'
			,extra = {'indent_level': indent_level + 1}
		)

		arcpy.management.EnableAttachments(
			in_dataset = table
		)
		
		
		
		if attachments_upgrade:
		
			logging.info(
				'Upgrading attachments format'
				,extra = {'indent_level': indent_level + 1}
			)
			
			arcpy.management.UpgradeAttachments(
				in_dataset = table
			)



	# Assign privileges

	if privileges:

		logging.info(
			'Assigning privileges'
			,extra = {'indent_level': indent_level + 1}
		)


		assign_privileges(
			table = table
			,privileges_spec = privileges
			,indent_level = indent_level + 2
		)



def create_view(
	gdb
	,view_name
	,view_text
	,view_alias = None
	,object_id_field_name = None
	,shape_field_name = None
	,geometry_type = None
	,sr = None
	,extent = None
	,field_aliases = None
	,privileges = None
	,indent_level = 0
):


	# Log start message
	
	logging.info(
		f'Creating view {view_name}'
		,extra = {'indent_level': indent_level}
	)
	
	
	
	# Create view
	
	arcpy.management.CreateDatabaseView(
		input_database = gdb
		,view_name = view_name
		,view_definition = view_text
	)
	
	
	view = os.path.join(
		gdb
		,view_name
	)
	
	
	
	# Register with geodatabase
	
	logging.info(
		'Registering with geodatabase'
		,extra = {'indent_level': indent_level + 1}
	)
	
	
	arcpy.management.RegisterWithGeodatabase(
		in_dataset = view
		,in_object_id_field = object_id_field_name
		,in_shape_field = shape_field_name
		,in_geometry_type = geometry_type
		,in_spatial_reference = sr
		,in_extent = extent
	)
	
	
	
	# Set view alias
	
	if view_alias:
	
		logging.info(
			'Setting view alias'
			,extra = {'indent_level': indent_level + 1}
		)
		
		
		arcpy.AlterAliasName(
			table = view
			,alias = view_alias
		)
	
	
	
	# Set field aliases
	
	if field_aliases:
	
		logging.info(
			'Setting field aliases'
			,extra = {'indent_level': indent_level + 1}
		)
		
		for alias in field_aliases:
		
			(
				field_name
				,field_alias
			) = alias
			
			
			logging.info(
				f'{field_name} > {field_alias}'
				,extra = {'indent_level': indent_level + 2}
			)
			
			
			arcpy.management.AlterField(
				in_table = view
				,field = field_name
				,new_field_alias = field_alias
			)
		
		
		
	# Assign privileges
	
	if privileges:
	
		logging.info(
			'Assigning privileges'
			,extra = {'indent_level': indent_level + 1}
		)
		
		
		assign_privileges(
			table = view
			,privileges_spec = privileges
			,indent_level = indent_level + 2
			
		)
	
		




def none2blank(
	string
):

	if string is None:
	
		return ''
		
		
	else:
	
		return string
		


def set_subtype_domains(
	table
	,domains_spec
	,indent_level = 0
):

	for domain_spec in domains_spec:

		(
			field_name
			,assignments
		) = domain_spec


		logging.info(
			f'Field {field_name}'
			,extra = {'indent_level': indent_level}
		)


		for assignment in assignments:

			(
				subtype_code
				,domain_name
			) = assignment


			logging.info(
				f'{subtype_code}: {domain_name}'
				,extra = {'indent_level': indent_level + 1}
			)


			arcpy.management.AssignDomainToField(
				in_table = table
				,field_name = field_name
				,domain_name = domain_name
				,subtype_code = subtype_code
			)





################################################################################
# END
################################################################################
