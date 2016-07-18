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
      type - the type of the handle. This should always be shock.
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
       unpack - either null, 'uncompress', or 'unpack'. 'uncompress' will cause
           any bzip or gzip files to be uncompressed. 'unpack' will behave the
           same way, but it will also unpack tar and zip archive files
           (uncompressing gzipped or bzipped archive files if necessary). If
           'uncompress' is specified and an archive file is encountered, an
           error will be thrown. If the file is an archive, it will be
           unbundled into the directory containing the original output file.
           
           Note that if the file name (either as provided by the user or by
           Shock) without the a decompression extension (e.g. .gz, .zip or
           .tgz -> .tar) points to an existing file and unpack is specified,
           that file will be overwritten by the decompressed Shock file.
    */
    typedef structure {
        string shock_id;
        string file_path;
        string unpack;
    } ShockToFileParams;

    /* Output from the shock_to_file function.
    
       node_file_name - the filename of the file as stored in Shock.
       file_path - the path to the downloaded file. If a directory was
           specified in the input, this will be the directory appended with the
           shock file name. If a file was specified, it will be that file path.
           In either case, if the file is uncompressed any compression file
           extensions will be removed (e.g. .gz) and or altered (e.g. .tgz ->
           .tar) as appropriate.
       size - the size of the file in bytes as stored in Shock, prior to
           unpacking.
       attributes - the file attributes, if any, stored in Shock.
    */
    typedef structure {
        string node_file_name;
        string file_path;
        int size;
        mapping<string, UnspecifiedObject> attributes;
    } ShockToFileOutput;

    /* Download a file from Shock. */
    funcdef shock_to_file(ShockToFileParams params)
        returns (ShockToFileOutput out) authentication required;

    /* Download multiple files from Shock. */
    funcdef shock_to_file_mass(list<ShockToFileParams> params)
        returns(list<ShockToFileOutput> out) authentication required;

    /* Input for the file_to_shock function.
       
       Required parameters:
       file_path - the location of the file to load to Shock.
       
       Optional parameters:
       attributes - user-specified attributes to save to the Shock node along
           with the file.
       make_handle - make a Handle Service handle for the shock node. Default
           false.
       pack - compress a file or archive a directory before loading to Shock.
           In all cases, the file specified in the file_path argument is
           required and will be appended with the appropriate file extension
           prior to writing. If the file extension denotes that the file is
           already packed, it will be skipped. The allowed values are:
               gzip - gzip the file given by file_path.
               targz - tar and gzip the directory specified by the file_path
                   into the file specified by the file path.
               zip - as targz but zip the directory. 
    */
    typedef structure {
        string file_path;
        mapping<string, UnspecifiedObject> attributes;
        boolean make_handle;
        string pack;
    } FileToShockParams;

    /* Output of the file_to_shock function.
    
        shock_id - the ID of the new Shock node.
        handle - the new handle, if created. Null otherwise.
        node_file_name - the name of the file stored in Shock.
        size - the size of the file stored in shock.
    */
    typedef structure {
        string shock_id;
        Handle handle;
        string node_file_name;
        string size;
    } FileToShockOutput;

    /* Load a file to Shock. */
    funcdef file_to_shock(FileToShockParams params)
        returns (FileToShockOutput out) authentication required;
    
    /* Load multiple files to Shock. */
    funcdef file_to_shock_mass(list<FileToShockParams> params)
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

    /* Input for the own_shock_node function.

       Required parameters:
       shock_id - the id of the node for which the user needs ownership.
       
       Optional parameters:
       make_handle - make or find a Handle Service handle for the shock node.
           Default false.
    */
    typedef structure {
        string shock_id;
        boolean make_handle;
    } OwnShockNodeParams;
    
    /* Output of the own_shock_node function.
      
       shock_id - the id of the (possibly new) Shock node.
       handle - the handle, if requested. Null otherwise.
    */
    typedef structure {
        string shock_id;
        Handle handle;
    } OwnShockNodeOutput;
    
    /* Gain ownership of a Shock node.
        
        Returns a shock node id which is owned by the caller, given a shock
        node id.
        
        If the shock node is already owned by the caller, returns the same
        shock node ID. If not, the ID of a copy of the original node will be
        returned.
        
        If a handle is requested, the node is already owned by the caller, and
        a handle already exists, that handle will be returned. Otherwise a new
        handle will be created and returned.
     */
    funcdef own_shock_node(OwnShockNodeParams params)
        returns(OwnShockNodeOutput out) authentication required;

    /* Translate a workspace name to a workspace ID. */
    funcdef ws_name_to_id(string name) returns(int id) authentication required;

    /* Information about an object, including user provided metadata.
    
        objid - the numerical id of the object.
        name - the name of the object.
        type - the type of the object.
        save_date - the save date of the object.
        ver - the version of the object.
        saved_by - the user that saved or copied the object.
        wsid - the id of the workspace containing the object.
        workspace - the name of the workspace containing the object.
        chsum - the md5 checksum of the object.
        size - the size of the object in bytes.
        meta - arbitrary user-supplied metadata about
            the object.

    */
    typedef tuple<int objid, string name, string type, string save_date,
        int version, string saved_by, int wsid, string workspace, string chsum,
        int size, mapping<string, string> meta> object_info;

    /* An object and associated data required for saving.
    
        Required parameters:
        type - the workspace type string for the object. Omit the version
            information to use the latest version.
        data - the object data.
        
        Optional parameters:
        One of an object name or id. If no name or id is provided the name
            will be set to 'auto' with the object id appended as a string,
            possibly with -\d+ appended if that object id already exists as a
            name.
        name - the name of the object.
        objid - the id of the object to save over.
        meta - arbitrary user-supplied metadata for the object,
            not to exceed 16kb; if the object type specifies automatic
            metadata extraction with the 'meta ws' annotation, and your
            metadata name conflicts, then your metadata will be silently
            overwritten.
        hidden - true if this object should not be listed when listing
            workspace objects.
    
    */
    typedef structure {
        string type;
        UnspecifiedObject data;
        string name;
        int objid;
        mapping<string, string> meta;
        boolean hidden;
    } ObjectSaveData;
    
    /* Input parameters for the "save_objects" function.
    
        Required parameters:
        id - the numerical ID of the workspace.
        objects - the objects to save.
        
        The object provenance is automatically pulled from the SDK runner.
    */
    typedef structure {
        int id;
        list<ObjectSaveData> objects;
    } SaveObjectsParams;
    
    /* 
        Save objects to the workspace. Saving over a deleted object undeletes
        it.
    */
    funcdef save_objects(SaveObjectsParams params)
        returns (list<object_info> info) authentication required;

    /* Input parameters for the "get_objects" function.
    
        Required parameters:
        object_refs - a list of object references in the form X/Y/Z, where X is
            the workspace name or id, Y is the object name or id, and Z is the
            (optional) object version. In general, always use ids rather than
            names if possible to avoid race conditions.
        
        Optional parameters:
        ignore_errors - ignore any errors that occur when fetching an object
            and instead insert a null into the returned list.
    */
    typedef structure {
        list<string> object_refs;
        boolean ignore_errors;
    } GetObjectsParams;
    
    /* The data and supplemental info for an object.
    
        UnspecifiedObject data - the object's data or subset data.
        object_info info - information about the object.
    */
    typedef structure {
        UnspecifiedObject data;
        object_info info;
    } ObjectData;
    
    /* Results from the get_objects function.
    
        list<ObjectData> data - the returned objects.
    */
    typedef structure {
        list<ObjectData> data;
    } GetObjectsResults;
    
    /* Get objects from the workspace. */
    funcdef get_objects(GetObjectsParams params)
        returns(GetObjectsResults results) authentication required;

    /* Get the versions of the Workspace service and Shock service. */
    funcdef versions() returns(string wsver, string shockver)
        authentication required;
};
