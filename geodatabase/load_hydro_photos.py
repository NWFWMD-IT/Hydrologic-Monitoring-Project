################################################################################
# Name:
#	load_hydro_photos.py
#
# Purpose:
#	Load Location and Measuring Point photos exported from Aquarius to
#	hydro geodatabase, including KEYWORDS values for Survey123
#
# Environment:
#	ArcGIS Pro 3.4.2
#	Python 3.11.10, with:
#		arcpy 3.4 (build py311_arcgispro_55347)
#
# Notes:
#	This script processes a directory of photo files exported from Aquarius
#	and loads those corresponding to a Location or Measuring Point to the
#	hydro geodatabase as attachments to their respective table. For each
#	photo, the script populates the attachment KEYWORDS attribute value
#	to assign the photo to the appropriate question in the hydro Survey123
#	survey.
#
#
#
#	BUSINESS CASE
#
#	Aquarius is the primary repository of hydro photos. The geodatabase
#	stores copies of these photos to provide visual guidance for Survey123
#	users when working in the field. Therefore, some workflow is required
#	for copying photos from the former to the latter and associating them
#	with the proper geodatabase records.
#
#	This script performs part of that workflow - specifically, processing
#	photo files that have been previously exported from Aquarius and loading
#	them to the geodatabase.
#
#	Each of the two systems manages photo storage and attribution
#	differently. So, this script must also translate between the Aquarius
#	and hydro geodatabase photo storage models to ensure that each picture
#	ultimately displays with the correct feature and question in the
#	Survey123 field application.
#
#
#
#	DATA MODELS
#
#	Photos in Aquarius are broadly associated with monitoring locations.
#	This includes general photos of the Location, as well as targeted photos
#	of Measuring Points at that Location. By contrast, in the hydro
#	geodatabase, photos are directly associated with either a Location or
#	a Measuring Point, by virtute of being stored as a geodatabase
#	attachment to one of those two tables.
#
#	Accordingly, photos in Aquarius are attributed (e.g. tags, comments) to
#	indicate whether the represent a general Location photo or specific
#	Measuring Point photo - and, in the latter case, which of possibly
#	multiple Measuring Points at a given Location the photo represents.
#
#
#
#	WORKFLOW
#
#	A separate process must be run before this script to export two types
#	of information from Aquarius:
#
#		o Filesystem directory of photo files
#
#		o Index file identifying, for each photo:
#
#			o Whether the photo should be attached to a Location or
#			  Measuring Point record
#
#			o Which specific Location or Measuring Point the photo
#			  represents
#
#	This script reads the index file, and loads each Location and Measuring
#	Point photo file in the index to the corresponding geodatabase table
#	and record. The script also populates the attachment metadata (KEYWORDS)
#	to associate the new geodatabase attachment with the appropriate
#	question in the Survey123 field application.
#
#	Note that Aquarius stores additional photos (and other documents) that
#	are not used with the geodatabase / Survey123. These extra photos may
#	be exported to the filesystem by the preceding process in the workflow,
#	but will be ignored by this script because they will not be annotated
#	in the index file as representing a photo for use with the geodatabase.
#	This implies that the integrity of the geodatabase photos depends on
#	Aquarius data managers attributing the source photos correctly. A
#	discussion of the Aquarius photo attribution workflow is outside the
#	scope of this document.
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
#	2023-10-30 MCM Created (#109)
#	2025-03-16 MCM Allow loading one photo to multiple Measuring Points (#213)
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
import mimetypes
import os
import re
import sys
import tempfile
import uuid


# Custom

import constants as C
import mg



#
# Constants
#

NEWLINE = '\n' # For f-string expressions, which disallow backslashes



################################################################################
# Classes
################################################################################

