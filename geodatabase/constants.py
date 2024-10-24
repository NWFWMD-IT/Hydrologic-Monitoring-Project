################################################################################
# Name:
#	constants.py
#
# Purpose:
#	Store constants used by hydro database deployment modules
#
# Environment:
#	Python 3.9.16
#
# Notes:
#	This module stores constants for hydro database deployment python
#	scripts. This module stores general-purpose constants that are, or may
#	be, shared by multiple scripts.
#
#	Note that more generic constants are defined in the mg.py module. Those
#	constants are shared broadly by geoprocessing scripts, whereas these
#	are specific to the hydro database.
#
# History:
#	2023-02-22 MCM Created
#	2023-03-13 MCM Replaced OS_USERNAMES_* constants
#	2024-10-22 MCM Added EXTENT_DISTRICT (#191)
#
# To do:
#	none
#
# Copyright 2003-2024. Mannion Geosystems, LLC. http://www.manniongeo.com
################################################################################


################################################################################
# Modules
################################################################################

import arcpy



################################################################################
# Constants
################################################################################


#
# Database connections
#

CONNECTION_FILE_NAME = 'connection.sde'



#
# Spatial references
#

SR_UTM16N_NAD83 = arcpy.SpatialReference(26916) # NAD_1983_UTM_Zone_16N
EXTENT_DISTRICT = '439316 3274624 809752 3431406'


################################################################################
# END
################################################################################
