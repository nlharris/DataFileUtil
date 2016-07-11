#BEGIN_HEADER
import os
import requests
import json
from biokbase.AbstractHandle.Client import AbstractHandle as HandleService  # @UnresolvedImport @IgnorePep8
from requests_toolbelt.multipart.encoder import MultipartEncoder
import time
import gzip
import shutil
from Workspace.WorkspaceClient import Workspace
import semver


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
    GIT_COMMIT_HASH = "6b228d8073553175ccd2b860d9903be6365d7fe0"
    
    #BEGIN_CLASS_HEADER

    GZIP = '.gz'
    TGZ = '.tgz'

    def log(self, message, prefix_newline=False):
        print(('\n' if prefix_newline else '') +
              str(time.time()) + ': ' + str(message))

    # it'd be nice if you could just open the file and gzip on the fly but I
    # don't see a way to do that
    def gzip(self, oldfile):
        lo = oldfile.lower()
        if lo.endswith(self.GZIP) or lo.endswith(self.TGZ):
            self.log('File {} is already gzipped, skipping'.format(oldfile))
            return oldfile
        newfile = oldfile + self.GZIP
        self.log('gzipping {} to {}'.format(oldfile, newfile))
        with open(oldfile, 'rb') as s, gzip.open(newfile, 'wb') as t:
            shutil.copyfileobj(s, t)
        return newfile

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
           in Shock. Optional parameters: unpack - if the file is compressed
           and / or a file bundle, it will be decompressed and unbundled into
           the directory containing the original output file. unpack supports
           gzip, bzip2, tar, and zip files. Default false. Currently
           unsupported.) -> structure: parameter "shock_id" of String,
           parameter "file_path" of String, parameter "unpack" of type
           "boolean" (A boolean - 0 for false, 1 for true. @range (0, 1))
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
           server type - the type of the handle. This should always be
           ‘shock’. file_name - the name of the file remote_md5 - the md5
           digest of the file.) -> structure: parameter "hid" of String,
           parameter "file_name" of String, parameter "id" of String,
           parameter "url" of String, parameter "type" of String, parameter
           "remote_md5" of String
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
           server type - the type of the handle. This should always be
           ‘shock’. file_name - the name of the file remote_md5 - the md5
           digest of the file.) -> structure: parameter "hid" of String,
           parameter "file_name" of String, parameter "id" of String,
           parameter "url" of String, parameter "type" of String, parameter
           "remote_md5" of String
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
