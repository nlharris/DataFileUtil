#BEGIN_HEADER
import os
import requests
import json


class ShockException(Exception):
    pass

#END_HEADER


class DataFileUtil:
    '''
    Module Name:
    DataFileUtil

    Module Description:
    A KBase module: DataFileUtil
    '''

    ######## WARNING FOR GEVENT USERS #######
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    #########################################
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""
    
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
        #END_CONSTRUCTOR
        pass
    

    def shock_to_file(self, ctx, params):
        """
        :param params: instance of type "ShockToFileParams" -> structure:
           parameter "shock_id" of String, parameter "file_path" of String
        :returns: instance of type "ShockToFileOutput" -> structure:
           parameter "node_file_name" of String, parameter "attributes" of
           mapping from String to String
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
        node_file_name = resp_obj['data']['file']['name']
        attributes = None
        if 'attributes' in resp_obj:
            attributes = resp_obj['attributes']
        if os.path.isdir(file_path):
            file_path = os.path.join(file_path, node_file_name)
        self.log('downloading shock node ' + shock_id + ' into file: ' +
                 str(file_path))
        with open(file_path, 'w') as fhandle:
            r = requests.get(node_url + '?download', stream=True,
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
        :param params: instance of type "FileToShockParams" -> structure:
           parameter "file_path" of String, parameter "attributes" of mapping
           from String to String
        :returns: instance of type "FileToShockOutput" -> structure:
           parameter "shock_id" of String
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
        file_path = params['file_path']
        self.log('uploading file ' + str(file_path) + ' into shock node')
        if 'attributes' in params:
            raise Exception("attributes argument is not supported yet")
        with open(os.path.abspath(file_path), 'rb') as data_file:
            files = {'upload': data_file}
            response = requests.post(
                self.shock_url + '/node', headers=header, files=files,
                stream=True, allow_redirects=True)
        self.check_shock_response(
            response, ('Error trying to upload contig FASTA file {} to Shock: '
                       ).format(file_path))
        shock_id = response.json()['data']['id']
        returnVal = {'shock_id': shock_id}
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
