import unittest
import os
import os.path
import json
import time

from os import environ
try:
    from ConfigParser import ConfigParser  # py2
except:
    from configparser import ConfigParser  # py3

from pprint import pprint

from biokbase.workspace.client import Workspace as workspaceService
from DataFileUtil.DataFileUtilImpl import DataFileUtil
from DataFileUtil.DataFileUtilServer import MethodContext


class DataFileUtilTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = environ.get('KB_AUTH_TOKEN', None)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
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
        cls.wsClient = workspaceService(cls.wsURL, token=token)
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
        ret = self.getWsClient().create_workspace({'workspace': wsName})
        self.__class__.wsName = wsName
        return wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    def test_file_to_shock_and_back(self):
        input = "Test!!!"
        tmp_dir = self.__class__.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input)
        ret1 = self.getImpl().file_to_shock(self.getContext(),
            {'file_path': file_path})[0]
        shock_id = ret1['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.txt')
        ret2 = self.getImpl().shock_to_file(self.getContext(),
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        file_name = ret2['node_file_name']
        self.assertEqual(file_name, input_file_name)
        output = None
        with open(file_path2, 'r') as fh2:
            output = fh2.read();
        self.assertEqual(output, input)
