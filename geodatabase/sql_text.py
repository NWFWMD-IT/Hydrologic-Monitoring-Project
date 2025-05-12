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
WITH lv AS (
	SELECT
		*
		,RANK () OVER (
			PARTITION BY
				LocationGlobalID
			ORDER BY
				VisitDate DESC
		) _rank
	FROM hydro.LocationVisit_EVW
)
,li AS (
	SELECT
		lv.LocationGlobalID
		,COUNT(*) IssueCount
	FROM hydro.LocationIssue_EVW li
	INNER JOIN hydro.LocationVisit_EVW lv ON
		li.LocationVisitGlobalID = lv.GlobalID
	WHERE
		li.IsActive = 'Yes'
	GROUP BY
		lv.LocationGlobalID
)
SELECT
	l.ObjectID ID
	,l.Shape
	,l.GDB_GEOMATTR_DATA
	,l.NWFID
	,l.Name
	,l.Project
	,l.FLUWID
	,l.HasDataLogger
	,l.HasSensor
	,l.HasMeasuringPoint
	,l.HasRainfall
	,l.HasStage
	,l.HasGroundwater
	,l.HasConductivity
	,l.HasADVM
	,l.HasDischarge
	,l.HasTemperature
	,l.HasWaterQuality
	,l.Comments LocationComments
	,l.GlobalID LocationGlobalID
	,lv.VisitDate
	,lv.Staff
	,lv.StaffComments
	,lv.EquipmentChange
	,lv.BatteryDOA
	,lv.BatteryLevel
	,lv.BatteryLevel2
	,lv.BatteryReplaced
	,lv.BatteryReplacementDate
	,lv.BatteryReplacementException
	,lv.BatteryReplacementComments
	,lv.DesiccantEnclosure
	,lv.DesiccantSensor
	,lv.DesiccantComments
	,lv.DataLoggerRecordStart
	,lv.DataLoggerRecordEnd
	,lv.DataLoggerTime
	,lv.DataLoggerTimeActual
	,lv.DataLoggerTimeAdjAmount
	,lv.DataLoggerTimeAdjusted
	,lv.DataLoggerTimeAdjDate
	,lv.DataLoggerTimeAdjException
	,lv.DataLoggerTimeAdjComments
	,lv.DataLoggerTime2
	,lv.DataLoggerTimeActual2
	,lv.DataLoggerTimeAdjAmount2
	,lv.DataLoggerTimeAdjusted2
	,lv.DataLoggerTimeAdjDate2
	,lv.DataLoggerTimeAdjException2
	,lv.DataLoggerTimeAdjComments2
	,lv.RainfallBucketCleaned
	,lv.RainfallBucketException
	,lv.RainfallBucketComments
	,lv.RainfallMechanismChecked
	,lv.RainfallMechanismException
	,lv.RainfallMechanismComments
	,lv.ADVMRecordStart
	,lv.ADVMRecordEnd
	,lv.ADVMDischarge_RecordStart
	,lv.ADVMDischarge_RecordEnd
	,lv.ADVMBeamCheckedInitial
	,lv.ADVMBeamCheckInitialException
	,lv.ADVMBeamCheckInitialComments
	,lv.ADVMBeamCheckedSecondary
	,lv.ADVMBeamCheckSecondaryException
	,lv.ADVMBeamCheckSecondaryComments
	,lv.ADVMCleaned
	,lv.ADVMCleanedException
	,lv.ADVMCleanedComments
	,lv.ADVMMaintenance
	,lv.ADVMMaintenanceComments
	,lv.DischargeRecordStart
	,lv.DischargeRecordEnd
	,lv.DischargeVolume
	,lv.DischargeUncertainty
	,lv.WaterQualitySensorPulled
	,lv.WaterQualitySensorPullDate
	,lv.WaterQualityPurgeStart
	,lv.WaterQualitySamplingEnd
	,lv.WaterQualitySensorReinstallDate
	,lv.GlobalID LocationVisitGlobalID
	,lv.Employee LocationVisitEmployee
	,lv.EditTimestamp LocationVisitEditTimestamp
	,li.IssueCount
FROM hydro.Location_EVW l
LEFT JOIN lv ON
	l.GlobalID = lv.LocationGlobalID
LEFT JOIN li ON
	l.GlobalID = li.LocationGlobalID
WHERE
	lv._rank = 1
'''



################################################################################
# END
################################################################################
