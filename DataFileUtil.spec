/*
Contains utilities for saving and retrieving data to and from KBase data
services. Requires Shock 0.9.6+ and Workspace Service 0.4.1+.
*/

module DataFileUtil {

    /* A boolean - 0 for false, 1 for true.
       @range (0, 1)
    */
    typedef int boolean;

    /* A handle for a file stored in Shock.
      hid - the id of the handle in the Handle Service that references this
         shock node
      id - the id for the shock node
      url - the url of the shock server
      type - the type of the handle. This should always be ‘shock’.
      file_name - the name of the file
      remote_md5 - the md5 digest of the file.
    */
    typedef structure {
      string hid;
      string file_name;
      string id;
      string url;
      string type;
      string remote_md5;
    } Handle;

    /* Input for the shock_to_file function.
       
       Required parameters:
       shock_id - the ID of the Shock node.
       file_path - the location to save the file output. If this is a
           directory, the file will be named as per the filename in Shock.

       Optional parameters:
       unpack - if the file is compressed and / or a file bundle, it will be
           decompressed and unbundled into the directory containing the
           original output file. unpack supports gzip, bzip2, tar, and zip
           files. Default false. Currently unsupported.
    */
    typedef structure {
        string shock_id;
        string file_path;
        boolean unpack;
    } ShockToFileParams;

    /* Output from the shock_to_file function.
    
       node_file_name - the filename of the file stored in Shock.
       attributes - the file attributes, if any, stored in Shock.
    */
    typedef structure {
        string node_file_name;
        mapping<string, UnspecifiedObject> attributes;
    } ShockToFileOutput;

    /* Download a file from Shock. */
    funcdef shock_to_file(ShockToFileParams params)
        returns (ShockToFileOutput out) authentication required;

    /* Download multiple files from Shock. */
    funcdef shock_to_files(list<ShockToFileParams> params)
        returns(list<ShockToFileOutput> out) authentication required;

    /* Input for the file_to_shock function.
       
       Required parameters:
       file_path - the location of the file to load to Shock.
       
       Optional parameters:
       attributes - user-specified attributes to save to the Shock node along
           with the file.
       make_handle - make a Handle Service handle for the shock node. Default
           false.
       gzip - gzip the file before loading it to Shock. This will create a
           file_path.gz file prior to upload. Default false.
    */
    typedef structure {
        string file_path;
        mapping<string, UnspecifiedObject> attributes;
        boolean make_handle;
        boolean gzip;
    } FileToShockParams;

    /* Output of the file_to_shock function.
    
        shock_id - the ID of the new Shock node.
        handle - the new handle, if created. Null otherwise.
    */
    typedef structure {
        string shock_id;
        Handle handle;
    } FileToShockOutput;

    /* Load a file to Shock. */
    funcdef file_to_shock(FileToShockParams params)
        returns (FileToShockOutput out) authentication required;
    
    /* Load multiple files to Shock. */
    funcdef files_to_shock(list<FileToShockParams> params)
        returns (list<FileToShockOutput> out) authentication required;

    /* Input for the copy_shock_node function.

       Required parameters:
       shock_id - the id of the node to copy.
       
       Optional parameters:
       make_handle - make a Handle Service handle for the shock node. Default
           false.
    */
    typedef structure {
        string shock_id;
        boolean make_handle;
    } CopyShockNodeParams;
    
    /* Output of the copy_shock_node function.
      
       shock_id - the id of the new Shock node.
       handle - the new handle, if created. Null otherwise.
    */
    typedef structure {
        string shock_id;
        Handle handle;
    } CopyShockNodeOutput;
    
    /* Copy a Shock node. */
    funcdef copy_shock_node(CopyShockNodeParams params)
        returns(CopyShockNodeOutput out) authentication required;
        
    /* Get the versions of the Workspace service and Shock service. */
    funcdef versions() returns(string wsver, string shockver);
};