class Attachment:
	'''
	Abstract superclass for common features of Location / Measuring Point
	attachment subclasses
	
	Stores source data and metadata for target attachment
	'''


	########################################################################
	# Class attributes
	########################################################################


	#
	# Public
	#


	# List of public, custom (i.e. non-system) instance attributes, for use
	# by __str__, etc.

	ATTRIBUTES = (
		'content_type'
		,'data_size'
		,'gdb'
		,'globalid'
		,'photo'
		,'rel_globalids'
	)



	########################################################################
	# Properties
	########################################################################


	#
	# Subclass-specific, read-only constants
	#
	# Initialized to None here in superclass
	#
	
	@property
	def keywords(self):
		'''
		Geodatabase attachment keywords, for Survey123 question names
		'''
	
		return None
		
	
	
	@property
	def table_name(self):
		
		return None
	
	
	
	@property
	def table_name_attachment(self):
	
		return None
	
	
	
	@property
	def where_clauses(self):
		'''
		List of filter expressions that identify rows to which photo
		will be attached
		'''
		
		return None
		
		
		
	#
	# Derived read-only properties
	#
	
	@property
	def table(self):
	
		return os.path.join(
			gdb
			,self.table_name
		)
		
	
	
	@property
	def table_attachment(self):
	
		return os.path.join(
			gdb
			,self.table_name_attachment
		)
		
	
	
	########################################################################
	# Instance methods
	########################################################################


	#
	# Public
	#

	def __init__(
		self
		,gdb
		,photo # Photo
		
	):

		logging.debug(f'Initializing {__class__.__name__}')



		# Store source data values

		self.gdb = gdb
		self.photo = photo



		# Create instance attributes
		
		self._initialize_attributes()
		
		
		
		# Process source data into instance attributes
		
		self.transform()



	def __str__(self):

		return json.dumps(
			self.asdict()
			,indent = mg.JSON_INDENT
		)
	
	
	
	def asdict(self):
	
		properties = (
			'keywords'
			,'table'
			,'table_attachment'
			,'table_name'
			,'table_name_attachment'
			,'where_clauses'
		)
		
		
		attributes = sorted(
			self.ATTRIBUTES
			+ properties
		)
		
		
		return mg.asdict(
			object = self
			,attributes = attributes
		)
		
		
		
	def check_target(
		self
		,rel_globalid
	):
		'''
		Check if attachment already exists in geodatabase
		
		We need to test by file name, because there is nowhere to store
		Aquarius photo UUID in the attachment table.
		'''
	
		logging.debug('Checking for existing attachment')
	
	
		table = os.path.join(
			self.gdb
			,self.table_name_attachment
		)


		with arcpy.da.SearchCursor(
			in_table = table
			,field_names = 'rel_globalid' # Arbitrary column
			,where_clause = (
				f"rel_globalid = '{rel_globalid}'"
				f" AND att_name = '{self.photo.file_name}'"
			)
		) as cursor:
		
			try:
			
				row = cursor.next()
				
				raise ValueError(
					'Attachment already exists for:'
					f'\n\tTable: {self.table_name}'
					f'\n\tGlobal ID: {rel_globalid}'
					f'\n\tFile name: {self.photo.file_name}'
				)
				
				
			except StopIteration:
			
				logging.debug('Attachment does not already exist')
				
					

	def load(self):
		'''
		Load source file to geodatabase attachment(s)
		
		Return list of errors for failed loads
		'''
		
		errors = []
		
		
		for rel_globalid in self.rel_globalids:
		
			logging.debug(f'Loading attachment to {self.table_name_attachment} for rel_globalid {rel_globalid}')
		
		
			# Verify that attachment does not already exist
			
			try:
			
				self.check_target(rel_globalid)
				
			
			except ValueError as e:
			
				logging.debug('Failed to load attachment; collecting error for reporting after attempting all targets for this photo')
				errors.append(e)
				continue
			


			# Load attachment
			
			with arcpy.da.InsertCursor(
				in_table = self.table_attachment
				,field_names = (
					'rel_globalid'
					,'content_type'
					,'att_name'
					,'data_size'
					,'data'
					#,'globalid'
					#,'attachmentid'
					,'keywords'
				)
			) as cursor:
			
				cursor.insertRow(
					(
						rel_globalid
						,self.content_type
						,self.photo.file_name
						,self.data_size
						,self.photo.data
						# ArcGIS generates globalid automatically
						# ArcGIS generates attachmentid automatically
						,self.keywords
					)
				)
				
		
		
		return errors
			
			
		
	def transform(self):
	
		# Run a transformation function to populate each output
		# attribute
		
		for f in (
			self.transform_content_type
			,self.transform_data_size
			,self.transform_rel_globalids
		):
		
			logging.debug(f'Executing: {f.__name__}')
			f()



	def transform_content_type(self):
	
		self.content_type = mimetypes.guess_type(self.photo.file_name)[0]
		
		if self.content_type is None:
		
			raise ValueError(f'content_type: Unknown content type for photo {self.photo.file_name}')
			
			
			
	def transform_data_size(self):
	
		self.data_size = len(self.photo.data)



	def transform_rel_globalids(self):
	
		self.rel_globalids = []
		
	
		table = os.path.join(
			self.gdb
			,self.table_name
		)
		
		
		for where_clause in self.where_clauses:
		
			count_fetch = 0
			
			with arcpy.da.SearchCursor(
				in_table = table
				,field_names = 'globalid'
				,where_clause = where_clause
			) as cursor:
			
				for row in cursor:
				
					count_fetch += 1
					
					if count_fetch > 1:
					
						raise ValueError(
							f'rel_globalid: Found multiple rows for:'
							f'\n\tTable: {self.table_name}'
							f'\n\tFilter: {where_clause}'
						)
						
					
					self.rel_globalids.append(row[0][1:-1]) # Trim curly braces
					
					
			if count_fetch == 0:
			
				raise ValueError(
					f'rel_globalid: Did not find row for:'
						f'\n\tTable: {self.table_name}'
						f'\n\tFilter: {where_clause}'
				)



	#
	# Private
	#

	def _initialize_attributes(self):

		for a in self.ATTRIBUTES:

			if not hasattr(
				self
				,a
			):
			
				setattr(
					self
					,a
					,None
				)



