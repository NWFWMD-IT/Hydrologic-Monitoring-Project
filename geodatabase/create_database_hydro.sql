--------------------------------------------------------------------------------
-- Name:
--	create_database_hydro.sql
--
-- Purpose:
--	Create SQL Server database [hydro] and configure for hosting a
--	geodatabase
--
-- Environment:
--	ArcGIS Enterprise 10.8.1
--	SQL Server 2019
--
-- Notes:
--
--	AUTHENTICATION
--
--	[hydro] database users are based on Windows users and groups in the
--	NWFWMD `HQ` domain. The following domain accounts must exist before
--	running this script:
--
--		Users
--			arcgis
--			hydro
--			sde
--
--		Groups
--			<none>
--
--
--	CONTAINMENT
--
--	All users are created as contained database users, per current Microsoft
--	recommendations, and to facilitate deploying during data model
--	development and testing.
--
--	In the target SQL Server release, contained authentication is disabled
--	by default at the instance level. Enabling contained authentication is
--	required before running this script. To enable this feature, run the
--	following statements:
--
--		sp_configure 'contained database authentication',  1;
--
--		RECONFIGURE;
--
--	Enabling contained authentication affects various security and
--	functional aspects of the instance/database. Therefore, this script does
--	not attempt to automatically enable contained authentication and
--	instead defers to a separate, preliminary decision/action, presumably
--	with informed consideration by the administrator.
--
--
--	DEVELOPMENT
--
--	To run in the development environment, find and replace:
--
--		D:\sqldata		C:\data\sqldata
--		HQ\			CITRA\
--
-- History:
--	2022-07-18 MCM Created
--	2022-09-13 MCM Change users from database to Windows authentication (Hydro #17)
--	               Updated file paths for NWFWMD production environment
--	2022-12-14 MCM Switch to [master] at end, to facilitae development testing
--	2023-04-25 MCM Moved data/log files to `hydro` directory
--
-- To do:
--	Localize for NWFWMD environment:
--		Add end users
--
-- Copyright 2003-2023. Mannion Geosystems, LLC. http://www.manniongeo.com
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Database
--------------------------------------------------------------------------------

CREATE DATABASE [hydro]
CONTAINMENT = PARTIAL
ON PRIMARY (
	NAME = 'hydro_01.mdf'
	,FILENAME = 'D:\sqldata\MSSQLSERVER\hydro\hydro_01.mdf'
	,SIZE = 16 GB
	,MAXSIZE = UNLIMITED
	,FILEGROWTH = 4 GB
)
LOG ON (
	NAME = 'hydro_01.ldf'
	,FILENAME = 'D:\sqldata\MSSQLSERVER\hydro\hydro_01.ldf'
	,SIZE = 1 GB
	,MAXSIZE = 16 GB
	,FILEGROWTH = 1 GB
)
WITH
	DB_CHAINING OFF
	,TRUSTWORTHY OFF
;

GO



ALTER DATABASE [hydro]
SET
	AUTO_CLOSE OFF
	,AUTO_CREATE_STATISTICS ON
	,AUTO_SHRINK OFF
	,AUTO_UPDATE_STATISTICS ON
	,AUTO_UPDATE_STATISTICS_ASYNC ON
	,RECOVERY FULL
;

GO



ALTER DATABASE [hydro]
SET
	ALLOW_SNAPSHOT_ISOLATION ON
;

GO


ALTER DATABASE [hydro]
SET
	READ_COMMITTED_SNAPSHOT ON
;

GO



--------------------------------------------------------------------------------
-- Users
--------------------------------------------------------------------------------

USE [hydro]

GO



--
-- Shared administrative users
--


-- Geodatabase administrator

CREATE USER [sde]
FOR LOGIN [HQ\sde]
WITH
	DEFAULT_SCHEMA = [sde]
;

GO



GRANT
	CREATE FUNCTION
	,CREATE PROCEDURE
	,CREATE TABLE
	,CREATE VIEW
TO
	[sde]
;

GO



GRANT
	VIEW DEFINITION
ON
	DATABASE::[hydro]
TO
	[sde]
;

GO



-- Data owner

CREATE USER [hydro]
FOR LOGIN [HQ\hydro]
WITH
	DEFAULT_SCHEMA = [hydro]
;

GO



GRANT
	CREATE PROCEDURE
	,CREATE TABLE
	,CREATE VIEW
TO
	[hydro]
;

GO



-- Service user

CREATE USER [HQ\arcgis]
WITH
	DEFAULT_SCHEMA = [dbo]
;

GO


--
-- End users
--



--------------------------------------------------------------------------------
-- Schemas
--------------------------------------------------------------------------------

USE [hydro]

GO



--
-- Geodatabase system tables
--

CREATE SCHEMA [sde]
AUTHORIZATION [sde]
;

GO



--
-- Geodatabase data sets
--

CREATE SCHEMA [hydro]
AUTHORIZATION [hydro]
;

GO



--------------------------------------------------------------------------------
-- Cleanup
--------------------------------------------------------------------------------


-- Release lock on [hydro] database
--
-- Useful for testing, so we can immediately drop > recreate database

USE [master]

GO


--------------------------------------------------------------------------------
-- END
--------------------------------------------------------------------------------
