/*
Contains utilities for retrieving and saving data from and to KBase data
services.
*/

module DataFileUtil {

    /* A boolean - 0 for false, 1 for true.
       @range (0, 1)
    */
    typedef int boolean;

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
    funcdef shock_to_file(ShockToFileParams params) returns (ShockToFileOutput)
        authentication required;

    /* Input for the file_to_shock function.
       
       Required parameters:
       file_path - the location of the file to load to Shock.
       
       Optional parameters:
       attributes - user-specified attributes to save to the Shock node along
           with the file.
       make_handle - make a Handle Service handle for the shock node. Default
           false.
    */
    typedef structure {
        string file_path;
        mapping<string, UnspecifiedObject> attributes;
        boolean make_handle;
    } FileToShockParams;

    /* Output of the file_to_shock function.
    
        shock_id - the ID of the new Shock node.
        handle_id - the handle ID for the new handle, if created. Null
           otherwise.
    */
    typedef structure {
        string shock_id;
        string handle_id;
    } FileToShockOutput;

    /* Load a file to Shock. */
    funcdef file_to_shock(FileToShockParams params) returns (FileToShockOutput)
        authentication required;
};