class LocationAttachment(Attachment):
	'''
	Source data and metadata for Location geodatabase attachment
	'''


	########################################################################
	# Properties
	########################################################################
	
	@property
	def keywords(self):
		'''
		Geodatabase attachment keywords, for Survey123 question names
		'''
	
		return 'Location_image'
	
	

	@property
	def table_name(self):

		return 'hydro.location'
	
	
	
	@property
	def table_name_attachment(self):
	
		return 'hydro.location__attach'
	
	
	
	@property
	def where_clauses(self):
		'''
		List of filter expressions that identify rows to which photo
		will be attached
		'''
		
		return [f"nwfid = '{self.photo.location}'"]
		
	
	
class MPAttachment(Attachment):
	'''
	Source data and metadata for Measuring Point geodatabase attachment
	'''
	

	########################################################################
	# Properties
	########################################################################
	
	@property
	def keywords(self):
		'''
		Geodatabase attachment keywords, for Survey123 question names
		'''
	
		return 'MeasuringPoint_image'
	
	

	@property
	def table_name(self):

		return 'hydro.measuringpoint'
	
	
	
	@property
	def table_name_attachment(self):
	
		return 'hydro.measuringpoint__attach'
	
	
	
	@property
	def where_clauses(self):
		'''
		List of filter expressions that identify rows to which photo
		will be attached
		'''
		
		return [f"UPPER(aquariusid) = '{id}'" for id in self.photo.mp_uuids]
		
	
	
class IndexRecord:


	########################################################################
	# Instance methods
	########################################################################


	#
	# Public
	#

	def __init__(
		self
		,fields
		,values
	):

		logging.debug(f'Initializing {__class__.__name__}')



		# Store field names passed by caller
		#
		# Allows consumers to determine which attributes are from the
		# index record 

		self.fields = fields



		# Create an instance attribute for each field/value

		for (
			field
			,value
		) in zip(
			fields
			,values
		):

			setattr(
				self
				,field
				,value
			)



	def __str__(self):

		return json.dumps(
			self.asdict()
			,indent = mg.JSON_INDENT
		)
		
		
		
	def asdict(self):
	
		return mg.asdict(
			object = self
			,attributes = self.fields
		)



