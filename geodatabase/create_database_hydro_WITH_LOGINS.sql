--------------------------------------------------------------------------------
-- Temporary workaround for create_database_hydro.sql until Esri Support case
-- #03150260 is resolved
--
-- Uses login-based users instead of contained database users for system/service
-- accounts.
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Logins
--
-- For object owners only. Readers/editors are contained database users.
--------------------------------------------------------------------------------

USE [master]
GO


-- Geodtabase administrator

IF NOT EXISTS (
	SELECT
		sid
	FROM sys.server_principals
	WHERE
		name = 'HQ\sde'
)
	CREATE LOGIN [HQ\sde]
	FROM WINDOWS
;



-- Data owner

IF NOT EXISTS (
	SELECT
		sid
	FROM sys.server_principals
	WHERE
		name = 'HQ\hydro'
)
	CREATE LOGIN [HQ\hydro]
	FROM WINDOWS
;



--------------------------------------------------------------------------------
-- Database
--------------------------------------------------------------------------------

CREATE DATABASE [hydro]
CONTAINMENT = PARTIAL
ON PRIMARY (
	NAME = 'hydro_01.mdf'
	,FILENAME = 'D:\sqldata\MSSQLSERVER\hydro_01.mdf'
	,SIZE = 16 GB
	,MAXSIZE = UNLIMITED
	,FILEGROWTH = 4 GB
)
LOG ON (
	NAME = 'hydro_01.ldf'
	,FILENAME = 'D:\sqldata\MSSQLSERVER\hydro_01.ldf'
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
-- END
--------------------------------------------------------------------------------
