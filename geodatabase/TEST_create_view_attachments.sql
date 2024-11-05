DROP VIEW IF EXISTS hydro.attachments;
GO


CREATE VIEW hydro.attachments AS
WITH la AS (
	SELECT
		rel_globalid
		,'x' location_attachment
	FROM hydro.location__attach_evw la
)
,mp AS (
	SELECT
		mp.locationglobalid
		,'x' mp_attachment
	FROM hydro.measuringpoint_evw mp
	INNER JOIN hydro.measuringpoint__attach_evw mpa ON
		mp.globalid = mpa.rel_globalid
)
SELECT
	DISTINCT
	CAST(nwfid AS INT) objectid
	,l.nwfid
	,la.location_attachment
	,mp.mp_attachment
FROM hydro.location_evw l
LEFT JOIN la ON
	l.globalid = la.rel_globalid
LEFT JOIN mp ON
	l.globalid = mp.locationglobalid
WHERE
	la.location_attachment IS NOT NULL
	OR mp.mp_attachment IS NOT NULL
;
GO


SELECT
	objectid
	,nwfid
	,location_attachment
	,mp_attachment
FROM hydro.attachments
ORDER BY
	nwfid
;
GO