class Metrics:
	'''
	Abstract superclass for common features of input/output metrics
	subclasses
	'''


	########################################################################
	# Class attributes
	########################################################################


	#
	# Private
	#

	_TEMPLATE = '\n\t{type:<30s}{total:>12s}{succeeded:>12s}{failed:>12s}'
	
	
	
	########################################################################
	# Static methods
	########################################################################


	#
	# Private
	#
	
	@staticmethod
	def _check_count(count):
	
		if count is None:
		
			return None
			
			
		elif isinstance(
			count
			,int
		):
		
			if count < 0:
			
				raise ValueError(f'Invalid Metrics count: Value cannot be negative')
			
			else:
			
				return count
			
			
		else:
		
			raise ValueError(f'Invalid Metrics count: Expected an int, received a {type(count)}')
			
			
			
	@staticmethod
	def _format_count(value):
	
		if value is None:
		
			return '-'
			
		else:
		
			return str(f'{value:n}')
	
		
		
	@staticmethod
	def _get_total(
		succeeded
		,failed
	):
	
		if (
			succeeded is None
			and failed is None
		):
		
			return None
			
		else:
		
			return (succeeded or 0) + (failed or 0)


	
	########################################################################
	# Instance methods
	########################################################################


	#
	# Public
	#

	def __init__(
		self
		,header # Header message
	):

		logging.debug(f'Initializing {__class__.__name__}')



		# Store header
		
		self.header = header
		
		
		
class MetricsInput(Metrics):
	'''
	Store and report statistics for input data processing progress
	
	Callers can set succeeded and failed counters; the total counter is
	derived from these, and cannot be set directly.
	
	In some cases, a counter may not apply. To disable a counter, set its
	value to None. If both the succeeded and failed counters for one metric
	type are None, the total will be reported as None, as well.
	'''


	########################################################################
	# Properties
	########################################################################


	#
	# Photo index records
	#
	
	
	# Succeeded
	
	@property
	def index_succeeded(self):
	
		return self._index_succeeded
		
		
	@index_succeeded.setter
	def index_succeeded(
		self
		,count
	):
	
		self._index_succeeded = self._check_count(count)
		
		
	
	# Failed
	
	@property
	def index_failed(self):
	
		return self._index_failed
		
		
	@index_failed.setter
	def index_failed(
		self
		,count
	):
	
		self._index_failed = self._check_count(count)
		
		
	
	# Total
	
	@property
	def index_total(self):
	
		return self._get_total(
			succeeded = self.index_succeeded
			,failed = self.index_failed
		)
		
		

	#
	# Photo metadata analysis
	#
	
	
	# Succeeded
	
	@property
	def metadata_succeeded(self):
	
		return self._metadata_succeeded
		
		
	@metadata_succeeded.setter
	def metadata_succeeded(
		self
		,count
	):
	
		self._metadata_succeeded = self._check_count(count)
		
		
	
	# Failed
	
	@property
	def metadata_failed(self):
	
		return self._metadata_failed
		
		
	@metadata_failed.setter
	def metadata_failed(
		self
		,count
	):
	
		self._metadata_failed = self._check_count(count)
		
		
	
	# Total
	
	@property
	def metadata_total(self):
	
		return self._get_total(
			succeeded = self.metadata_succeeded
			,failed = self.metadata_failed
		)
		
		

	#
	# Photo file
	#
	
	
	# Succeeded
	
	@property
	def file_succeeded(self):
	
		return self._file_succeeded
		
		
	@file_succeeded.setter
	def file_succeeded(
		self
		,count
	):
	
		self._file_succeeded = self._check_count(count)
		
		
	
	# Failed
	
	@property
	def file_failed(self):
	
		return self._file_failed
		
		
	@file_failed.setter
	def file_failed(
		self
		,count
	):
	
		self._file_failed = self._check_count(count)
		
		
	
	# Total
	
	@property
	def file_total(self):
	
		return self._get_total(
			succeeded = self.file_succeeded
			,failed = self.file_failed
		)
		
		

	########################################################################
	# Instance methods
	########################################################################


	#
	# Public
	#

	def __init__(
		self
		,header = 'Input Processing Metrics' # Header message
	):

		super().__init__(header)
		
		
		
		# Initialize counters

		self.file_failed = 0
		self.file_succeeded = 0
		self.index_failed = 0
		self.index_succeeded = 0
		self.metadata_failed = 0
		self.metadata_succeeded = 0



	def __str__(self):


		# Negative count values indicate that the count does not apply,
		# and are formatted as '-'. By contrast, a zero indicates that
		# the counter is active and has not accumulated any instances
		# yet.
	
		message = self.header
		
		message += self._TEMPLATE.format(
			type = ''
			,total = 'Total'
			,succeeded = 'Succeeded'
			,failed = 'Failed'
		)

		message += self._TEMPLATE.format(
			type = 'Photo index record'
			,total = self._format_count(self.index_total)
			,succeeded = self._format_count(self.index_succeeded)
			,failed = self._format_count(self.index_failed)
		)


		message += self._TEMPLATE.format(
			type = 'Photo metadata analysis'
			,total = self._format_count(self.metadata_total)
			,succeeded = self._format_count(self.metadata_succeeded)
			,failed = self._format_count(self.metadata_failed)
		)


		message += self._TEMPLATE.format(
			type = 'Photo file'
			,total = self._format_count(self.file_total)
			,succeeded = self._format_count(self.file_succeeded)
			,failed = self._format_count(self.file_failed)
		)



		return message



