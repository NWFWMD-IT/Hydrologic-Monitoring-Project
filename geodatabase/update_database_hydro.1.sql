--------------------------------------------------------------------------------
-- Name:
--	update_database_hydro.1.sql
--
-- Purpose:
--	Update existing hydro geodatabase to:
--
--		- Add user HQ\hydro_admin
--
-- Environment:
--	ArcGIS Enterprise 11.3
--	SQL Server 2019
--
-- Notes:
--	none
--
-- History:
--	2025-04-20 MCM Created (#217)
--
-- To do:
--	none
--
-- Copyright 2003-2025. Mannion Geosystems, LLC. http://www.manniongeo.com
--------------------------------------------------------------------------------

USE [hydro]

GO


CREATE USER [HQ\hydro_admin]
WITH
	DEFAULT_SCHEMA = [dbo]
;

GO


GRANT -- For I-table procedures
	EXECUTE
ON SCHEMA::[hydro]
TO
	[HQ\hydro_admin]
;

GO


ALTER ROLE [db_datareader]
ADD MEMBER [HQ\hydro_admin]
;

GO


ALTER ROLE [db_datawriter]
ADD MEMBER [HQ\hydro_admin]
;

GO


--------------------------------------------------------------------------------
-- END
--------------------------------------------------------------------------------
