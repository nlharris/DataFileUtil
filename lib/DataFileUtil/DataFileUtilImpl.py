#BEGIN_HEADER
import os
import requests
import json
from biokbase.AbstractHandle.Client import AbstractHandle as HandleService  # @UnresolvedImport @IgnorePep8
from biokbase.AbstractHandle.Client import ServerError as HandleError  # @UnresolvedImport @IgnorePep8
from requests_toolbelt.multipart.encoder import MultipartEncoder
import time
import gzip
import shutil
from Workspace.WorkspaceClient import Workspace
from Workspace.baseclient import ServerError as WorkspaceError
import semver
import magic
import tempfile
import bz2  # @UnresolvedImport no idea why PyDev is complaining about this
import tarfile
import zipfile
import errno


class ShockException(Exception):
    pass

#END_HEADER


class DataFileUtil:
    '''
    Module Name:
    DataFileUtil

    Module Description:
    Contains utilities for saving and retrieving data to and from KBase data
services. Requires Shock 0.9.6+ and Workspace Service 0.4.1+.
    '''

    ######## WARNING FOR GEVENT USERS #######
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    #########################################
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/mrcreosote/DataFileUtil"
    GIT_COMMIT_HASH = "c661638cfffd90fe7832c90f51aad8e73dfb510c"
    
    #BEGIN_CLASS_HEADER

    GZ = '.gz'
    GZIP = '.gzip'
    TGZ = '.tgz'

    def log(self, message, prefix_newline=False):
        print(('\n' if prefix_newline else '') +
              str(time.time()) + ': ' + str(message))

    def endswith(self, string, suffixes):
        strl = string.lower()
        for s in suffixes:
            if strl.endswith(s):
                return True
        return False

    # it'd be nice if you could just open the file and gzip on the fly but I
    # don't see a way to do that
    def gzip(self, oldfile):
        if self.endswith(oldfile, [self.GZ, self.GZIP, self.TGZ]):
            self.log('File {} is already gzipped, skipping'.format(oldfile))
            return oldfile
        newfile = oldfile + self.GZ
        self.log('gzipping {} to {}'.format(oldfile, newfile))
        with open(oldfile, 'rb') as s, gzip.open(newfile, 'wb') as t:
            shutil.copyfileobj(s, t)
        return newfile

    def _decompress(self, openfn, file_path, unpack):
        self.log('decompressing...')
        with openfn(file_path, 'rb') as s, tempfile.NamedTemporaryFile() as tf:
            shutil.copyfileobj(s, tf)
            s.close()
            shutil.copy2(tf.name, file_path)
        t = magic.from_file(file_path, mime=True)
        self._unarchive(file_path, unpack, t)

    def _unarchive(self, file_path, unpack, file_type):
        file_dir = os.path.dirname(file_path)
        if file_type in ['application/' + x for x in 'x-tar', 'tar', 'x-gtar']:
            if not unpack:
                raise ValueError(
                    'File is tar file but only uncompress was specified')
            self.log('unpacking...')
            with tarfile.open(file_path) as tf:
                self._check_members(tf.getnames())
                tf.extractall(file_dir)
        if file_type in ['application/' + x for x in
                         'zip', 'x-zip-compressed']:  # , 'x-compressed']:
                        # x-compressed is apparently both .Z and .zip?
            if not unpack:
                raise ValueError(
                    'File is zip file but only uncompress was specified')
            self.log('unpacking...')
            with zipfile.ZipFile(file_path) as zf:
                self._check_members(zf.namelist())
                zf.extractall(file_dir)

    def _check_members(self, member_list):
        # How the hell do I test this? Adding relative paths outside a zip is
        # easy, but the other 3 cases aren't
        for m in member_list:
            n = os.path.normpath(m)
            if n.startswith('/') or n.startswith('..'):
                err = ('Dangerous archive file - entry [{}] points to a ' +
                       'file outside the archive directory').format(m)
                self.log(err)
                raise ValueError(err)

    def _unpack(self, file_path, unpack):
        t = magic.from_file(file_path, mime=True)
        if t in ['application/' + x for x in 'x-gzip', 'gzip']:
            self._decompress(gzip.open, file_path, unpack)
        # probably most of these aren't needed, but hard to find a definite
        # source
        if t in ['application/' + x for x in
                 'x-bzip', 'x-bzip2', 'bzip', 'bzip2']:
            self._decompress(bz2.BZ2File, file_path, unpack)

        self._unarchive(file_path, unpack, t)

    # http://stackoverflow.com/a/600612/643675
    def mkdir_p(self, path):
        if not path:
            return
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def check_shock_response(self, response, errtxt):
        if not response.ok:
            try:
                err = json.loads(response.content)['error'][0]
            except:
                # this means shock is down or not responding.
                self.log("Couldn't parse response error content from Shock: " +
                         response.content)
                response.raise_for_status()
            raise ShockException(errtxt + str(err))

    def make_handle(self, shock_data, token):
        hs = HandleService(self.handle_url, token=token)
        handle = {'id': shock_data['id'],
                  'type': 'shock',
                  'url': self.shock_url,
                  'file_name': shock_data['file']['name'],
                  'remote_md5': shock_data['file']['checksum']['md5']
                  }
        hid = hs.persist_handle(handle)
        handle['hid'] = hid
        return handle

    def make_ref(self, object_info):
        return str(object_info[6]) + '/' + str(object_info[0]) + \
            '/' + str(object_info[4])
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.shock_url = config['shock-url']
        self.handle_url = config['handle-service-url']
        self.ws_url = config['workspace-url']
        #END_CONSTRUCTOR
        pass
    

    def shock_to_file(self, ctx, params):
        """
        Download a file from Shock.
        :param params: instance of type "ShockToFileParams" (Input for the
           shock_to_file function. Required parameters: shock_id - the ID of
           the Shock node. file_path - the location to save the file output.
           If this is a directory, the file will be named as per the filename
           in Shock. Optional parameters: unpack - either null, 'uncompress',
           or 'unpack'. 'uncompress' will cause any bzip or gzip files to be
           uncompressed. 'unpack' will behave the same way, but it will also
           unpack tar and zip archive files (uncompressing gzipped or bzipped
           archive files if necessary). If 'uncompress' is specified and an
           archive file is encountered, an error will be thrown. If the file
           is an archive, it will be unbundled into the directory containing
           the original output file.) -> structure: parameter "shock_id" of
           String, parameter "file_path" of String, parameter "unpack" of
           String
        :returns: instance of type "ShockToFileOutput" (Output from the
           shock_to_file function. node_file_name - the filename of the file
           stored in Shock. attributes - the file attributes, if any, stored
           in Shock.) -> structure: parameter "node_file_name" of String,
           parameter "attributes" of mapping from String to unspecified object
        """
        # ctx is the context object
        # return variables are: out
        #BEGIN shock_to_file
        token = ctx['token']
        if not token:
            raise ValueError('Authentication token required.')
        headers = {'Authorization': 'OAuth ' + token}
        shock_id = params.get('shock_id')
        if not shock_id:
            raise ValueError('Must provide shock ID')
        file_path = params.get('file_path')
        if not file_path:
            raise ValueError('Must provide file path')
        self.mkdir_p(os.path.dirname(file_path))
        node_url = self.shock_url + '/node/' + shock_id
        r = requests.get(node_url, headers=headers, allow_redirects=True)
        errtxt = ('Error downloading file from shock ' +
                  'node {}: ').format(shock_id)
        self.check_shock_response(r, errtxt)
        resp_obj = r.json()
        if not resp_obj['data']['file']['size']:
            raise ShockException('Node {} has no file'.format(shock_id))
        node_file_name = resp_obj['data']['file']['name']
        attributes = resp_obj['data']['attributes']
        if os.path.isdir(file_path):
            file_path = os.path.join(file_path, node_file_name)
        self.log('downloading shock node ' + shock_id + ' into file: ' +
                 str(file_path))
        with open(file_path, 'wb') as fhandle:
            r = requests.get(node_url + '?download_raw', stream=True,
                             headers=headers, allow_redirects=True)
            self.check_shock_response(r, errtxt)
            for chunk in r.iter_content(1024):
                if not chunk:
                    break
                fhandle.write(chunk)
        unpack = params.get('unpack')
        if unpack:
            if unpack not in ['unpack', 'uncompress']:
                raise ValueError('Illegal unpack value: ' + str(unpack))
            self._unpack(file_path, unpack == 'unpack')
        out = {'node_file_name': node_file_name,
               'attributes': attributes}
        self.log('downloading done')
        #END shock_to_file

        # At some point might do deeper type checking...
        if not isinstance(out, dict):
            raise ValueError('Method shock_to_file return value ' +
                             'out is not type dict as required.')
        # return the results
        return [out]

    def shock_to_file_mass(self, ctx, params):
        """
        Download multiple files from Shock.
        :param params: instance of list of type "ShockToFileParams" (Input
           for the shock_to_file function. Required parameters: shock_id -
           the ID of the Shock node. file_path - the location to save the
           file output. If this is a directory, the file will be named as per
           the filename in Shock. Optional parameters: unpack - either null,
           'uncompress', or 'unpack'. 'uncompress' will cause any bzip or
           gzip files to be uncompressed. 'unpack' will behave the same way,
           but it will also unpack tar and zip archive files (uncompressing
           gzipped or bzipped archive files if necessary). If 'uncompress' is
           specified and an archive file is encountered, an error will be
           thrown. If the file is an archive, it will be unbundled into the
           directory containing the original output file.) -> structure:
           parameter "shock_id" of String, parameter "file_path" of String,
           parameter "unpack" of String
        :returns: instance of list of type "ShockToFileOutput" (Output from
           the shock_to_file function. node_file_name - the filename of the
           file stored in Shock. attributes - the file attributes, if any,
           stored in Shock.) -> structure: parameter "node_file_name" of
           String, parameter "attributes" of mapping from String to
           unspecified object
        """
        # ctx is the context object
        # return variables are: out
        #BEGIN shock_to_file_mass
        if type(params) != list:
            raise ValueError('expected list input')
        out = []
        # in the future, could make this rather silly implementation smarter
        # although probably bottlenecked by disk & network so parallelization
        # may not help
        for p in params:
            out.append(self.shock_to_file(ctx, p)[0])
        #END shock_to_file_mass

        # At some point might do deeper type checking...
        if not isinstance(out, list):
            raise ValueError('Method shock_to_file_mass return value ' +
                             'out is not type list as required.')
        # return the results
        return [out]

    def file_to_shock(self, ctx, params):
        """
        Load a file to Shock.
        :param params: instance of type "FileToShockParams" (Input for the
           file_to_shock function. Required parameters: file_path - the
           location of the file to load to Shock. Optional parameters:
           attributes - user-specified attributes to save to the Shock node
           along with the file. make_handle - make a Handle Service handle
           for the shock node. Default false. gzip - gzip the file before
           loading it to Shock. This will create a file_path.gz file prior to
           upload. Default false.) -> structure: parameter "file_path" of
           String, parameter "attributes" of mapping from String to
           unspecified object, parameter "make_handle" of type "boolean" (A
           boolean - 0 for false, 1 for true. @range (0, 1)), parameter
           "gzip" of type "boolean" (A boolean - 0 for false, 1 for true.
           @range (0, 1))
        :returns: instance of type "FileToShockOutput" (Output of the
           file_to_shock function. shock_id - the ID of the new Shock node.
           handle - the new handle, if created. Null otherwise.) ->
           structure: parameter "shock_id" of String, parameter "handle" of
           type "Handle" (A handle for a file stored in Shock. hid - the id
           of the handle in the Handle Service that references this shock
           node id - the id for the shock node url - the url of the shock
           server type - the type of the handle. This should always be shock.
           file_name - the name of the file remote_md5 - the md5 digest of
           the file.) -> structure: parameter "hid" of String, parameter
           "file_name" of String, parameter "id" of String, parameter "url"
           of String, parameter "type" of String, parameter "remote_md5" of
           String
        """
        # ctx is the context object
        # return variables are: out
        #BEGIN file_to_shock
        token = ctx['token']
        if not token:
            raise ValueError('Authentication token required.')
        header = {'Authorization': 'Oauth ' + token}
        file_path = params.get('file_path')
        if not file_path:
            raise ValueError('No file provided for upload to Shock.')
        if params.get('gzip'):
            file_path = self.gzip(file_path)
        attribs = params.get('attributes')
        self.log('uploading file ' + str(file_path) + ' into shock node')
        with open(os.path.abspath(file_path), 'rb') as data_file:
            files = {'upload': data_file}
            if attribs:
                files['attributes'] = ('attributes',
                                       json.dumps(attribs).encode('UTF-8'))
            response = requests.post(
                self.shock_url + '/node', headers=header, files=files,
                stream=True, allow_redirects=True)
        self.check_shock_response(
            response, ('Error trying to upload file {} to Shock: '
                       ).format(file_path))
        shock_data = response.json()['data']
        shock_id = shock_data['id']
        out = {'shock_id': shock_id, 'handle': None}
        if params.get('make_handle'):
            out['handle'] = self.make_handle(shock_data, token)
        self.log('uploading done into shock node: ' + shock_id)
        #END file_to_shock

        # At some point might do deeper type checking...
        if not isinstance(out, dict):
            raise ValueError('Method file_to_shock return value ' +
                             'out is not type dict as required.')
        # return the results
        return [out]

    def file_to_shock_mass(self, ctx, params):
        """
        Load multiple files to Shock.
        :param params: instance of list of type "FileToShockParams" (Input
           for the file_to_shock function. Required parameters: file_path -
           the location of the file to load to Shock. Optional parameters:
           attributes - user-specified attributes to save to the Shock node
           along with the file. make_handle - make a Handle Service handle
           for the shock node. Default false. gzip - gzip the file before
           loading it to Shock. This will create a file_path.gz file prior to
           upload. Default false.) -> structure: parameter "file_path" of
           String, parameter "attributes" of mapping from String to
           unspecified object, parameter "make_handle" of type "boolean" (A
           boolean - 0 for false, 1 for true. @range (0, 1)), parameter
           "gzip" of type "boolean" (A boolean - 0 for false, 1 for true.
           @range (0, 1))
        :returns: instance of list of type "FileToShockOutput" (Output of the
           file_to_shock function. shock_id - the ID of the new Shock node.
           handle - the new handle, if created. Null otherwise.) ->
           structure: parameter "shock_id" of String, parameter "handle" of
           type "Handle" (A handle for a file stored in Shock. hid - the id
           of the handle in the Handle Service that references this shock
           node id - the id for the shock node url - the url of the shock
           server type - the type of the handle. This should always be shock.
           file_name - the name of the file remote_md5 - the md5 digest of
           the file.) -> structure: parameter "hid" of String, parameter
           "file_name" of String, parameter "id" of String, parameter "url"
           of String, parameter "type" of String, parameter "remote_md5" of
           String
        """
        # ctx is the context object
        # return variables are: out
        #BEGIN file_to_shock_mass
        if type(params) != list:
            raise ValueError('expected list input')
        out = []
        # in the future, could make this rather silly implementation smarter
        # although probably bottlenecked by disk & network so parallelization
        # may not help
        for p in params:
            out.append(self.file_to_shock(ctx, p)[0])
        #END file_to_shock_mass

        # At some point might do deeper type checking...
        if not isinstance(out, list):
            raise ValueError('Method file_to_shock_mass return value ' +
                             'out is not type list as required.')
        # return the results
        return [out]

    def copy_shock_node(self, ctx, params):
        """
        Copy a Shock node.
        :param params: instance of type "CopyShockNodeParams" (Input for the
           copy_shock_node function. Required parameters: shock_id - the id
           of the node to copy. Optional parameters: make_handle - make a
           Handle Service handle for the shock node. Default false.) ->
           structure: parameter "shock_id" of String, parameter "make_handle"
           of type "boolean" (A boolean - 0 for false, 1 for true. @range (0,
           1))
        :returns: instance of type "CopyShockNodeOutput" (Output of the
           copy_shock_node function. shock_id - the id of the new Shock node.
           handle - the new handle, if created. Null otherwise.) ->
           structure: parameter "shock_id" of String, parameter "handle" of
           type "Handle" (A handle for a file stored in Shock. hid - the id
           of the handle in the Handle Service that references this shock
           node id - the id for the shock node url - the url of the shock
           server type - the type of the handle. This should always be shock.
           file_name - the name of the file remote_md5 - the md5 digest of
           the file.) -> structure: parameter "hid" of String, parameter
           "file_name" of String, parameter "id" of String, parameter "url"
           of String, parameter "type" of String, parameter "remote_md5" of
           String
        """
        # ctx is the context object
        # return variables are: out
        #BEGIN copy_shock_node
        token = ctx['token']
        if token is None:
            raise ValueError('Authentication token required!')
        header = {'Authorization': 'Oauth {}'.format(token)}
        source_id = params.get('shock_id')
        if not source_id:
            raise ValueError('Must provide shock ID')
        mpdata = MultipartEncoder(fields={'copy_data': source_id})
        header['Content-Type'] = mpdata.content_type
        response = requests.post(
            # copy_attributes only works in 0.9.13+
            self.shock_url + '/node?copy_indexes=1&copy_attributes=1',
            headers=header, data=mpdata, allow_redirects=True)
        self.check_shock_response(
            response, ('Error copying Shock node {}: '
                       ).format(source_id))
        shock_data = response.json()['data']
        shock_id = shock_data['id']
        # remove when min required version is 0.9.13
        if semver.match(self.versions(ctx)[1], '<0.9.13'):
            del header['Content-Type']
            r = requests.get(self.shock_url + '/node/' + source_id,
                             headers=header, allow_redirects=True)
            errtxt = ('Error downloading attributes from shock ' +
                      'node {}: ').format(shock_id)
            self.check_shock_response(r, errtxt)
            attribs = r.json()['data']['attributes']
            if attribs:
                files = {'attributes': ('attributes',
                                        json.dumps(attribs).encode('UTF-8'))}
                response = requests.put(
                    self.shock_url + '/node/' + shock_id, headers=header,
                    files=files, allow_redirects=True)
                self.check_shock_response(
                    response, ('Error setting attributes on Shock node {}: '
                               ).format(shock_id))
        out = {'shock_id': shock_id, 'handle': None}
        if params.get('make_handle'):
            out['handle'] = self.make_handle(shock_data, token)
        #END copy_shock_node

        # At some point might do deeper type checking...
        if not isinstance(out, dict):
            raise ValueError('Method copy_shock_node return value ' +
                             'out is not type dict as required.')
        # return the results
        return [out]

    def own_shock_node(self, ctx, params):
        """
        Gain ownership of a Shock node.
        Returns a shock node id which is owned by the caller, given a shock
        node id.
        If the shock node is already owned by the caller, returns the same
        shock node ID. If not, the ID of a copy of the original node will be
        returned.
        If a handle is requested, the node is already owned by the caller, and
        a handle already exists, that handle will be returned. Otherwise a new
        handle will be created and returned.
        :param params: instance of type "OwnShockNodeParams" (Input for the
           own_shock_node function. Required parameters: shock_id - the id of
           the node for which the user needs ownership. Optional parameters:
           make_handle - make or find a Handle Service handle for the shock
           node. Default false.) -> structure: parameter "shock_id" of
           String, parameter "make_handle" of type "boolean" (A boolean - 0
           for false, 1 for true. @range (0, 1))
        :returns: instance of type "OwnShockNodeOutput" (Output of the
           own_shock_node function. shock_id - the id of the (possibly new)
           Shock node. handle - the handle, if requested. Null otherwise.) ->
           structure: parameter "shock_id" of String, parameter "handle" of
           type "Handle" (A handle for a file stored in Shock. hid - the id
           of the handle in the Handle Service that references this shock
           node id - the id for the shock node url - the url of the shock
           server type - the type of the handle. This should always be shock.
           file_name - the name of the file remote_md5 - the md5 digest of
           the file.) -> structure: parameter "hid" of String, parameter
           "file_name" of String, parameter "id" of String, parameter "url"
           of String, parameter "type" of String, parameter "remote_md5" of
           String
        """
        # ctx is the context object
        # return variables are: out
        #BEGIN own_shock_node
        token = ctx['token']
        if token is None:
            raise ValueError('Authentication token required!')
        header = {'Authorization': 'Oauth {}'.format(token)}
        source_id = params.get('shock_id')
        if not source_id:
            raise ValueError('Must provide shock ID')
        res = requests.get(self.shock_url + '/node/' + source_id +
                           '/acl/owner/?verbosity=full',
                           headers=header, allow_redirects=True)
        self.check_shock_response(
            res, 'Error getting ACLs for Shock node {}: '.format(source_id))
        owner = res.json()['data']['owner']['username']
        if owner != ctx['user_id']:
            out = self.copy_shock_node(ctx, params)[0]
        elif params.get('make_handle'):
            hs = HandleService(self.handle_url, token=token)
            handles = hs.ids_to_handles([source_id])
            if handles:
                h = handles[0]
                del h['created_by']
                del h['creation_date']
                del h['remote_sha1']
                out = {'shock_id': source_id, 'handle': h}
            else:
                # possibility of race condition here, but highly unlikely, so
                # meh
                r = requests.get(self.shock_url + '/node/' + source_id,
                                 headers=header, allow_redirects=True)
                errtxt = ('Error downloading attributes from shock ' +
                          'node {}: ').format(source_id)
                self.check_shock_response(r, errtxt)
                out = {'shock_id': source_id,
                       'handle': self.make_handle(r.json()['data'], token)}
        else:
            out = {'shock_id': source_id}
        #END own_shock_node

        # At some point might do deeper type checking...
        if not isinstance(out, dict):
            raise ValueError('Method own_shock_node return value ' +
                             'out is not type dict as required.')
        # return the results
        return [out]

    def ws_name_to_id(self, ctx, name):
        """
        Translate a workspace name to a workspace ID.
        :param name: instance of String
        :returns: instance of Long
        """
        # ctx is the context object
        # return variables are: id
        #BEGIN ws_name_to_id
        ws = Workspace(self.ws_url, token=ctx['token'])
        id = ws.get_workspace_info(  # @ReservedAssignment
            {'workspace': name})[0]
        #END ws_name_to_id

        # At some point might do deeper type checking...
        if not isinstance(id, int):
            raise ValueError('Method ws_name_to_id return value ' +
                             'id is not type int as required.')
        # return the results
        return [id]

    def save_objects(self, ctx, params):
        """
        Save objects to the workspace. Saving over a deleted object undeletes
        it.
        :param params: instance of type "SaveObjectsParams" (Input parameters
           for the "save_objects" function. Required parameters: id - the
           numerical ID of the workspace. objects - the objects to save. The
           object provenance is automatically pulled from the SDK runner.) ->
           structure: parameter "id" of Long, parameter "objects" of list of
           type "ObjectSaveData" (An object and associated data required for
           saving. Required parameters: type - the workspace type string for
           the object. Omit the version information to use the latest
           version. data - the object data. Optional parameters: One of an
           object name or id. If no name or id is provided the name will be
           set to 'auto' with the object id appended as a string, possibly
           with -\d+ appended if that object id already exists as a name.
           name - the name of the object. objid - the id of the object to
           save over. meta - arbitrary user-supplied metadata for the object,
           not to exceed 16kb; if the object type specifies automatic
           metadata extraction with the 'meta ws' annotation, and your
           metadata name conflicts, then your metadata will be silently
           overwritten. hidden - true if this object should not be listed
           when listing workspace objects.) -> structure: parameter "type" of
           String, parameter "data" of unspecified object, parameter "name"
           of String, parameter "objid" of Long, parameter "meta" of mapping
           from String to String, parameter "hidden" of type "boolean" (A
           boolean - 0 for false, 1 for true. @range (0, 1))
        :returns: instance of list of type "object_info" (Information about
           an object, including user provided metadata. objid - the numerical
           id of the object. name - the name of the object. type - the type
           of the object. save_date - the save date of the object. ver - the
           version of the object. saved_by - the user that saved or copied
           the object. wsid - the id of the workspace containing the object.
           workspace - the name of the workspace containing the object. chsum
           - the md5 checksum of the object. size - the size of the object in
           bytes. meta - arbitrary user-supplied metadata about the object.)
           -> tuple of size 11: parameter "objid" of Long, parameter "name"
           of String, parameter "type" of String, parameter "save_date" of
           String, parameter "version" of Long, parameter "saved_by" of
           String, parameter "wsid" of Long, parameter "workspace" of String,
           parameter "chsum" of String, parameter "size" of Long, parameter
           "meta" of mapping from String to String
        """
        # ctx is the context object
        # return variables are: info
        #BEGIN save_objects
        prov = ctx.provenance()
        objs = params.get('objects')
        if not objs:
            raise ValueError('Required parameter objects missing')
        wsid = params.get('id')
        if not wsid:
            raise ValueError('Required parameter id missing')
        for o in objs:
            o['provenance'] = prov
        ws = Workspace(self.ws_url, token=ctx['token'])
        try:
            info = ws.save_objects({'id': wsid, 'objects': objs})
        except WorkspaceError as e:
            self.log('Logging workspace error on save_objects: {}\n{}'.format(
                e.message, e.data))
            raise
        #END save_objects

        # At some point might do deeper type checking...
        if not isinstance(info, list):
            raise ValueError('Method save_objects return value ' +
                             'info is not type list as required.')
        # return the results
        return [info]

    def get_objects(self, ctx, params):
        """
        Get objects from the workspace.
        :param params: instance of type "GetObjectsParams" (Input parameters
           for the "get_objects" function. Required parameters: object_refs -
           a list of object references in the form X/Y/Z, where X is the
           workspace name or id, Y is the object name or id, and Z is the
           (optional) object version. In general, always use ids rather than
           names if possible to avoid race conditions. Optional parameters:
           ignore_errors - ignore any errors that occur when fetching an
           object and instead insert a null into the returned list.) ->
           structure: parameter "object_refs" of list of String, parameter
           "ignore_errors" of type "boolean" (A boolean - 0 for false, 1 for
           true. @range (0, 1))
        :returns: instance of type "GetObjectsResults" (Results from the
           get_objects function. list<ObjectData> data - the returned
           objects.) -> structure: parameter "data" of list of type
           "ObjectData" (The data and supplemental info for an object.
           UnspecifiedObject data - the object's data or subset data.
           object_info info - information about the object.) -> structure:
           parameter "data" of unspecified object, parameter "info" of type
           "object_info" (Information about an object, including user
           provided metadata. objid - the numerical id of the object. name -
           the name of the object. type - the type of the object. save_date -
           the save date of the object. ver - the version of the object.
           saved_by - the user that saved or copied the object. wsid - the id
           of the workspace containing the object. workspace - the name of
           the workspace containing the object. chsum - the md5 checksum of
           the object. size - the size of the object in bytes. meta -
           arbitrary user-supplied metadata about the object.) -> tuple of
           size 11: parameter "objid" of Long, parameter "name" of String,
           parameter "type" of String, parameter "save_date" of String,
           parameter "version" of Long, parameter "saved_by" of String,
           parameter "wsid" of Long, parameter "workspace" of String,
           parameter "chsum" of String, parameter "size" of Long, parameter
           "meta" of mapping from String to String
        """
        # ctx is the context object
        # return variables are: results
        #BEGIN get_objects
        ignore_err = params.get('ignore_errors')
        objlist = params.get('object_refs')
        if not objlist:
            raise ValueError('No objects specified for retrieval')
        input_ = {'objects': [{'ref': x} for x in objlist]}
        if ignore_err:
            input_['ignoreErrors'] = 1
        ws = Workspace(self.ws_url, token=ctx['token'])
        try:
            retobjs = ws.get_objects2(input_)['data']
        except WorkspaceError as e:
            self.log('Logging workspace error on get_objects: {}\n{}'.format(
                e.message, e.data))
            raise
        results = []
        for o in retobjs:
            if not o:
                results.append(None)
                continue
            res = {'data': o['data'], 'info': o['info']}
            he = 'handle_error'
            hs = 'handle_stacktrace'
            if he in o or hs in o:
                ref = self.make_ref(o['info'])
                self.log('Handle error for object {}: {}.\nStacktrace: {}'
                         .format(ref, o.get(he), o.get(hs)))
                if ignore_err:
                    res = None
                else:
                    raise HandleError(
                        'HandleError', 0, 'Handle error for object {}: {}'
                        .format(ref, o.get(he)), o.get(hs))
            results.append(res)
        results = {'data': results}
        #END get_objects

        # At some point might do deeper type checking...
        if not isinstance(results, dict):
            raise ValueError('Method get_objects return value ' +
                             'results is not type dict as required.')
        # return the results
        return [results]

    def versions(self, ctx):
        """
        Get the versions of the Workspace service and Shock service.
        :returns: multiple set - (1) parameter "wsver" of String, (2)
           parameter "shockver" of String
        """
        # ctx is the context object
        # return variables are: wsver, shockver
        #BEGIN versions
        del ctx
        wsver = Workspace(self.ws_url).ver()
        resp = requests.get(self.shock_url, allow_redirects=True)
        self.check_shock_response(resp, 'Error contacting Shock: ')
        shockver = resp.json()['version']
        #END versions

        # At some point might do deeper type checking...
        if not isinstance(wsver, basestring):
            raise ValueError('Method versions return value ' +
                             'wsver is not type basestring as required.')
        if not isinstance(shockver, basestring):
            raise ValueError('Method versions return value ' +
                             'shockver is not type basestring as required.')
        # return the results
        return [wsver, shockver]

    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': 'OK',
                     'message': '',
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH
                     }
        del ctx
        #END_STATUS
        return [returnVal]