class MetricsOutput(Metrics):
	'''
	Store and report statistics for output data processing progress
	
	Callers can set succeeded and failed counters; the total counter is
	derived from these, and cannot be set directly.
	
	In some cases, a counter may not apply. To disable a counter, set its
	value to None. If both the succeeded and failed counters for one metric
	type are None, the total will be reported as None, as well.
	'''


	########################################################################
	# Properties
	########################################################################


	#
	# Location photos
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
	
		self._location_succeeded = self._check_count(count)
		
		
	
	# Failed
	
	@property
	def location_failed(self):
	
		return self._location_failed
		
		
	@location_failed.setter
	def location_failed(
		self
		,count
	):
	
		self._location_failed = self._check_count(count)
		
		
	
	# Total
	
	@property
	def location_total(self):
	
		return self._get_total(
			succeeded = self.location_succeeded
			,failed = self.location_failed
		)
		


	#
	# Measuring Point photos
	#
	
	
	# Succeeded
	
	@property
	def mp_succeeded(self):
	
		return self._mp_succeeded
		
		
	@mp_succeeded.setter
	def mp_succeeded(
		self
		,count
	):
	
		self._mp_succeeded = self._check_count(count)
		
		
	
	# Failed
	
	@property
	def mp_failed(self):
	
		return self._mp_failed
		
		
	@mp_failed.setter
	def mp_failed(
		self
		,count
	):
	
		self._mp_failed = self._check_count(count)
		
		
	
	# Total
	
	@property
	def mp_total(self):
	
		return self._get_total(
			succeeded = self.mp_succeeded
			,failed = self.mp_failed
		)
		
		

	########################################################################
	# Instance methods
	########################################################################


	#
	# Public
	#

	def __init__(
		self
		,header = 'Output Processing Metrics' # Header message
	):

		super().__init__(header)
		
		
		
		# Initialize counters

		self.location_failed = 0
		self.location_succeeded = 0
		self.mp_failed = 0
		self.mp_succeeded = 0



	def __str__(self):


		# Negative count values indicate that the count does not apply,
		# and are formatted as '-'. By contrast, a zero indicates that
		# the counter is active and has not accumulated any instances
		# yet.
	
		message = self.header
		
		message += self._TEMPLATE.format(
			type = ''
			,total = 'Total'
			,succeeded = 'Succeeded'
			,failed = 'Failed'
		)

		message += self._TEMPLATE.format(
			type = 'Location photo'
			,total = self._format_count(self.location_total)
			,succeeded = self._format_count(self.location_succeeded)
			,failed = self._format_count(self.location_failed)
		)

		message += self._TEMPLATE.format(
			type = 'Measuring Point photo'
			,total = self._format_count(self.mp_total)
			,succeeded = self._format_count(self.mp_succeeded)
			,failed = self._format_count(self.mp_failed)
		)



		return message
		
		
	
