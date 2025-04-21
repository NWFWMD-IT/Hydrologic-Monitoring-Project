--------------------------------------------------------------------------------
-- Name:
--	create_database_hydro.sql
--
-- Purpose:
--	Create SQL Server database [hydro] and configure for hosting a
--	geodatabase
--
-- Environment:
--	ArcGIS Enterprise 11.3
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
--	USER NAMES
--
--	Adding a Windows authenticated, contained database user can be done with
--	a statement as simple as:
--
--		CREATE USER [HQ\sde]
--
--	The resulting username, however, includes the domain name. This is
--	generally acceptable for end users, but not for some administrative
--	users, including:
--
--		o Geodatabase administrator - The ArcGIS software requires this
--		  user to be called 'sde', without a domain prefix.
--
--		o Data owner - The data owner's name is visible to end users
--		  in many areas of the ArcGIS UI, such as when browsing the
--		  content of a geodatabase in ArcGIS Pro. Object names are
--		  simpler without the domain prefix, and District users are
--		  accustom to seeing the unadorned names from various legacy
--		  enterprise geodatabases.
--
--	Therefore, we use an alternate syntax when creating these users that
--	allows defining a database user name that differs from the underlying
--	Windows account name:
--
--		CREATE USER [sde]
--		FOR LOGIN [HQ\sde]
--
--	Note that the `FOR LOGIN` syntax does not create a user based on a
--	SQL Server login. Despite its name, this clause creates a Windows
--	authenticated, contained database user, as desired.
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
--	2023-08-23 MCM Add rmd_db group as end user
--	2024-05-29 MCM Add [ESRI Service] group as end user
--	2024-09-06 MCM Add [GIS_Admin] and [gis_staff] groups as end users (#192)
--	2025-04-20 MCM Add user [HQ\hydro_admmin] (#217)
--
-- To do:
--	none
--
-- Copyright 2003-2025. Mannion Geosystems, LLC. http://www.manniongeo.com
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


-- Writers

CREATE USER [HQ\hydro_admin]
WITH
	DEFAULT_SCHEMA = [dbo]
;

GO


ALTER ROLE [db_datawriter]
ADD MEMBER [HQ\hydro_admin]
;

GO



-- Readers

CREATE USER [HQ\rmd_db]
WITH
	DEFAULT_SCHEMA = [dbo]
;

GO


ALTER ROLE [db_datareader]
ADD MEMBER [HQ\rmd_db]
;

GO



CREATE USER [HQ\Esri Service]
WITH
	DEFAULT_SCHEMA = [dbo]
;

GO


ALTER ROLE [db_datareader]
ADD MEMBER [HQ\Esri Service]
;

GO



CREATE USER [HQ\GIS_Admin]
WITH
	DEFAULT_SCHEMA = [dbo]
;

GO


ALTER ROLE [db_datareader]
ADD MEMBER [HQ\GIS_Admin]
;

GO



CREATE USER [HQ\gis_staff]
WITH
	DEFAULT_SCHEMA = [dbo]
;

GO


ALTER ROLE [db_datareader]
ADD MEMBER [HQ\gis_staff]
;

GO



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
