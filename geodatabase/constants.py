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
#
# To do:
#	none
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
# Operating system users
#

OS_USERNAMES_HYDRO = (
	'HQ\HYDRO' # NWFWMD production
	,'CITRA\HYDRO' # MannionGeo development
	,'PORTER\HYDRO' # MannionGeo development
)

OS_USERNAMES_SDE = (
	'HQ\SDE' # NWFWMD production
	,'CITRA\SDE' # MannionGeo development
	,'PORTER\SDE' # MannionGeo development
)



#
# Spatial references
#

SR_UTM16N_NAD83 = arcpy.SpatialReference(26916) # NAD_1983_UTM_Zone_16N


################################################################################
# END
################################################################################
