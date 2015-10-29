#!/usr/bin/env python

import arcpy
from arcpy import env

WORKSPACE_PATH=""  # add workspace path from windows machine

# define workspace and high level container
env.workspace = r"{}".format(WORKSPACE_PATH)

feature_classes = arcpy.ListFeatureClasses("*", "All")

# fields that I want to delete
# feel free to update the tuple and include
# fields that need to be removed from the feature classes
fileds_to_delete = ("CREATEDBY", "CREATEDATE")


for feature_class in feature_classes:
    # we need to create a list of field names that are in
    # the feature class
    field_names = [fl.name for fl in arcpy.ListFields(feature_class)]

    # For each filed in the list of fields to delete
    # we need to verify if the filed exist in feature class.
    # This has to be done before we attemp to delete field
    # that may not be present in the class (this will return
    # errori).
    for field in fields_to_delete:
        if field in field_names:
            # if the filed that has to be deleted
            # is in the field names of the feature class
            # than we delete the field
            arcpy.DeleteField_management(feature_class, field)


# If we  want to print out fields to make sure
# they have been deleted run this code (or comment it)

lfc = arcpy.ListFeatureClasses("*", "All")
for l in lfc:
    fields = arcpy.ListFields(l)
    for f in fields:
        # It will print current field (after deletion)
        print f.name
