import unittest
import os.path
import time
import requests

from os import environ
import gzip
try:
    from ConfigParser import ConfigParser  # py2 @UnusedImport
except:
    from configparser import ConfigParser  # py3 @UnresolvedImport @Reimport


from biokbase.workspace.client import Workspace as workspaceService  # @UnresolvedImport @IgnorePep8
from DataFileUtil.DataFileUtilImpl import DataFileUtil, ShockException
from DataFileUtil.DataFileUtilServer import MethodContext
from biokbase.AbstractHandle.Client import AbstractHandle as HandleService  # @UnresolvedImport @IgnorePep8


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
        cls.hs = HandleService(url=cls.cfg['handle-service-url'],
                               token=cls.token)
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

    def test_file_to_shock_and_back_with_attribs(self):
        input_ = "Test!!!"
        tmp_dir = self.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input_)
        ret1 = self.getImpl().file_to_shock(
            self.ctx,
            {'file_path': file_path,
             'attributes': {'foo': [{'bar': 'baz'}]}})[0]
        shock_id = ret1['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.txt')
        ret2 = self.getImpl().shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        file_name = ret2['node_file_name']
        attribs = ret2['attributes']
        self.assertEqual(file_name, input_file_name)
        self.assertEqual(attribs, {'foo': [{'bar': 'baz'}]})
        with open(file_path2, 'r') as fh2:
            output = fh2.read()
        self.assertEqual(output, input_)
        self.delete_shock_node(shock_id)

    def test_file_to_shock_and_back(self):
        input_ = "Test2!!!"
        tmp_dir = self.cfg['scratch']
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
        attribs = ret2['attributes']
        self.assertEqual(file_name, input_file_name)
        self.assertIsNone(attribs)
        with open(file_path2, 'r') as fh2:
            output = fh2.read()
        self.assertEqual(output, input_)
        self.delete_shock_node(shock_id)

    def test_make_handle(self):
        input_ = "Test3!!!"
        tmp_dir = self.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input_)
        ret1 = self.getImpl().file_to_shock(
            self.ctx,
            {'file_path': file_path, 'make_handle': 1})[0]
        shock_id = ret1['shock_id']
        hid = ret1['handle_id']
        handle = self.hs.hids_to_handles([hid])[0]
        self.assertEqual(handle['id'], shock_id)
        self.assertEqual(handle['hid'], hid)
        self.assertEqual(handle['url'], self.shockURL)
        self.assertEqual(handle['type'], 'shock')
        self.delete_shock_node(shock_id)
        self.hs.delete_handles([hid])

    def test_gzip(self):
        input_ = 'testgzip'
        tmp_dir = self.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input_)
        ret1 = self.getImpl().file_to_shock(
            self.ctx,
            {'file_path': file_path, 'gzip': 1})[0]
        shock_id = ret1['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.txt')
        ret2 = self.getImpl().shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        file_name = ret2['node_file_name']
        attribs = ret2['attributes']
        self.assertEqual(file_name, input_file_name + '.gz')
        self.assertIsNone(attribs)
        with gzip.open(file_path2, 'rb') as fh2:
            output = fh2.read()
        self.assertEqual(output, input_)
        self.delete_shock_node(shock_id)

    def test_upload_err_already_gzipped(self):
        self.fail_upload(
            {'file_path': 'input.gz', 'gzip': 1},
            'File input.gz is already gzipped')

    def test_upload_err_no_file_provided(self):
        self.fail_upload(
            {'file_path': ''},
            'No file provided for upload to Shock.')

    def test_download_err_node_not_found(self):
        # test forcing a ShockException on download.
        self.fail_download(
            {'shock_id': '79261fd9-ae10-4a84-853d-1b8fcd57c8f23',
             'file_path': 'foo'
             },
            'Error downloading file from shock node ' +
            '79261fd9-ae10-4a84-853d-1b8fcd57c8f23: Node not found',
            exception=ShockException)

    def test_download_err_node_has_no_file(self):
        # test attempting download on a node without a file.
        res = requests.post(
            self.shockURL + '/node/',
            headers={'Authorization': 'OAuth ' + self.token}).json()
        self.fail_download(
            {'shock_id': res['data']['id'],
             'file_path': 'foo'
             },
            'Node {} has no file'.format(res['data']['id']),
            exception=ShockException)
        self.delete_shock_node(res['data']['id'])

    def test_download_err_no_node_provided(self):
        self.fail_download(
            {'shock_id': '',
             'file_path': 'foo'
             },
            'Must provide shock ID')

    def test_download_err_no_file_provided(self):
        self.fail_download(
            {'shock_id': '79261fd9-ae10-4a84-853d-1b8fcd57c8f2',
             'file_path': ''
             },
            'Must provide file path')

    def test_copy_node(self):
        input_ = 'copytest'
        tmp_dir = self.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input_)
        ret1 = self.getImpl().file_to_shock(
            self.ctx,
            {'file_path': file_path,
             'attributes': {'foopy': [{'bar': 'baz'}]}})[0]
        shock_id = ret1['shock_id']
        retcopy = self.getImpl().copy_shock_node(self.ctx,
                                                 {'shock_id': shock_id})[0]
        new_id = retcopy['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.txt')
        ret2 = self.getImpl().shock_to_file(
            self.ctx,
            {'shock_id': new_id, 'file_path': file_path2})[0]
        file_name = ret2['node_file_name']
        attribs = ret2['attributes']  # @UnusedVariable
        self.assertEqual(file_name, input_file_name)
        # attributes only works in Shock 0.9.13+
        # self.assertEqual(attribs, {'foopy': [{'bar': 'baz'}]})
        with open(file_path2, 'r') as fh2:
            output = fh2.read()
        self.assertEqual(output, input_)
        self.delete_shock_node(shock_id)
        self.delete_shock_node(new_id)

    def test_copy_err_node_not_found(self):
        self.fail_copy(
            {'shock_id': '79261fd9-ae10-4a84-853d-1b8fcd57c8f23'},
            'Error copying Shock node ' +
            '79261fd9-ae10-4a84-853d-1b8fcd57c8f23: ' +
            'err@node_CreateNodeUpload: not found',
            exception=ShockException)

    def test_copy_err_no_node_provided(self):
        self.fail_copy(
            {'shock_id': ''}, 'Must provide shock ID')

    def fail_copy(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.getImpl().copy_shock_node(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def fail_download(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.getImpl().shock_to_file(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def fail_upload(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.getImpl().file_to_shock(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))