class Photo:
	'''
	Source photo
	'''


	########################################################################
	# Class attributes
	########################################################################


	#
	# Public
	#


	# List of public, custom (i.e. non-system) instance attributes, for use
	# by __str__, etc.

	ATTRIBUTES = (
		'data'
		,'file_name'
		,'index_record'
		,'is_location'
		,'is_mp'
		,'location'
		,'mp_uuids'
		,'photo_dir'
		,'photo_uuid'
		,'tags'
	)



	########################################################################
	# Properties
	########################################################################
	
	@property
	def photo_file(self):
		'''
		Read-only property for fully qualified photo file name
		'''
	
		return os.path.abspath(
			os.path.join(
				self.photo_dir
				,self.file_name
			)
		)
	
	
	
	########################################################################
	# Instance methods
	########################################################################


	#
	# Public
	#

	def __init__(
		self
		,index_record # IndexRecord
		,photo_dir
	):

		logging.debug(f'Initializing {__class__.__name__}')



		# Store source data values

		self.index_record = index_record
		self.photo_dir = photo_dir



		# Create instance attributes
		
		self._initialize_attributes()
		
		
		
		# Process source data into instance attributes
		
		self.transform()



	def __str__(self):

		return json.dumps(
			self.asdict()
			,indent = mg.JSON_INDENT
		)
	
	
	
	def asdict(self):
	
		properties = (
			'photo_file'
			,
		)
		
		
		attributes = sorted(
			self.ATTRIBUTES
			+ properties
		)
		
	
		return mg.asdict(
			object = self
			,attributes = attributes
		)



	def get_data(self):
	
		photo_file = open(
			self.photo_file
			,'rb'
		)
		
		self.data = photo_file.read()
	

	
	def transform(self):
	
		# Run a transformation function to populate each output
		# attribute
		
		for f in (
			# Photo index record properties
			self.transform_file_name
			,self.transform_location
			,self.transform_photo_uuid
			,self.transform_tags
			# First tier derived attributes
			,self.transform_is_location
			,self.transform_is_mp
			# Second tier derived attributes
			,self.transform_mp_uuids
		):
		
			logging.debug(f'Executing: {f.__name__}')
			f()
			
			

	def transform_file_name(self):
	
		self.file_name = self.index_record.FileName
		
		
		
	def transform_is_location(self):
	
		if 'Site Photo' in self.tags:
		
			self.is_location = True
			
			
		else:
		
			self.is_location = False
			
			
			
	def transform_is_mp(self):
	
		if 'MP' in self.tags:
		
			self.is_mp = True
			
			
		else:
		
			self.is_mp = False
			
			
			
	def transform_mp_uuids(self):
	
		self.mp_uuids = []
		
		

		if self.is_mp == True:
		
			match = re.findall(
				r'''MP#([0-9a-f]{32})'''
				,mg.none2blank(self.index_record.Comment)
			)


			if len(match) == 0:

				raise ValueError(f'Measuring Point photo missing Aquarius ID of related MP: {self.file_name}')
				
				
			for mp_uuid in match:
			
				# Use UUID module to test/standardize value.
				# Store result as upper-case string to match
				# geodatabase format.

				self.mp_uuids.append(str(uuid.UUID(mp_uuid)).upper())



	def transform_location(self):
		'''
		The `Identifier` column in the photo index CSV file contains
		six-digit, zero-padded text values. arcpy determines CSV column
		types on-the-fly, however, and chooses an integer type for
		this column.
		
		We can define the column types for a CSV file by creating a
		schema.ini file in the same directory as the CSV file. To avoid
		the need for write access in this potentially protected
		location, though, we instead use our knowledge of the photo
		index file format and default arcpy CSV behavior to cast the
		integer value back to a six-character string.
		
		Note that the resulting values may or may not be identical to
		the source CSV values. For example, arcpy would ingest all of
		the following values as the integer 12345:
		
			  12345
			 012345
			0012345

		In each case, this transformer would yield the correct six-digit
		version used by the hydro geodatabase: 012345.
		'''
	
		self.location = f'{self.index_record.Identifier:06}'
		
		
		
	def transform_photo_uuid(self):
	
	
		# Standardize on geodatabase format
	
		self.photo_uuid = str(uuid.UUID(self.index_record.UniqueId)).upper()
		
	
	
	def transform_tags(self):
	
		tag_columns = re.findall(
			pattern = 'Tags_[0-9]+_Key'
			,string = str(self.index_record.fields)
		)
		
				
		self.tags = []
		
		for tag_column in tag_columns:
		
			self.tags.append(
				getattr(
					self.index_record
					,tag_column
				)
			)



	#
	# Private
	#

	def _initialize_attributes(self):

		for a in self.ATTRIBUTES:

			if not hasattr(
				self
				,a
			):
			
				setattr(
					self
					,a
					,None
				)



