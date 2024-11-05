DROP VIEW IF EXISTS hydro.attachment_count;
GO


CREATE VIEW hydro.attachment_count AS
WITH la AS (
	SELECT
		rel_globalid
		,COUNT(rel_globalid) location_attachments
	FROM hydro.location__attach_evw la
	GROUP BY
		rel_globalid
)
,mp AS (
	SELECT
		mp.locationglobalid
		,COUNT(mp.locationglobalid) mp_attachments
	FROM hydro.measuringpoint_evw mp
	INNER JOIN hydro.measuringpoint__attach_evw mpa ON
		mp.globalid = mpa.rel_globalid
	GROUP BY
		mp.locationglobalid
)
SELECT
	l.nwfid
	,la.location_attachments
	,mp.mp_attachments
FROM hydro.location_evw l
LEFT JOIN la ON
	l.globalid = la.rel_globalid
LEFT JOIN mp ON
	l.globalid = mp.locationglobalid
WHERE
	la.location_attachments IS NOT NULL
	OR mp.mp_attachments IS NOT NULL
;
GO


SELECT
	nwfid
	,location_attachments
	,mp_attachments
FROM hydro.attachment_count
ORDER BY
	nwfid
;
GO
