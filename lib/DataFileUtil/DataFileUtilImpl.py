#BEGIN_HEADER
import os
import requests
import json
from biokbase.AbstractHandle.Client import AbstractHandle as HandleService  # @UnresolvedImport @IgnorePep8


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
    GIT_COMMIT_HASH = "a3f5097c150ea522e700f743096520e006cc8cc0"
    
    #BEGIN_CLASS_HEADER
    def log(self, message):
        print(message)

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
        # return variables are: returnVal
        #BEGIN shock_to_file
        token = ctx['token']
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
                             headers=headers)
            self.check_shock_response(r, errtxt)
            for chunk in r.iter_content(1024):
                if not chunk:
                    break
                fhandle.write(chunk)
        returnVal = {'node_file_name': node_file_name,
                     'attributes': attributes}
        self.log('downloading done')
        #END shock_to_file

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method shock_to_file return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]

    def file_to_shock(self, ctx, params):
        """
        Load a file to Shock.
        :param params: instance of type "FileToShockParams" (Input for the
           file_to_shock function. Required parameters: file_path - the
           location of the file to load to Shock. Optional parameters:
           attributes - user-specified attributes to save to the Shock node
           along with the file. make_handle - make a Handle Service handle
           for the shock node. Default false.) -> structure: parameter
           "file_path" of String, parameter "attributes" of mapping from
           String to unspecified object, parameter "make_handle" of type
           "boolean" (A boolean - 0 for false, 1 for true. @range (0, 1))
        :returns: instance of type "FileToShockOutput" (Output of the
           file_to_shock function. shock_id - the ID of the new Shock node.
           handle_id - the handle ID for the new handle, if created. Null
           otherwise.) -> structure: parameter "shock_id" of String,
           parameter "handle_id" of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN file_to_shock
        token = ctx['token']
        if token is None:
            raise Exception("Authentication token required!")
        header = {'Authorization': "Oauth {0}".format(token)}
        if 'file_path' not in params:
            raise Exception("No file given for upload to SHOCK!")
        attribs = params.get('attributes')
        file_path = params['file_path']
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
        returnVal = {'shock_id': shock_id, 'handle_id': None}
        if params.get('make_handle'):
            hs = HandleService(self.handle_url, token=token)
            hid = hs.persist_handle({'id': shock_id,
                                     'type': 'shock',
                                     'url': self.shock_url
                                     })
            returnVal['handle_id'] = hid
        self.log('uploading done into shock node: ' + shock_id)
        #END file_to_shock

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method file_to_shock return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]

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
