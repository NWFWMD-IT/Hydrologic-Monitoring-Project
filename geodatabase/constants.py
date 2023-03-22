################################################################################
# Name:
#	constants.py
#
# Purpose:
#	Store constants used by hydro database deployment modules
#
# Environment:
#	Python 3.9.11
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
#
# To do:
#	none
#
# Copyright 2003-2023. Mannion Geosystems, LLC. http://www.manniongeo.com
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


################################################################################
# END
################################################################################
