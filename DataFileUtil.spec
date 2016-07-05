/*
A KBase module: DataFileUtil
*/

module DataFileUtil {
    typedef structure {
        string shock_id;
        string file_path;
    } ShockToFileParams;

    typedef structure {
        string node_file_name;
        mapping<string, string> attributes;
    } ShockToFileOutput;

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