################################################################################
# Functions
################################################################################


#
# Public
#

def load_photos(
	index_file
	,photo_dir
	,gdb
	,feedback
):
	'''
	Read data from source files and load to target geodatabase
	'''


	#
	# Initialize metrics
	#


	# Input
	
	metrics_input = MetricsInput()
	
	metrics_input.index_failed = None # Disable counter
	
	
	
	# Output
	
	metrics_output = MetricsOutput()
	
	


	#
	# Process data
	#
	
	logging.info('Starting photo index processing')
	
	
	
	with arcpy.da.SearchCursor(
		in_table = index_file
		,field_names = '*'
	) as cursor_index:
	
		for row_index in cursor_index:
		
		
			#
			# Report feedback
			#
			
			if (
				feedback > 0 # Check first to avoid ZeroDivisionError in modulo
				and metrics_input.index_total != 0 # Skip first pass
				and metrics_input.index_total % feedback == 0
			):
			
				logging.info(f'{metrics_input}\n{metrics_output}')
				
				
				
			####################
			# Process input photo
			####################
			
			
			# Read photo index record
			
			index_record = IndexRecord(
				fields = cursor_index.fields
				,values = row_index
			)
			logging.datadebug(f'Photo index record:\n{index_record}')
			
			metrics_input.index_succeeded += 1
			
			
			
			# Gather photo metadata
			
			try:
			
				photo = Photo(
					index_record = index_record
					,photo_dir = photo_dir
				)
				logging.datadebug(f'Photo:\n{photo}')
				

			except ValueError as e:
			
				logging.warning(f'Skipping photo: {e}')
				metrics_input.metadata_failed += 1
				continue
				
				
				
			# Assess metadata properties
			
			if not (
				photo.is_location == True
				or photo.is_mp == True
			):
			
				logging.warning(f'Skipping photo: Photo not tagged for Location or Measuring Point: File {photo.file_name}')
				metrics_input.metadata_failed += 1
				continue
			
			
			
			# Log valid metadata
			
			logging.debug('Photo metadata is valid')
			metrics_input.metadata_succeeded += 1
				
				
			
			# Fetch source data from photo file
			
			try:
				photo.get_data()
				
				metrics_input.file_succeeded += 1
				
			except Exception as e:
			
				logging.warning(f'Skipping photo: Failed to fetch data from source file: File {photo.file_name}: {e}')
				metrics_input.file_failed += 1
				continue
			
			
			
			####################
			# Load photo to geodatabase
			#
			# Photo may be for either or both of Location or
			# Measuring Point
			####################
			
			logging.debug('Loading photo file as geodatabase attachment(s)')
			
			
			
			#
			# Location attachment
			#
			
			if photo.is_location == True:
			
			
				# Get attachment metadata
				
				logging.debug('Gathering Location attachment metadata')
				try:
				
					attachment = LocationAttachment(
						gdb = gdb
						,photo = photo
					)
					logging.datadebug(f'Location attachment:\n{attachment}')
				
				
				except ValueError as e:
				
					logging.warning(
						f'Failed to generate attachment metadata: Location: {photo.location} File: {photo.file_name}'
						f'\n{e}'
					)
					metrics_output.location_failed += 1
					continue
				
				
					
				# Load attachment
				
				logging.debug('Loading Location attachment')
				
				errors = attachment.load()
					
				if len(errors) > 0:
				
					for error in errors:
					
						logging.warning(
							f'Failed to load attachment: Location: {photo.location} File: {photo.file_name}'
							f'\n{error}'
						)
						metrics_output.location_failed += 1
					
					
					continue
				
				
				else:
				
					logging.debug('Loaded Location attachment')
					metrics_output.location_succeeded += 1
				
				
				
			#
			# Measuring Point attachment
			#
			
			if photo.is_mp == True:
			
			
				# Get attachment metadata
				
				logging.debug('Gathering Measuring Point attachment metadata')
				try:
				
					attachment = MPAttachment(
						gdb = gdb
						,photo = photo
					)
					logging.datadebug(f'Measuring Point attachment:\n{attachment}')
				
				
				except ValueError as e:
				
					logging.warning(
						f'Failed to generate attachment metadata: Location: {photo.location} File: {photo.file_name}'
						f'\n{e}'
					)
					metrics_output.mp_failed += 1
					continue
				
				
					
				# Load attachment
				
				logging.debug('Loading Measuring Point attachments')
				
				errors = attachment.load()
					
				if len(errors) > 0:
				
					for error in errors:
				
						logging.warning(
							f'Failed to load attachment: Location: {photo.location} File: {photo.file_name}'
							f'\n{error}'
						)
						metrics_output.mp_failed += 1
						
					
					continue
					
					
				else:
				
					logging.debug('Loaded Measuring Point attachments')
					metrics_output.mp_succeeded += 1
				
				
				
	#
	# Final feedback message
	#
	
	logging.info('Finished processing photos')
	
	logging.info(f'{metrics_input}\n{metrics_output}')



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
		,description = 'Load asset and configuration data to hydro geodatabase'
	)



	g = ap.add_argument_group( # Avoid all named arguments being listed as 'optional' in help
		'Arguments'
	)



	g.add_argument(
		'-i'
		,'--index-file'
		,dest = 'index_file'
		,help = 'Photo index file'
		,metavar = '<index_file>'
		,required = True
	)

	g.add_argument(
		'-d'
		,'--photo-dir'
		,dest = 'photo_dir'
		,help = 'Photo directory'
		,metavar = '<photo_dir>'
		,required = True
	)

	g.add_argument(
		'-g'
		,'--gdb-server'
		,dest = 'gdb_server'
		,help = 'Geodatabase server'
		,metavar = '<geodatabase_server>'
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
		,help = 'Feedback interval for progress metrics (number of Locations processed); 0 to disable'
		,metavar = '<feedback>'
		,required = False
		,type = int
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
		f'Hydrologic Geodatabase Photo Loader\n'
		f'{mg.BANNER_DELIMITER_2}\n'
		f'Photo index file:                  {args.index_file}\n'
		f'Photo directory:                   {args.photo_dir}\n'
		f'Geodatabase server:                {args.gdb_server}\n'
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



	#
	# Verify feedback
	#

	if not args.feedback >= 0:

		raise ValueError('Feedback interval must be greater or equal to zero')



	# Standardize paths
	#
	# Relative paths break some arcpy functionality (e.g. accessing Excel
	# tables) so force all paths to absolute

	index_file = os.path.abspath(args.index_file)
	photo_dir = os.path.abspath(args.photo_dir)



	#
	# Return
	#

	return (
		args
		,index_file
		,photo_dir
	)



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

		(
			args
			,index_file
			,photo_dir
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
		) = _connect_gdb(args.gdb_server)


	except RuntimeError as e:

		logging.error(e)

		sys.exit(mg.EXIT_FAILURE)



	#
	# Load data
	#

	load_photos(
		index_file = index_file
		,photo_dir = photo_dir
		,gdb = gdb
		,feedback = args.feedback
	)



	#
	# Cleanup
	#

	logging.info('Done.')




################################################################################
# END
################################################################################