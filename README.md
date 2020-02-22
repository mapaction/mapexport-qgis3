# mapexport-qgis3
A QGIS 3 plugin which exports and zips up a PDF, JPG, and metadata file for a selected Print Layout.

This plugin is a QGIS implementation of MapAction's ArcGIS MapExport toolset, which prepares map filesets and metadata for upload to online repositories.

This is how to use it:
1. Prepare a map, ideally using a MapAction layout template (see mapaction/maptemplates-qgis repo), but it should work with any layout (at least one is needed). Alternatively use a QGIS project from the test folder.
2. Launch the plugin, select the template and populate the metadata items, the save them to the project - this stores them in project and layout variables. Add some themes (these aren't stored for now).
3. On the first tab, select a folder and export - this exports a PDF and JPG version of the layout, along with an XML metadata file, to a folder with the same name as the layout, and a zip of the folder.

This zip can be upload to MapAction's Maps and Data Repository to publish the map.

This plugin is in beta - for MapAction users, there's a link in the plugin dialog to more help.
