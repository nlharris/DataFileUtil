#BEGIN_HEADER
import os
import requests
import json
from biokbase.AbstractHandle.Client import AbstractHandle as HandleService  # @UnresolvedImport @IgnorePep8
from requests_toolbelt.multipart.encoder import MultipartEncoder
import time
import gzip
import shutil


class ShockException(Exception):
    pass

#END_HEADER


class DataFileUtil:
    '''
    Module Name:
    DataFileUtil

    Module Description:
    Contains utilities for retrieving and saving data from and to KBase data
services.
    '''

    ######## WARNING FOR GEVENT USERS #######
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    #########################################
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/mrcreosote/DataFileUtil"
    GIT_COMMIT_HASH = "f2f142cc8c94e25fa46249a45ae22f57b4b0b11e"
    
    #BEGIN_CLASS_HEADER

    GZIP = '.gz'

    def log(self, message, prefix_newline=False):
        print(('\n' if prefix_newline else '') +
              str(time.time()) + ': ' + str(message))

    # it'd be nice if you could just open the file and gzip on the fly but I
    # don't see a way to do that
    def gzip(self, oldfile):
        if oldfile.lower().endswith(self.GZIP):
            raise ValueError('File {} is already gzipped'.format(oldfile))
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
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.shock_url = config['shock-url']
        self.handle_url = config['handle-service-url']
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
        r = requests.get(node_url, headers=headers)
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
        with open(file_path, 'w') as fhandle:
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
           handle_id - the handle ID for the new handle, if created. Null
           otherwise.) -> structure: parameter "shock_id" of String,
           parameter "handle_id" of String
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
        shock_id = response.json()['data']['id']
        out = {'shock_id': shock_id, 'handle_id': None}
        if params.get('make_handle'):
            hs = HandleService(self.handle_url, token=token)
            hid = hs.persist_handle({'id': shock_id,
                                     'type': 'shock',
                                     'url': self.shock_url
                                     })
            out['handle_id'] = hid
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
        Copy a Shock node. Note that attributes are only copied in Shock
        version 0.9.13+.
        :param params: instance of type "CopyShockNodeParams" (Input for the
           copy_shock_node function. shock_id - the id of the node to copy.)
           -> structure: parameter "shock_id" of String
        :returns: instance of type "CopyShockNodeOutput" (Output of the
           copy_shock_node function. shock_id - the id of the new Shock
           node.) -> structure: parameter "shock_id" of String
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
        shock_id = response.json()['data']['id']
        out = {'shock_id': shock_id}
        #END copy_shock_node

        # At some point might do deeper type checking...
        if not isinstance(out, dict):
            raise ValueError('Method copy_shock_node return value ' +
                             'out is not type dict as required.')
        # return the results
        return [out]

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
