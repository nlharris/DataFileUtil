package us.kbase.datafileutil;

import com.fasterxml.jackson.core.type.TypeReference;
import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import us.kbase.auth.AuthToken;
import us.kbase.common.service.JsonClientCaller;
import us.kbase.common.service.JsonClientException;
import us.kbase.common.service.RpcContext;
import us.kbase.common.service.Tuple11;
import us.kbase.common.service.Tuple2;
import us.kbase.common.service.UnauthorizedException;

/**
 * <p>Original spec-file module name: DataFileUtil</p>
 * <pre>
 * Contains utilities for saving and retrieving data to and from KBase data
 * services. Requires Shock 0.9.6+ and Workspace Service 0.4.1+.
 * </pre>
 */
public class DataFileUtilClient {
    private JsonClientCaller caller;
    private String serviceVersion = null;


    /** Constructs a client with a custom URL and no user credentials.
     * @param url the URL of the service.
     */
    public DataFileUtilClient(URL url) {
        caller = new JsonClientCaller(url);
    }
    /** Constructs a client with a custom URL.
     * @param url the URL of the service.
     * @param token the user's authorization token.
     * @throws UnauthorizedException if the token is not valid.
     * @throws IOException if an IOException occurs when checking the token's
     * validity.
     */
    public DataFileUtilClient(URL url, AuthToken token) throws UnauthorizedException, IOException {
        caller = new JsonClientCaller(url, token);
    }

    /** Constructs a client with a custom URL.
     * @param url the URL of the service.
     * @param user the user name.
     * @param password the password for the user name.
     * @throws UnauthorizedException if the credentials are not valid.
     * @throws IOException if an IOException occurs when checking the user's
     * credentials.
     */
    public DataFileUtilClient(URL url, String user, String password) throws UnauthorizedException, IOException {
        caller = new JsonClientCaller(url, user, password);
    }

    /** Constructs a client with a custom URL
     * and a custom authorization service URL.
     * @param url the URL of the service.
     * @param user the user name.
     * @param password the password for the user name.
     * @param auth the URL of the authorization server.
     * @throws UnauthorizedException if the credentials are not valid.
     * @throws IOException if an IOException occurs when checking the user's
     * credentials.
     */
    public DataFileUtilClient(URL url, String user, String password, URL auth) throws UnauthorizedException, IOException {
        caller = new JsonClientCaller(url, user, password, auth);
    }

    /** Get the token this client uses to communicate with the server.
     * @return the authorization token.
     */
    public AuthToken getToken() {
        return caller.getToken();
    }

    /** Get the URL of the service with which this client communicates.
     * @return the service URL.
     */
    public URL getURL() {
        return caller.getURL();
    }

    /** Set the timeout between establishing a connection to a server and
     * receiving a response. A value of zero or null implies no timeout.
     * @param milliseconds the milliseconds to wait before timing out when
     * attempting to read from a server.
     */
    public void setConnectionReadTimeOut(Integer milliseconds) {
        this.caller.setConnectionReadTimeOut(milliseconds);
    }

    /** Check if this client allows insecure http (vs https) connections.
     * @return true if insecure connections are allowed.
     */
    public boolean isInsecureHttpConnectionAllowed() {
        return caller.isInsecureHttpConnectionAllowed();
    }

    /** Deprecated. Use isInsecureHttpConnectionAllowed().
     * @deprecated
     */
    public boolean isAuthAllowedForHttp() {
        return caller.isAuthAllowedForHttp();
    }

    /** Set whether insecure http (vs https) connections should be allowed by
     * this client.
     * @param allowed true to allow insecure connections. Default false
     */
    public void setIsInsecureHttpConnectionAllowed(boolean allowed) {
        caller.setInsecureHttpConnectionAllowed(allowed);
    }

    /** Deprecated. Use setIsInsecureHttpConnectionAllowed().
     * @deprecated
     */
    public void setAuthAllowedForHttp(boolean isAuthAllowedForHttp) {
        caller.setAuthAllowedForHttp(isAuthAllowedForHttp);
    }

    /** Set whether all SSL certificates, including self-signed certificates,
     * should be trusted.
     * @param trustAll true to trust all certificates. Default false.
     */
    public void setAllSSLCertificatesTrusted(final boolean trustAll) {
        caller.setAllSSLCertificatesTrusted(trustAll);
    }
    
    /** Check if this client trusts all SSL certificates, including
     * self-signed certificates.
     * @return true if all certificates are trusted.
     */
    public boolean isAllSSLCertificatesTrusted() {
        return caller.isAllSSLCertificatesTrusted();
    }
    /** Sets streaming mode on. In this case, the data will be streamed to
     * the server in chunks as it is read from disk rather than buffered in
     * memory. Many servers are not compatible with this feature.
     * @param streamRequest true to set streaming mode on, false otherwise.
     */
    public void setStreamingModeOn(boolean streamRequest) {
        caller.setStreamingModeOn(streamRequest);
    }

    /** Returns true if streaming mode is on.
     * @return true if streaming mode is on.
     */
    public boolean isStreamingModeOn() {
        return caller.isStreamingModeOn();
    }

