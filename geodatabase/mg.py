################################################################################
# Name:
#	mg.py
#
# Purpose:
#	Shared Python objects for Mannion Geosystems modules
#
# Environment:
#	Python 3.9.11
#
# Notes:
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

import copy
import logging



################################################################################
# Constants
################################################################################


#
# Exit codes
#

EXIT_FAILURE = -1



#
# Console banner
#

BANNER_WIDTH = 80
BANNER_DELIMITER_1 = '=' * BANNER_WIDTH
BANNER_DELIMITER_2 = '-' * BANNER_WIDTH



#
# Diagnostic log
#

LOG_FORMAT = '%(asctime)s.%(msecs)-3d %(levelname)-9s %(message)s' # msecs occasionally returns two digits instead of three; right-pad with space character to preserve alignment, if necessary
LOG_FORMAT_DATE = '%Y-%m-%d %H:%M:%S'
LOG_INDENT = 34 # For indenting multi-line messages; currently set to line header length
LOG_LEVEL_DATA = logging.DEBUG - 1
LOG_LEVEL_DATADEBUG = logging.DEBUG - 2




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
		
		r.msg = str(r.msg).replace(
			'\n'
			,f'\n{" " * LOG_INDENT}'
		)


		return super().format(r)



################################################################################
# END
################################################################################
