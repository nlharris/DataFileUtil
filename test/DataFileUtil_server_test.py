import unittest
import os.path
import time
import requests

from os import environ
try:
    from ConfigParser import ConfigParser  # py2 @UnusedImport
except:
    from configparser import ConfigParser  # py3 @UnresolvedImport @Reimport


from biokbase.workspace.client import Workspace as workspaceService  # @UnresolvedImport @IgnorePep8
from DataFileUtil.DataFileUtilImpl import DataFileUtil, ShockException
from DataFileUtil.DataFileUtilServer import MethodContext


class DataFileUtilTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.token = environ.get('KB_AUTH_TOKEN', None)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': cls.token,
                        'provenance': [
                            {'service': 'DataFileUtil',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('DataFileUtil'):
            cls.cfg[nameval[0]] = nameval[1]
        cls.wsURL = cls.cfg['workspace-url']
        cls.shockURL = cls.cfg['shock-url']
        cls.wsClient = workspaceService(cls.wsURL, token=cls.token)
        cls.serviceImpl = DataFileUtil(cls.cfg)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        if hasattr(self.__class__, 'wsName'):
            return self.__class__.wsName
        suffix = int(time.time() * 1000)
        wsName = "test_DataFileUtil_" + str(suffix)
        self.getWsClient().create_workspace({'workspace': wsName})
        self.__class__.wsName = wsName
        return wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    @classmethod
    def delete_shock_node(cls, node_id):
        header = {'Authorization': 'Oauth {0}'.format(cls.token)}
        requests.delete(cls.shockURL + '/node/' + node_id, headers=header,
                        allow_redirects=True)
        print('Deleted shock node ' + node_id)

    def test_file_to_shock_and_back(self):
        input_ = "Test!!!"
        tmp_dir = self.__class__.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input_)
        ret1 = self.getImpl().file_to_shock(
            self.ctx,
            {'file_path': file_path})[0]
        shock_id = ret1['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.txt')
        ret2 = self.getImpl().shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        file_name = ret2['node_file_name']
        self.assertEqual(file_name, input_file_name)
        with open(file_path2, 'r') as fh2:
            output = fh2.read()
        self.assertEqual(output, input_)
        self.delete_shock_node(shock_id)

    def test_download_err(self):
        # test forcing a ShockException on download.
        try:
            self.getImpl().shock_to_file(
                self.ctx,
                {'shock_id': '79261fd9-ae10-4a84-853d-1b8fcd57c8f23',
                 'file_path': 'foo'
                 })
        except ShockException as se:
            self.assertEqual(
                se.message, 'Error downloading file from shock node ' +
                '79261fd9-ae10-4a84-853d-1b8fcd57c8f23: Node not found')
