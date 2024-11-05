import arcpy
# import getpass

# arcpy.SignInToPortal(
	# portal_url = 'https://apollo.manniongeo.com/portal'
	# ,username = 'portaladmin'
	# ,password = getpass.getpass('Password: ')
# )


# Reference existing map

project = arcpy.mp.ArcGISProject('CURRENT')
map = project.listMaps()[0]



# Configure sharing

draft = map.getWebLayerSharingDraft(
	server_type = 'FEDERATED_SERVER'
	,service_type = 'MAP_IMAGE'
	,service_name = 'HydroServiceScriptTest'
)

draft.federatedServerUrl = 'https://apollo.manniongeo.com/server'
draft.portalFolder = 'Hydro'
draft.serverFolder = 'Hydro'
draft.overwriteExistingService = True
draft.tags = 'test'
draft.summary = 'test'
draft.credits = 'test'
draft.description = 'test'
draft.useLimitations = 'test'



# Publish service

file_sddraft = r'Z:/manniongeo/projects/nwfwmd/2015-01-13_gis_support/github/Hydrologic-Monitoring-Project/geodatabase/hydro.sddraft'
file_sd = 'Z:/manniongeo/projects/nwfwmd/2015-01-13_gis_support/github/Hydrologic-Monitoring-Project/geodatabase/hydro.sd'

draft.exportToSDDraft(file_sddraft)
print(arcpy.GetMessages(1))

arcpy.server.StageService(
	in_service_definition_draft = file_sddraft
	,out_service_definition = file_sd
)
print(arcpy.GetMessages(1))

service = arcpy.server.UploadServiceDefinition(
	in_sd_file = file_sd
	,in_server = draft.federatedServerUrl
)
print(arcpy.GetMessages(1))