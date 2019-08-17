# mapexport-qgis3
A QGIS 3 plugin which exports and zips up a PDF, JPG, and metadata file for a selected Print Layout.

This plugin is a QGIS implementation of MapAction's ArcGIS MapExport toolset, which prepares map filesets and metadata for upload to online repositories.

This is what it does:
1. Using a MapAction template, the user enters/edits values for the custom variables in the Item Properties dialogue, then prepares the Layout for publication. These variables also populate most of the marginalia in the template.
2. The user launches the plugin, selects the Layout to export and an export location, and clicks export.
3. The plugin exports a PDF and JPG version of the Layout to a new folder with the same name as the Composer.
4. The plugin creates an XML metadata file in the same folder, populated with the variable values the user has entered.
5. The plugin creates a zip of the  the folder with the same name.

This plugin is in beta - full help documentation will be added in due course.

For testing, a QGIS project containing the MapAction templates is stored in the 'test' folder of the plugin.

## Issues
This is the initial conversion from the QGIS 2 version - the basic export functionality should work but is by no means production ready. The metadata editing UI is not working yet, and it needs a good tidy up. 

The main map object in the Layout must have an id 'main'.
