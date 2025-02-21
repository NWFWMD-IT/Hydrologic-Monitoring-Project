################################################################################
# Name:
#	constants.py
#
# Purpose:
#	Store constants used by hydro database deployment modules
#
# Environment:
#	ArcGIS Pro 3.4.2
#	Python 3.11.10, with:
#		arcpy 3.4 (build py311_arcgispro_55347)
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
#	2023-03-13 MCM Replace OS_USERNAMES_* constants
#	2024-10-22 MCM Added EXTENT_DISTRICT (#191)
#	2025-02-01 MCM Add source table names (#188)
#
# To do:
#	none
#
# Copyright 2003-2025. Mannion Geosystems, LLC. http://www.manniongeo.com
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
# Source table names
#

TABLE_NAME_LOCATION = 'aq_stations_inventory'
TABLE_NAME_MONITORING = 'district_monitoring'
TABLE_NAME_MEASURING_POINT = 'reference_points'



#
# Spatial references
#

SR_UTM16N_NAD83 = arcpy.SpatialReference(26916) # NAD_1983_UTM_Zone_16N
EXTENT_DISTRICT = '439316 3274624 809752 3431406'


################################################################################
# END
################################################################################
