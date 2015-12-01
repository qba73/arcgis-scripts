#The MIT License (MIT)
#Copyright (c) 2015 Jakub jarosz & Edita Laurinaviciute
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


#!/usr/bin/python

import arcpy

# Parameters provided from GUI Tool
DATABASE = arcpy.GetParameterAsText(0)          # Selected geodatabase
OUT_DATABASE = arcpy.GetParameterAsText(1)      # Selected output geodatabase
input_datasets = arcpy.GetParameterAsText(2)    # Coma-separated list of datasets to process
clip_feature = arcpy.GetParameterAsText(3)      # Selected clip feature file

# Params used when exporting database:
export = arcpy.GetParameter(4)                  # Flag to define if we export DB

export_format = arcpy.GetParameterAsText(5)     #
output_folder = arcpy.GetParameterAsText(6)     #
ext           = arcpy.GetParameterAsText(7)     #


# Map geodatabases from input to 'workspace' names
INPUT_WORKSPACE = DATABASE
OUTPUT_WORKSPACE = OUT_DATABASE

# add fields to delete to the empty tuple
FIELDS_TO_DELETE = ()


def validate(export_format, output_folder, ext):
    """Return a string that represents output feature path or file.

    Args:
      export_format (str): read from GUI, one of: MITAB, MIF, DWG_R2010, DXF_R2010
      output_folder (str): read from GUI, must be a folder path of MITAB / MIF
      ext           (str): read from GUI, must be a path to the ACAD file
    """
    
    if export_format in ('DWG_R2010', 'DXF_R2010') and ext in ('dwg', 'dxf'):
        return True
    
    elif export_format in ('MITAB', 'MIF', 'SHAPE') and output_folder != "":
        return True

    return False
        

    
def process_datasets(datasets):
    """Return a list of datasets provided as a string
       in GUI input or None if default 'All' is provided.

    Args:
      datasets (str): a string with coma-separated datasets names

    Example:
      >>> process_datasets("Data1,Data2")
      ['Data1', 'Data2']
      
    """
    if datasets != "All":
        return [dataset.strip() for dataset in datasets.split(",")]
    return None


def get_datasets(to_process=None):
    """Return a list of datasets from the given geodatabase."""
    arcpy.env.workspace = INPUT_WORKSPACE
    data_sets = arcpy.ListDatasets('*')
    
    if to_process is not None:
        listdatasets = []
        for dataset in data_sets:
            if dataset in to_process:
                listdatasets.append(dataset)
        return listdatasets
    
    return data_sets


def get_features(dataset, dont_process=None):
    """Return a list of feature classes from dataset except
       of the features listed in dont_process var (list).

    Args:
      dataset (arcpy obj)
      dont_process: list or tuple of strings

    Example:
      >>> get_features(dataset, dont_process=["wSrvConnetion"])

    """
    all_feature_classes = arcpy.ListFeatureClasses("*", "All", dataset)
    if dont_process is not None:
        # filter stuff we don't want:
        return [fclass for fclass in all_feature_classes if fclass not in dont_process]
    return all_feature_classes


def make_clip(in_feature, clip_feature, xy_tolerance=""):
    """Creates and saves clip feature."""
    arcpy.env.workspace = INPUT_WORKSPACE
    out_feature = r"{}\{}_clp".format(OUTPUT_WORKSPACE, in_feature)
    return arcpy.Clip_analysis(in_feature, clip_feature, out_feature, xy_tolerance)


def clip_features(features, clip_feature):
    """Clip feature class by study area for given list of features.
    
    Args:
      features: a list of feature classes (arcpy objects)
      clip_feature (str): name of the Clip Feature's geometry, it must be polygon

    """
    for feature in features:
        arcpy.AddMessage("Clipping feature {}".format(feature))
        make_clip(feature, clip_feature)


def remove_feature_classes():
    """Remove empty feature classes from workspace."""
    arcpy.env.workspace = OUTPUT_WORKSPACE
    feature_classes = arcpy.ListFeatureClasses("*")

    for fc in feature_classes:
        count1 = str(arcpy.GetCount_management(fc))
        if count1 == "0":
            fclass = r"{}\{}".format(OUTPUT_WORKSPACE, fc)
            arcpy.Delete_management(fclass)


def remove_fields():
    arcpy.env.workspace = OUTPUT_WORKSPACE
    feature_classes = arcpy.ListFeatureClasses("*")
   
    # fields that need to be removed from the feature classes
    fields_to_delete = FIELDS_TO_DELETE

    for feature_class in feature_classes:
        field_names = [fl.name for fl in arcpy.ListFields(feature_class)]

        for field in fields_to_delete:
            if field in field_names:
                arcpy.DeleteField_management(feature_class, field)


def cleanup():
    arcpy.AddMessage("Removing empty feature classes...")
    remove_feature_classes()
    arcpy.AddMessage("Removing restricted fields...")
    remove_fields()


def quick_export(export_format, output_folder, ext):
    """Export feature classes to CAD MapInfo.

    Args:
      output_feature (str): for example "MITAB,C:\\MyTraining\\MapInfo"
      
    """
    class LicenseError(Exception):
        """Wrapper for general Python exception."""
        pass

    try:
        # Make sure extension is installed
        if arcpy.CheckExtension("DataInteroperability") == "Available":
            arcpy.CheckOutExtension("DataInteroperability")
        else:
            raise LicenseError
    except LicenseError:
        print "Please install Data Interoperability extension!"
        print arcpy.GetMessages(0)

    arcpy.env.workspace = OUTPUT_WORKSPACE
    input_features = arcpy.ListFeatureClasses("*")

    for feature in input_features:

        if export_format in ("DWG_R2010", "DXF_R2010"):
            feature_name = '.'.join([feature.split("/")[-1].strip(), ext])
            output_feature = "{}/{}".format(output_folder, feature_name)
            arcpy.AddMessage("Exporting feature: {} to {}".format(feature, output_feature))
            arcpy.ExportCAD_conversion(feature, export_format, output_feature, "Use_Filenames_in_Tables","Overwrite_Existing_Files", "")

        elif export_format in ("MITAB", "MIF", "SHAPE"):
            output_feature = "{},{}".format(export_format, output_folder)
            arcpy.AddMessage("Exporting feature: {} to {}".format(feature, output_feature))
            arcpy.QuickExport_interop(feature, output_feature)


if __name__=="__main__":
    # Parse datasets input string
    dataset_list = process_datasets(input_datasets)

    # Retrieve datasets arc objects 
    datasets = get_datasets(to_process=dataset_list)

    # Process stuff
    for dataset in datasets:
        arcpy.AddMessage("Getting features from dataset: {}".format(dataset))
        features = get_features(dataset, dont_process=["JJGIS.wSConnection", "JJGIS.wNMeter", "JJGIS.wConnection"])
        clip_features(features, clip_feature)

    # Delete unwanted stuff
    cleanup()

    # Export files to CAD/MIF etc formats
    if export:
        # Validate user input (from GUI)
        arcpy.AddMessage("Validating input variables...")
        if not validate(export_format, output_folder, ext):
            raise ValueError("Export format {} mismatched with output folder or ext!".format())
    
        arcpy.AddMessage("Exporting...")
        quick_export(export_format, output_folder, ext)

