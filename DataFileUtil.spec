/*
Contains utilities for retrieving and saving data from and to KBase data
services.
*/

module DataFileUtil {

    /* Input for the shock_to_file function.
       
       Required parameters:
       shock_id - the ID of the Shock node.
       file_path - the location to save the file output. If this is a
           directory, the file will be named as per the filename in Shock.
    */
    typedef structure {
        string shock_id;
        string file_path;
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


    typedef structure {
        string file_path;
        mapping<string, string> attributes;
    } FileToShockParams;

    typedef structure {
        string shock_id;
    } FileToShockOutput;

    funcdef file_to_shock(FileToShockParams params) returns (FileToShockOutput)
        authentication required;
};
