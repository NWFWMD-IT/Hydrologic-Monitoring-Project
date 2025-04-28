################################################################################
# Name:
#	sql_text.py
#
# Purpose:
#	Store lengthy SQL text in a module, for reference by deployment scripts
#
# Environment:
#	SQL Server 2019
#	ArcGIS Pro 3.4.2
#	Python 3.11.10, with:
#		arcpy 3.4 (build py311_arcgispro_55347)
#
# Notes:
#	The SQL text required to perform some Hydrologic Monitoring data model
#	configuration activities is lengthy, especially when formatted for
#	human readability. These long strings can make it difficult to work
#	with other Python modules when embedded directly within them. Therefore,
#	this module stores the text of such SQL statements - and nothing else.
#	This advantages other scripts by removing the cumbersome strings, and
#	simplifies the structure of this module by storing nothing but the
#	strings.
#
#	Other scripts can import this module and reference the relevant SQL
#	by their respective variable names.
#
# History:
#	2024-10-22 MCM Created (#191)
#	2025-04-25 MCM Add column SQL_VIEW_LOCATIONLASTVISIT.IssueCount (#202)
#
# To do:
#	none
#
# Copyright 2003-2025. Mannion Geosystems, LLC. http://www.manniongeo.com
################################################################################


SQL_VIEW_LOCATIONLASTVISIT = '''
WITH li (
	LocationGlobalID
	,IssueCount
) AS (
	SELECT
		lv.LocationGlobalID
		,COUNT(*)
	FROM hydro.LocationIssue_EVW li
	INNER JOIN hydro.LocationVisit_EVW lv ON
		li.LocationVisitGlobalID = lv.GlobalID
	WHERE
		li.IsActive = 'Yes'
	GROUP BY
		lv.LocationGlobalID
)
,lv (
	LocationGlobalID
	,LastVisit
) AS (
	SELECT
		LocationGlobalID
		,MAX(VisitDate)
	FROM hydro.LocationVisit_EVW
	GROUP BY
		LocationGlobalID
)
SELECT
	l.Shape
	,l.ObjectID ID
	,l.NWFID
	,l.Name
	,lv.LastVisit
	,li.IssueCount
FROM hydro.Location_EVW l
LEFT JOIN lv ON
	l.GlobalID = lv.LocationGlobalID
LEFT JOIN li ON
	l.GlobalID = li.LocationGlobalID
'''



################################################################################
# END
################################################################################