    public void _setFileForNextRpcResponse(File f) {
        caller.setFileForNextRpcResponse(f);
    }

    public String getServiceVersion() {
        return this.serviceVersion;
    }

    public void setServiceVersion(String newValue) {
        this.serviceVersion = newValue;
    }

    /**
     * <p>Original spec-file function name: shock_to_file</p>
     * <pre>
     * Download a file from Shock.
     * </pre>
     * @param   params   instance of type {@link us.kbase.datafileutil.ShockToFileParams ShockToFileParams}
     * @return   parameter "out" of type {@link us.kbase.datafileutil.ShockToFileOutput ShockToFileOutput}
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public ShockToFileOutput shockToFile(ShockToFileParams params, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(params);
        TypeReference<List<ShockToFileOutput>> retType = new TypeReference<List<ShockToFileOutput>>() {};
        List<ShockToFileOutput> res = caller.jsonrpcCall("DataFileUtil.shock_to_file", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: shock_to_file_mass</p>
     * <pre>
     * Download multiple files from Shock.
     * </pre>
     * @param   params   instance of list of type {@link us.kbase.datafileutil.ShockToFileParams ShockToFileParams}
     * @return   parameter "out" of list of type {@link us.kbase.datafileutil.ShockToFileOutput ShockToFileOutput}
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public List<ShockToFileOutput> shockToFileMass(List<ShockToFileParams> params, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(params);
        TypeReference<List<List<ShockToFileOutput>>> retType = new TypeReference<List<List<ShockToFileOutput>>>() {};
        List<List<ShockToFileOutput>> res = caller.jsonrpcCall("DataFileUtil.shock_to_file_mass", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: file_to_shock</p>
     * <pre>
     * Load a file to Shock.
     * </pre>
     * @param   params   instance of type {@link us.kbase.datafileutil.FileToShockParams FileToShockParams}
     * @return   parameter "out" of type {@link us.kbase.datafileutil.FileToShockOutput FileToShockOutput}
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public FileToShockOutput fileToShock(FileToShockParams params, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(params);
        TypeReference<List<FileToShockOutput>> retType = new TypeReference<List<FileToShockOutput>>() {};
        List<FileToShockOutput> res = caller.jsonrpcCall("DataFileUtil.file_to_shock", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: unpack_file</p>
     * <pre>
     * Using the same logic as unpacking a Shock file, this method will cause
     * any bzip or gzip files to be uncompressed, and then unpack tar and zip
     * archive files (uncompressing gzipped or bzipped archive files if 
     * necessary). If the file is an archive, it will be unbundled into the 
     * directory containing the original output file.
     * </pre>
     * @param   params   instance of type {@link us.kbase.datafileutil.UnpackFileParams UnpackFileParams}
     * @return   parameter "out" of type {@link us.kbase.datafileutil.UnpackFileResult UnpackFileResult}
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public UnpackFileResult unpackFile(UnpackFileParams params, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(params);
        TypeReference<List<UnpackFileResult>> retType = new TypeReference<List<UnpackFileResult>>() {};
        List<UnpackFileResult> res = caller.jsonrpcCall("DataFileUtil.unpack_file", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: pack_file</p>
     * <pre>
     * Pack a file or directory into gzip, targz, or zip archives.
     * </pre>
     * @param   params   instance of type {@link us.kbase.datafileutil.PackFileParams PackFileParams}
     * @return   parameter "out" of type {@link us.kbase.datafileutil.PackFileResult PackFileResult}
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public PackFileResult packFile(PackFileParams params, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(params);
        TypeReference<List<PackFileResult>> retType = new TypeReference<List<PackFileResult>>() {};
        List<PackFileResult> res = caller.jsonrpcCall("DataFileUtil.pack_file", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: package_for_download</p>
     * <pre>
     * </pre>
     * @param   params   instance of type {@link us.kbase.datafileutil.PackageForDownloadParams PackageForDownloadParams}
     * @return   instance of type {@link us.kbase.datafileutil.PackageForDownloadOutput PackageForDownloadOutput}
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public PackageForDownloadOutput packageForDownload(PackageForDownloadParams params, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(params);
        TypeReference<List<PackageForDownloadOutput>> retType = new TypeReference<List<PackageForDownloadOutput>>() {};
        List<PackageForDownloadOutput> res = caller.jsonrpcCall("DataFileUtil.package_for_download", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: file_to_shock_mass</p>
     * <pre>
     * Load multiple files to Shock.
     * </pre>
     * @param   params   instance of list of type {@link us.kbase.datafileutil.FileToShockParams FileToShockParams}
     * @return   parameter "out" of list of type {@link us.kbase.datafileutil.FileToShockOutput FileToShockOutput}
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public List<FileToShockOutput> fileToShockMass(List<FileToShockParams> params, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(params);
        TypeReference<List<List<FileToShockOutput>>> retType = new TypeReference<List<List<FileToShockOutput>>>() {};
        List<List<FileToShockOutput>> res = caller.jsonrpcCall("DataFileUtil.file_to_shock_mass", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: copy_shock_node</p>
     * <pre>
     * Copy a Shock node.
     * </pre>
     * @param   params   instance of type {@link us.kbase.datafileutil.CopyShockNodeParams CopyShockNodeParams}
     * @return   parameter "out" of type {@link us.kbase.datafileutil.CopyShockNodeOutput CopyShockNodeOutput}
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public CopyShockNodeOutput copyShockNode(CopyShockNodeParams params, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(params);
        TypeReference<List<CopyShockNodeOutput>> retType = new TypeReference<List<CopyShockNodeOutput>>() {};
        List<CopyShockNodeOutput> res = caller.jsonrpcCall("DataFileUtil.copy_shock_node", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: own_shock_node</p>
     * <pre>
     * Gain ownership of a Shock node.
     * Returns a shock node id which is owned by the caller, given a shock
     * node id.
     * If the shock node is already owned by the caller, returns the same
     * shock node ID. If not, the ID of a copy of the original node will be
     * returned.
     * If a handle is requested, the node is already owned by the caller, and
     * a handle already exists, that handle will be returned. Otherwise a new
     * handle will be created and returned.
     * </pre>
     * @param   params   instance of type {@link us.kbase.datafileutil.OwnShockNodeParams OwnShockNodeParams}
     * @return   parameter "out" of type {@link us.kbase.datafileutil.OwnShockNodeOutput OwnShockNodeOutput}
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public OwnShockNodeOutput ownShockNode(OwnShockNodeParams params, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(params);
        TypeReference<List<OwnShockNodeOutput>> retType = new TypeReference<List<OwnShockNodeOutput>>() {};
        List<OwnShockNodeOutput> res = caller.jsonrpcCall("DataFileUtil.own_shock_node", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: ws_name_to_id</p>
     * <pre>
     * Translate a workspace name to a workspace ID.
     * </pre>
     * @param   name   instance of String
     * @return   parameter "id" of Long
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public Long wsNameToId(String name, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(name);
        TypeReference<List<Long>> retType = new TypeReference<List<Long>>() {};
        List<Long> res = caller.jsonrpcCall("DataFileUtil.ws_name_to_id", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: save_objects</p>
     * <pre>
     * Save objects to the workspace. Saving over a deleted object undeletes
     * it.
     * </pre>
     * @param   params   instance of type {@link us.kbase.datafileutil.SaveObjectsParams SaveObjectsParams}
     * @return   parameter "info" of list of original type "object_info" (Information about an object, including user provided metadata. objid - the numerical id of the object. name - the name of the object. type - the type of the object. save_date - the save date of the object. ver - the version of the object. saved_by - the user that saved or copied the object. wsid - the id of the workspace containing the object. workspace - the name of the workspace containing the object. chsum - the md5 checksum of the object. size - the size of the object in bytes. meta - arbitrary user-supplied metadata about the object.) &rarr; tuple of size 11: parameter "objid" of Long, parameter "name" of String, parameter "type" of String, parameter "save_date" of String, parameter "version" of Long, parameter "saved_by" of String, parameter "wsid" of Long, parameter "workspace" of String, parameter "chsum" of String, parameter "size" of Long, parameter "meta" of mapping from String to String
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String,String>>> saveObjects(SaveObjectsParams params, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(params);
        TypeReference<List<List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String,String>>>>> retType = new TypeReference<List<List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String,String>>>>>() {};
        List<List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String,String>>>> res = caller.jsonrpcCall("DataFileUtil.save_objects", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: get_objects</p>
     * <pre>
     * Get objects from the workspace.
     * </pre>
     * @param   params   instance of type {@link us.kbase.datafileutil.GetObjectsParams GetObjectsParams}
     * @return   parameter "results" of type {@link us.kbase.datafileutil.GetObjectsResults GetObjectsResults}
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public GetObjectsResults getObjects(GetObjectsParams params, RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        args.add(params);
        TypeReference<List<GetObjectsResults>> retType = new TypeReference<List<GetObjectsResults>>() {};
        List<GetObjectsResults> res = caller.jsonrpcCall("DataFileUtil.get_objects", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }

    /**
     * <p>Original spec-file function name: versions</p>
     * <pre>
     * Get the versions of the Workspace service and Shock service.
     * </pre>
     * @return   multiple set: (1) parameter "wsver" of String, (2) parameter "shockver" of String
     * @throws IOException if an IO exception occurs
     * @throws JsonClientException if a JSON RPC exception occurs
     */
    public Tuple2<String, String> versions(RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        TypeReference<Tuple2<String, String>> retType = new TypeReference<Tuple2<String, String>>() {};
        Tuple2<String, String> res = caller.jsonrpcCall("DataFileUtil.versions", args, retType, true, true, jsonRpcContext, this.serviceVersion);
        return res;
    }

    public Map<String, Object> status(RpcContext... jsonRpcContext) throws IOException, JsonClientException {
        List<Object> args = new ArrayList<Object>();
        TypeReference<List<Map<String, Object>>> retType = new TypeReference<List<Map<String, Object>>>() {};
        List<Map<String, Object>> res = caller.jsonrpcCall("DataFileUtil.status", args, retType, true, false, jsonRpcContext, this.serviceVersion);
        return res.get(0);
    }
}
