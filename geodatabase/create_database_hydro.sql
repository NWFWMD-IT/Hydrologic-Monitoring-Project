--------------------------------------------------------------------------------
-- Name:
--	configure_database_hydro.sql
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
--	Shared administrative accounts use SQL Server authentication.
--
--	End user accounts use Windows authentication
--
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
-- History:
--	2022-07-18 MCM Created
--
-- To do:
--	Localize for NWFWMD environment:
--
--		Update file paths
--
--		Add end users
--
-- Copyright 2003-2022. Mannion Geosystems, LLC. http://www.manniongeo.com
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Database
--------------------------------------------------------------------------------

CREATE DATABASE [hydro]
CONTAINMENT = PARTIAL
ON PRIMARY (
	NAME = 'hydro_01.mdf'
	,FILENAME = 'C:\data\sqldata\MSSQLSERVER\hydro\hydro_01.mdf'
	,SIZE = 16 GB
	,MAXSIZE = UNLIMITED
	,FILEGROWTH = 4 GB
)
LOG ON (
	NAME = 'hydro_01.ldf'
	,FILENAME = 'C:\data\sqldata\MSSQLSERVER\hydro\hydro_01.ldf'
	,SIZE = 1 GB
	,MAXSIZE = 16 GB
	,FILEGROWTH = 1 GB
)
WITH
	DB_CHAINING OFF
	,TRUSTWORTHY OFF
;



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
WITH
	PASSWORD = 'sde'
	,DEFAULT_SCHEMA = [sde]
;



RAISERROR(
	'***** Change password for [sde] user *****'
	,0
	,0
)
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
WITH
	PASSWORD = 'hydro'
	,DEFAULT_SCHEMA = [hydro]
;



RAISERROR(
	'***** Change password for [hydro] user *****'
	,0
	,0
)
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

CREATE USER [mapserver]
WITH
	PASSWORD = 'mapserver'
	,DEFAULT_SCHEMA = [dbo]
;



RAISERROR(
	'***** Change password for [mapserver] user *****'
	,0
	,0
)
;


GO



ALTER ROLE db_datareader
ADD MEMBER [mapserver]
;

GO


ALTER ROLE db_datawriter
ADD MEMBER [mapserver]
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
-- END
--------------------------------------------------------------------------------
