import unittest
import os.path
import time
import requests

from os import environ
import gzip
import semver
import tempfile
import shutil
import filecmp
import tarfile
import zipfile
from mock import patch 
import ftplib
try:
    from ConfigParser import ConfigParser  # py2 @UnusedImport
except:
    from configparser import ConfigParser  # py3 @UnresolvedImport @Reimport

from Workspace.WorkspaceClient import Workspace
from DataFileUtil.DataFileUtilImpl import DataFileUtil, ShockException
from DataFileUtil.DataFileUtilServer import MethodContext
from biokbase.AbstractHandle.Client import AbstractHandle as HandleService  # @UnresolvedImport @IgnorePep8
from Workspace.baseclient import ServerError as WorkspaceError
from DataFileUtil.DataFileUtilImpl import HandleError
from DataFileUtil.authclient import KBaseAuth as _KBaseAuth


class DataFileUtilTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.token = environ.get('KB_AUTH_TOKEN', None)
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('DataFileUtil'):
            cls.cfg[nameval[0]] = nameval[1]
        authServiceUrl = cls.cfg.get('auth-service-url',
                "https://kbase.us/services/authorization/Sessions/Login")
        auth_client = _KBaseAuth(authServiceUrl)
        cls.user_id = auth_client.get_user(cls.token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': cls.token,
                        'user_id': cls.user_id,
                        'provenance': [
                            {'service': 'DataFileUtilFakeProv',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})

        
        
        cls.shockURL = cls.cfg['shock-url']
        cls.ws = Workspace(cls.cfg['workspace-url'], token=cls.token)
        cls.hs = HandleService(url=cls.cfg['handle-service-url'],
                               token=cls.token)
        shutil.rmtree(cls.cfg['scratch'])
        os.mkdir(cls.cfg['scratch'])
        cls.impl = DataFileUtil(cls.cfg)
        suffix = int(time.time() * 1000)
        wsName = "test_DataFileUtil_" + str(suffix)
        cls.ws_info = cls.ws.create_workspace({'workspace': wsName})

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'ws_info'):
            cls.ws.delete_workspace({'id': cls.ws_info[0]})
            print('Test workspace was deleted')

    @classmethod
    def delete_shock_node(cls, node_id):
        header = {'Authorization': 'Oauth {0}'.format(cls.token)}
        requests.delete(cls.shockURL + '/node/' + node_id, headers=header,
                        allow_redirects=True)
        print('Deleted shock node ' + node_id)

    def test_file_to_shock_and_back_by_handle(self):
        input_ = "Test!!!"
        tmp_dir = self.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input_)
        ret1 = self.impl.file_to_shock(
                    self.ctx,
                    {'file_path': file_path,
                     'make_handle': 1})[0]
        shock_id = ret1['shock_id']
        handle_id = ret1['handle']['hid']
        file_path2 = os.path.join(tmp_dir, 'output.txt')
        self.impl.shock_to_file(
            self.ctx,
            {'handle_id': handle_id, 'file_path': file_path2})[0]
        with open(file_path2, 'r') as fh2:
            output = fh2.read()
        self.assertEqual(output, input_)
        self.delete_shock_node(shock_id)

    def test_file_to_shock_and_back_with_attribs(self):
        input_ = "Test!!!"
        tmp_dir = self.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input_)
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': file_path,
             'attributes': {'foo': [{'bar': 'baz'}]}})[0]
        shock_id = ret1['shock_id']
        self.assertEqual(ret1['node_file_name'], 'input.txt')
        self.assertEqual(ret1['size'], 7)
        file_path2 = os.path.join(tmp_dir, 'output.txt')
        ret2 = self.impl.shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        file_name = ret2['node_file_name']
        attribs = ret2['attributes']
        self.assertEqual(file_name, input_file_name)
        self.assertEqual(ret2['file_path'], file_path2)
        self.assertEqual(attribs, {'foo': [{'bar': 'baz'}]})
        self.assertEqual(ret2['size'], 7)
        with open(file_path2, 'r') as fh2:
            output = fh2.read()
        self.assertEqual(output, input_)
        self.delete_shock_node(shock_id)

    def test_file_to_shock_and_back(self):
        file_path = self.write_file('input.txt', 'Test2!!!')
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': file_path})[0]
        shock_id = ret1['shock_id']
        self.assertEqual(ret1['node_file_name'], 'input.txt')
        self.assertEqual(ret1['size'], 8)
        # test creating a directory on download
        file_path2 = os.path.join(self.cfg['scratch'], 'tftsab/output.txt')
        ret2 = self.impl.shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        file_name = ret2['node_file_name']
        attribs = ret2['attributes']
        self.assertEqual(file_name, 'input.txt')
        self.assertEqual(ret2['file_path'], file_path2)
        self.assertEqual(ret2['size'], 8)
        self.assertIsNone(attribs)
        with open(file_path2, 'r') as fh2:
            output = fh2.read()
        self.assertEqual(output, 'Test2!!!')
        self.delete_shock_node(shock_id)

    def test_file_to_shock_mass_and_back(self):
        infile1 = self.write_file('input1.txt', 'filestoshock1')
        infile2 = self.write_file('input2.txt', 'filestoshock2')
        ret1 = self.impl.file_to_shock_mass(
            self.ctx,
            [{'file_path': infile1},
             {'file_path': infile2}
             ]
        )[0]
        shock_id1 = ret1[0]['shock_id']
        shock_id2 = ret1[1]['shock_id']
        self.assertEqual(ret1[0]['node_file_name'], 'input1.txt')
        self.assertEqual(ret1[0]['size'], 13)
        self.assertEqual(ret1[1]['node_file_name'], 'input2.txt')
        self.assertEqual(ret1[1]['size'], 13)
        outfile1 = os.path.join(self.cfg['scratch'], 'output1.txt')
        outfile2 = os.path.join(self.cfg['scratch'], 'output2.txt')
        ret2 = self.impl.shock_to_file_mass(
            self.ctx,
            [{'shock_id': shock_id1, 'file_path': outfile1},
             {'shock_id': shock_id2, 'file_path': outfile2}
             ]
        )[0]

        self.delete_shock_node(shock_id1)
        self.delete_shock_node(shock_id2)

        file_name1 = ret2[0]['node_file_name']
        attribs1 = ret2[0]['attributes']
        file_path1 = ret2[0]['file_path']
        self.assertEqual(file_name1, 'input1.txt')
        self.assertEqual(file_path1, outfile1)
        self.assertEqual(ret2[0]['size'], 13)
        self.assertIsNone(attribs1)
        with open(outfile1, 'r') as fh:
            output = fh.read()
        self.assertEqual(output, 'filestoshock1')

        file_name2 = ret2[1]['node_file_name']
        attribs2 = ret2[1]['attributes']
        file_path2 = ret2[1]['file_path']
        self.assertEqual(file_name2, 'input2.txt')
        self.assertEqual(ret2[1]['size'], 13)
        self.assertEqual(file_path2, outfile2)
        self.assertIsNone(attribs2)
        with open(outfile2, 'r') as fh:
            output = fh.read()
        self.assertEqual(output, 'filestoshock2')

    def test_unpack(self):
        tmp_dir = self.cfg['scratch']
        test_file = 'file1.txt.bz'
        unpack_dir = os.path.join(tmp_dir, 'test_unpack')
        test_file_path = os.path.join(unpack_dir, test_file)
        os.mkdir(unpack_dir)
        shutil.copy('data/'+test_file, test_file_path)

        # the low level unpack method is well tested by other methods-
        # here we just want to be sure the impl.unpack_file is behaving
        # as expected
        ret1 = self.impl.unpack_file(
                self.ctx,
                {'file_path': test_file_path}
            )[0]
        self.assertEqual(ret1['file_path'],
                         str(os.path.join(unpack_dir, 'file1.txt')))

    def test_unpack_large_zip(self):
        txt_filename = 'large_file.txt'
        zip_filename = 'large_file.txt.zip'
        tmp_dir = os.path.join(self.cfg['scratch'], 'unpacklargeziptest')
        if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
        zip_file_path = os.path.join(tmp_dir, zip_filename)
        txt_file_path = os.path.join(tmp_dir, txt_filename)

        size_3GB = 3 * 1024 * 1024 * 1024

        with open(txt_file_path, "wb") as output:
            output.seek(size_3GB)
            output.write('0')

        print ('--- generating a 3GB zipfile ---\n' +
            '--- to speed up your local test, ' +
            'please comment out test_unpack_large_zip ---')

        compress_size = 0
        count = 0
        while compress_size < size_3GB:
            with zipfile.ZipFile(zip_file_path, 'a', zipfile.ZIP_STORED,
                    allowZip64=True) as output:
                output.write(txt_file_path, str(count) + '.zip')
            count += 1
            compress_size = os.stat(zip_file_path).st_size

        ret1 = self.impl.unpack_file(
                self.ctx,
                {'file_path': zip_file_path}
            )[0]
        self.assertEqual(ret1['file_path'],
                         str(os.path.join(tmp_dir, zip_file_path)))

        self.assertIn('0.zip', os.listdir(tmp_dir))

        os.remove(zip_file_path)
        os.remove(txt_file_path)

    def write_file(self, filename, content):
        tmp_dir = self.cfg['scratch']
        file_path = os.path.join(tmp_dir, filename)
        with open(file_path, 'w') as fh1:
            fh1.write(content)
        return file_path

    def test_upload_make_handle(self):
        input_ = "Test3!!!"
        tmp_dir = self.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input_)
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': file_path, 'make_handle': 1})[0]
        self.assertEqual(ret1['node_file_name'], 'input.txt')
        self.assertEqual(ret1['size'], 8)
        shock_id = ret1['shock_id']
        self.delete_shock_node(shock_id)
        rethandle = ret1['handle']
        hid = rethandle['hid']
        handle = self.hs.hids_to_handles([hid])[0]
        self.hs.delete_handles([hid])
        self.check_handle(rethandle, hid, shock_id,
                          '88d0594a4ee2b25527540fe76233a405', 'input.txt')
        self.check_handle(handle, hid, shock_id,
                          '88d0594a4ee2b25527540fe76233a405', 'input.txt')

    def check_handle(self, handle, hid, shock_id, md5, filename):
        self.assertEqual(handle['id'], shock_id)
        self.assertEqual(handle['hid'], hid)
        self.assertEqual(handle['url'], self.shockURL)
        self.assertEqual(handle['type'], 'shock')
        self.assertEqual(handle['remote_md5'], md5)
        self.assertEqual(handle['file_name'], filename)

    def test_gzip(self):
        input_ = 'testgzip'
        tmp_dir = self.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input_)
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': file_path, 'pack': 'gzip'})[0]
        self.assertEqual(ret1['node_file_name'], 'input.txt.gz')
        self.assertEqual(ret1['size'], 38)
        shock_id = ret1['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.txt')
        ret2 = self.impl.shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        self.delete_shock_node(shock_id)
        file_name = ret2['node_file_name']
        attribs = ret2['attributes']
        self.assertEqual(file_name, input_file_name + '.gz')
        self.assertIsNone(attribs)
        with gzip.open(file_path2, 'rb') as fh2:
            output = fh2.read()
        self.assertEqual(output, input_)

    def test_upload_zip(self):
        tmp_dir = os.path.join(self.cfg['scratch'], 'ziptest')
        os.makedirs(tmp_dir)
        self.write_file(os.path.join(tmp_dir, 'inzip1.txt'), 'zip1')
        self.write_file(os.path.join(tmp_dir, 'inzip2.txt'), 'zip2')
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': tmp_dir + '/target',
             'pack': 'zip'})[0]
        self.assertEqual(ret1['node_file_name'], 'target.zip')
        self.assertTrue(ret1['size'] > 215 and ret1['size'] < 235)
        shock_id = ret1['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.zip')
        ret2 = self.impl.shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        self.delete_shock_node(shock_id)
        self.assertEqual(ret2['node_file_name'], 'target.zip')
        self.assertIsNone(ret2['attributes'])
        self.assertEqual(ret2['file_path'], file_path2)
        self.assertTrue(ret2['size'] > 215 and ret2['size'] < 235)
        with zipfile.ZipFile(file_path2) as z:
            self.assertEqual(set(z.namelist()),
                             set(['inzip1.txt', 'inzip2.txt']))

    def test_upload_tgz_with_no_dir(self):
        tmp_dir = os.path.join(self.cfg['scratch'], 'tartest')
        os.makedirs(tmp_dir)
        self.write_file(os.path.join(tmp_dir, 'intar1.txt'), 'tar1')
        self.write_file(os.path.join(tmp_dir, 'intar2.txt'), 'tar2')
        wd = os.getcwd()
        os.chdir(tmp_dir)
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': 'target',
             'pack': 'targz'})[0]
        os.chdir(wd)
        self.assertEqual(ret1['node_file_name'], 'target.tar.gz')
        self.assertGreater(ret1['size'], 220)
        self.assertLess(ret1['size'], 240)
        shock_id = ret1['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.tgz')
        ret2 = self.impl.shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        self.delete_shock_node(shock_id)
        self.assertEqual(ret2['node_file_name'], 'target.tar.gz')
        self.assertIsNone(ret2['attributes'])
        self.assertEqual(ret2['file_path'], file_path2)
        self.assertGreater(ret2['size'], 220)
        self.assertLess(ret2['size'], 240)
        with tarfile.open(file_path2) as t:
            self.assertEqual(set(t.getnames()),
                             set(['.', './intar1.txt', './intar2.txt']))

    def test_package_for_download(self):
        obj_name = 'TestForWsRef'
        ws = self.ws_info[0]
        self.impl.save_objects(
            self.ctx, {'id': ws, 'objects':
                       [{'name': obj_name, 'type': 'Empty.AType-0.1',
                         'data': {'thingy': 1}}]})
        tmp_dir = self.cfg['scratch'] + '/ws_refs_test'
        os.makedirs(tmp_dir)
        self.write_file('ws_refs_test/inzip1.txt', 'zip1')
        shock_id = self.impl.package_for_download(
            self.ctx,
            {'file_path': tmp_dir,
             'ws_refs': [str(ws) + '/' + obj_name]})[0]['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.zip')
        self.impl.shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        self.delete_shock_node(shock_id)
        txt_found = False
        json_found = False
        with zipfile.ZipFile(file_path2) as z:
            for entry in set(z.namelist()):
                if 'inzip1.txt' in entry:
                    txt_found = True
                elif 'TestForWsRef_v1.json' in entry:
                    json_found = True
        self.assertTrue(txt_found)
        self.assertTrue(json_found)

    def test_upload_tgz_with_no_file_name(self):
        tmp_dir = os.path.join(self.cfg['scratch'], 'tartest2')
        os.makedirs(tmp_dir)
        self.write_file(os.path.join(tmp_dir, 'intar1.txt'), 'tar1')
        self.write_file(os.path.join(tmp_dir, 'intar2.txt'), 'tar2')
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': tmp_dir,
             'pack': 'targz'})[0]
        self.assertEqual(ret1['node_file_name'], 'tartest2.tar.gz')
        self.assertGreater(ret1['size'], 220)
        self.assertLess(ret1['size'], 240)
        shock_id = ret1['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.tgz')
        ret2 = self.impl.shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        self.delete_shock_node(shock_id)
        self.assertEqual(ret2['node_file_name'], 'tartest2.tar.gz')
        self.assertIsNone(ret2['attributes'])
        self.assertEqual(ret2['file_path'], file_path2)
        self.assertGreater(ret1['size'], 220)
        self.assertLess(ret1['size'], 240)
        with tarfile.open(file_path2) as t:
            self.assertEqual(set(t.getnames()),
                             set(['.', './intar1.txt', './intar2.txt']))

    def test_gzip_already_gzipped(self):
        print('*** test_gzip_already_gzipped ***')
        self.check_gzip_skip('input.txt.gz', 'gz test')
        self.check_gzip_skip('input.txt.tgz', 'tgz test')
        self.check_gzip_skip('input.txt.gzip', 'gzip test')

    def check_gzip_skip(self, input_file_name, contents):
        file_path = self.write_file(input_file_name, contents)
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': file_path, 'pack': 'gzip'})[0]
        shock_id = ret1['shock_id']
        self.assertEqual(ret1['node_file_name'], input_file_name)
        file_path2 = os.path.join(self.cfg['scratch'], 'output.txt')
        ret2 = self.impl.shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        file_name = ret2['node_file_name']
        attribs = ret2['attributes']
        self.assertEqual(file_name, input_file_name)
        self.assertIsNone(attribs)
        with open(file_path2, 'r') as fh2:
            output = fh2.read()
        self.assertEqual(output, contents)
        self.delete_shock_node(shock_id)

        # test with pack function
        new_file_path = self.impl.pack_file(
            self.ctx, {'file_path': file_path, 'pack': 'gzip'})[0]['file_path']
        self.assertEqual(new_file_path, file_path)
        with open(file_path2, 'r') as fh2:
            output = fh2.read()
        self.assertEqual(output, contents)

    def test_unpack_archive(self):
        self.check_unpack_archive('data/tar1.tar', 10240)
        self.check_unpack_archive('data/tar1.tar.txt', 10240)
        self.check_unpack_archive('data/tar1.tgz.txt', 180)
        self.check_unpack_archive('data/tar1.tgz', 180, 'tar1.tar')
        self.check_unpack_archive('data/tar1.tar.gz', 189, 'tar1.tar')
        self.check_unpack_archive('data/tar1.tar.gzip', 189, 'tar1.tar')
        self.check_unpack_archive('data/tar1.tbz', 194, 'tar1.tar')
        self.check_unpack_archive('data/tar1.tar.bz', 194, 'tar1.tar')
        self.check_unpack_archive('data/tar1.tar.bz2', 194, 'tar1.tar')
        self.check_unpack_archive('data/tar1.tar.bzip', 194, 'tar1.tar')
        self.check_unpack_archive('data/tar1.tar.bzip2', 194, 'tar1.tar')
        self.check_unpack_archive('data/zip1.zip', 484)

    def check_unpack_archive(self, file_path, size, file_name=None):
        ret1 = self.impl.file_to_shock(self.ctx, {'file_path': file_path})[0]
        sid = ret1['shock_id']
        td = os.path.abspath(tempfile.mkdtemp(dir=self.cfg['scratch']))
        ret2 = self.impl.shock_to_file(self.ctx, {'shock_id': sid,
                                                  'file_path': td,
                                                  'unpack': 'unpack'
                                                  }
                                       )[0]
        self.delete_shock_node(sid)
        fn = os.path.basename(file_path)
        self.assertEqual(ret2['node_file_name'], fn)
        newfn = file_name if file_name else fn
        self.assertEqual(ret2['file_path'], td + '/' + newfn)
        self.assertEqual(ret2['size'], size)
        filecmp.cmp(file_path, td + '/' + ret2['node_file_name'])
        self.assertEqual(set(os.listdir(td + '/tar1')),
                         set(['file1.txt', 'file2.txt']))
        filecmp.cmp('data/file1.txt', td + '/tar1/file1.txt')
        filecmp.cmp('data/file2.txt', td + '/tar1/file2.txt')

    def test_uncompress(self):
        self.check_uncompress('data/file1.txt.bz', 44, 'file1.txt')
        self.check_uncompress('data/file1.txt.bz.txt', 44)
        self.check_uncompress('data/file1.txt.bz2', 44, 'file1.txt')
        self.check_uncompress('data/file1.txt.bzip', 44, 'file1.txt')
        self.check_uncompress('data/file1.txt.bzip2', 44, 'file1.txt')
        self.check_uncompress('data/file1.txt.gz', 36, 'file1.txt')
        self.check_uncompress('data/file1.txt.gzip', 36, 'file1.txt')

    def check_uncompress(self, file_path, size, file_name=None):
        ret1 = self.impl.file_to_shock(self.ctx, {'file_path': file_path})[0]
        sid = ret1['shock_id']
        td = os.path.abspath(tempfile.mkdtemp(dir=self.cfg['scratch']))
        ret2 = self.impl.shock_to_file(self.ctx, {'shock_id': sid,
                                                  'file_path': td,
                                                  'unpack': 'uncompress'
                                                  }
                                       )[0]
        self.delete_shock_node(sid)
        fn = os.path.basename(file_path)
        self.assertEquals(ret2['node_file_name'], fn)
        self.assertEqual(ret2['size'], size)
        newfn = file_name if file_name else fn
        self.assertEqual(ret2['file_path'], td + '/' + newfn)
        filecmp.cmp('data/file1.txt', td + '/' + ret2['node_file_name'])

    def test_bad_archive(self):
        # haven't figured out how to make a malicious tgz yet
        self.fail_unpack(
            'data/bad_zip.zip', 'unpack', 'Dangerous archive file - entry ' +
            '[../bad_file.txt] points to a file outside the archive directory')
        self.fail_unpack(
            'data/bad_zip2.zip', 'unpack', 'Dangerous archive file - entry ' +
            '[tar1/../../bad_file2.txt] points to a file outside the ' +
            'archive directory')
        self.fail_unpack(
            'data/rootzip.zip', 'unpack', 'Dangerous archive file - entry ' +
            '[/foo/bar] points to a file outside the ' +
            'archive directory')

    def fail_unpack(self, file_path, unpack, error):
        ret1 = self.impl.file_to_shock(self.ctx, {'file_path': file_path})[0]
        sid = ret1['shock_id']
        td = os.path.abspath(tempfile.mkdtemp(dir=self.cfg['scratch']))
        self.fail_download({'shock_id': sid,
                            'file_path': td,
                            'unpack': unpack},
                           error)
        self.delete_shock_node(sid)

    def test_uncompress_on_archive(self):
        self.fail_uncompress_on_archive('data/tar1.tar', 'tar')
        self.fail_uncompress_on_archive('data/tar1.tar.txt', 'tar')
        self.fail_uncompress_on_archive('data/tar1.tgz.txt', 'tar')
        self.fail_uncompress_on_archive('data/tar1.tgz', 'tar', 'tar1.tar')
        self.fail_uncompress_on_archive('data/tar1.tbz', 'tar', 'tar1.tar')
        self.fail_uncompress_on_archive('data/zip1.zip', 'zip')

    def fail_uncompress_on_archive(self, infile, file_type, newfile=None):
        newfile = newfile if newfile else os.path.basename(infile)
        print('*** Running fail_uncompress_on_archive with params {} {} {}'
              .format(infile, file_type, newfile))
        ret1 = self.impl.file_to_shock(self.ctx, {'file_path': infile})[0]
        sid = ret1['shock_id']
        td = os.path.abspath(tempfile.mkdtemp(dir=self.cfg['scratch']))
        err = ('File {}/{} is {} file but only uncompress was specified'
               ).format(td, newfile, file_type)
        self.fail_download(
            {'shock_id': sid, 'file_path': td, 'unpack': 'uncompress'}, err)
        self.delete_shock_node(sid)

    def test_upload_err_no_file_provided(self):
        self.fail_upload(
            {'file_path': ''},
            'No file(s) provided for upload to Shock.')

    def test_upload_err_bad_pack_param(self):
        self.fail_upload(
            {'file_path': 'foo',
             'pack': 'bar'},
            'Invalid pack value: bar')

    def test_upload_err_empty_pack_dir(self):
        tmp_dir = self.cfg['scratch'] + '/emptytest/'
        os.makedirs(tmp_dir)
        self.fail_upload(
            {'file_path': tmp_dir,
             'pack': 'targz'},
            'Directory {} is empty'.format(tmp_dir[0: -1]))

    def test_upload_err_bad_pack_filename(self):
        self.fail_upload(
            {'file_path': '/',
             'pack': 'zip'},
            'Packing root is not allowed')

    def test_pack_gzip(self):
        input_ = 'testgzip'
        tmp_dir = self.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input_)
        new_file_path = self.impl.pack_file(
            self.ctx, {'file_path': file_path, 'pack': 'gzip'})[0]['file_path']
        self.assertEqual(new_file_path, file_path + '.gz')
        with gzip.open(new_file_path, 'rb') as fh2:
            output = fh2.read()
        self.assertEqual(output, input_)

    def test_pack_tgz_with_no_dir(self):
        tmp_dir = os.path.join(self.cfg['scratch'], 'packtartest')
        os.makedirs(tmp_dir)
        self.write_file(os.path.join(tmp_dir, 'intar1.txt'), 'tar1')
        self.write_file(os.path.join(tmp_dir, 'intar2.txt'), 'tar2')
        wd = os.getcwd()
        os.chdir(tmp_dir)
        new_file_path = self.impl.pack_file(
            self.ctx, {'file_path': 'target', 'pack': 'targz'})[0]['file_path']
        os.chdir(wd)
        self.assertEqual(new_file_path,
                         '/kb/module/work/tmp/packtartest/target.tar.gz')
        with tarfile.open(new_file_path) as t:
            self.assertEqual(set(t.getnames()),
                             set(['.', './intar1.txt', './intar2.txt']))

    def test_pack_tgz_with_no_file_name(self):
        tmp_dir = os.path.join(self.cfg['scratch'], 'packtartest2')
        os.makedirs(tmp_dir)
        self.write_file(os.path.join(tmp_dir, 'intar1.txt'), 'tar1')
        self.write_file(os.path.join(tmp_dir, 'intar2.txt'), 'tar2')
        new_file_path = self.impl.pack_file(
            self.ctx, {'file_path': tmp_dir, 'pack': 'targz'})[0]['file_path']
        self.assertEqual(
            new_file_path,
            '/kb/module/work/tmp/packtartest2/packtartest2.tar.gz')
        with tarfile.open(new_file_path) as t:
            self.assertEqual(set(t.getnames()),
                             set(['.', './intar1.txt', './intar2.txt']))

    def test_pack_zip(self):
        tmp_dir = os.path.join(self.cfg['scratch'], 'packziptest')
        os.makedirs(tmp_dir)
        self.write_file(os.path.join(tmp_dir, 'inzip1.txt'), 'zip1')
        self.write_file(os.path.join(tmp_dir, 'inzip2.txt'), 'zip2')
        new_file_path = self.impl.pack_file(
            self.ctx, {'file_path': tmp_dir + '/target',
                       'pack': 'zip'})[0]['file_path']
        self.assertEqual(
            new_file_path,
            '/kb/module/work/tmp/packziptest/target.zip')
        with zipfile.ZipFile(new_file_path) as z:
            self.assertEqual(set(z.namelist()),
                             set(['inzip1.txt', 'inzip2.txt']))

    def test_pack_large_zip(self):

        filename = 'large_file.txt'
        tmp_dir = os.path.join(self.cfg['scratch'], 'packlargeziptest')
        if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
        file_path = os.path.join(tmp_dir, filename)

        size_3GB = 3 * 1024 * 1024 * 1024

        with open(file_path, "wb") as output:
            output.seek(size_3GB)
            output.write('0')

        new_file_path = self.impl.pack_file(
            self.ctx, {'file_path': tmp_dir + '/' + filename,
                       'pack': 'zip'})[0]['file_path']

        self.assertEqual(
            new_file_path,
            '/kb/module/work/tmp/packlargeziptest/{}.zip'.format(filename))
        with zipfile.ZipFile(new_file_path) as z:
            self.assertEqual(set(z.namelist()),
                             set([filename]))

        os.remove(file_path)

    def test_pack_err_no_file_provided(self):
        self.fail_pack(
            {'file_path': ''},
            'file_path is required')

    def test_pack_err_bad_pack_param(self):
        self.fail_pack(
            {'file_path': 'foo',
             'pack': 'bar'},
            'Invalid pack value: bar')

    def test_pack_err_empty_pack_dir(self):
        tmp_dir = self.cfg['scratch'] + '/packemptytest/'
        os.makedirs(tmp_dir)
        self.fail_pack(
            {'file_path': tmp_dir,
             'pack': 'targz'},
            'Directory {} is empty'.format(tmp_dir[0: -1]))

    def test_pack_err_bad_pack_filename(self):
        self.fail_pack(
            {'file_path': '/',
             'pack': 'zip'},
            'Packing root is not allowed')

    def test_download_existing_dir(self):
        ret1 = self.impl.file_to_shock(self.ctx,
                                       {'file_path': 'data/file1.txt'})[0]
        sid = ret1['shock_id']
        d = 'foobarbazbingbang'
        os.mkdir(d)
        ret2 = self.impl.shock_to_file(self.ctx, {'shock_id': sid,
                                                  'file_path': d + '/foo',
                                                  }
                                       )[0]
        self.delete_shock_node(sid)
        self.assertEqual(ret2['node_file_name'], 'file1.txt')
        self.assertEqual(ret2['file_path'], d + '/foo')
        filecmp.cmp('data/file1.txt', d + '/foo')

    def test_download_fail_make_dir(self):
        ret1 = self.impl.file_to_shock(self.ctx,
                                       {'file_path': 'data/file1.txt'})[0]
        sid = ret1['shock_id']
        f = 'whooptywhoopwhee'
        with open(f, 'a'):  # touch
            os.utime(f, None)
        try:
            self.impl.shock_to_file(
                self.ctx, {'shock_id': sid, 'file_path': f + '/foo'})
            self.fail('expecting an OSError here')
        except OSError as e:
            self.assertEqual(e.args, (17, 'File exists'))
        self.delete_shock_node(sid)

    def test_download_err_bad_unpack_param(self):
        self.fail_unpack('data/tar1.tar', 'foo', 'Illegal unpack value: foo')

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
            'Must provide shock ID or handle ID')

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
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': file_path,
             'attributes': {'foopy': [{'bar': 'baz'}]}})[0]
        shock_id = ret1['shock_id']
        retcopy = self.impl.copy_shock_node(self.ctx,
                                            {'shock_id': shock_id})[0]
        new_id = retcopy['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.txt')
        ret2 = self.impl.shock_to_file(
            self.ctx,
            {'shock_id': new_id, 'file_path': file_path2})[0]
        self.delete_shock_node(shock_id)
        self.delete_shock_node(new_id)
        file_name = ret2['node_file_name']
        attribs = ret2['attributes']  # @UnusedVariable
        self.assertEqual(file_name, input_file_name)
        self.assertEqual(attribs, {'foopy': [{'bar': 'baz'}]})
        with open(file_path2, 'r') as fh2:
            output = fh2.read()
        self.assertEqual(output, input_)

    def test_copy_make_handle(self):
        input_ = 'copytesthandle'
        tmp_dir = self.cfg['scratch']
        input_file_name = 'input.txt'
        file_path = os.path.join(tmp_dir, input_file_name)
        with open(file_path, 'w') as fh1:
            fh1.write(input_)
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': file_path,
             'attributes': {'foopy': [{'bar': 'baz'}]}})[0]
        shock_id = ret1['shock_id']
        retcopy = self.impl.copy_shock_node(self.ctx,
                                            {'shock_id': shock_id,
                                             'make_handle': 1})[0]
        new_id = retcopy['shock_id']
        self.delete_shock_node(shock_id)
        self.delete_shock_node(new_id)
        hid = retcopy['handle']['hid']
        handle = self.hs.hids_to_handles([hid])[0]
        self.hs.delete_handles([hid])
        self.check_handle(retcopy['handle'], hid, new_id,
                          '748ff3bbb8d31783c852513422eedb87', 'input.txt')
        self.check_handle(handle, hid, new_id,
                          '748ff3bbb8d31783c852513422eedb87', 'input.txt')

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

    def test_own_node_owned_with_existing_handle(self):
        fp = self.write_file('ownfile23.txt', 'ownfile23')
        r1 = self.impl.file_to_shock(
            self.ctx, {'file_path': fp, 'attributes': {'id': 23}})[0]
        # note this is missing fields that the created handles will have
        handle = {u'id': unicode(r1['shock_id']),
                  u'type': u'shock',
                  u'url': unicode(self.shockURL)}
        handle[u'hid'] = unicode(self.hs.persist_handle(handle))
        handle[u'file_name'] = None
        handle[u'remote_md5'] = None
        r2 = self.impl.own_shock_node(
            self.ctx, {'shock_id': r1['shock_id'], 'make_handle': 1})[0]
        r3 = self.impl.shock_to_file(
            self.ctx, {'shock_id': r1['shock_id'],
                       'file_path': self.cfg['scratch'] + '/foo.txt'})[0]
        self.delete_shock_node(r1['shock_id'])
        self.assertEqual(r1['shock_id'], r2['shock_id'])
        self.assertEqual(handle, r2['handle'])
        self.assertEqual(r3['attributes'], {'id': 23})

    def test_own_node_owned_no_handle(self):
        fp = self.write_file('ownfile25.txt', 'ownfile25')
        r1 = self.impl.file_to_shock(
            self.ctx, {'file_path': fp, 'attributes': {'id': 25}})[0]
        # note this is missing fields that the created handles will have
        r2 = self.impl.own_shock_node(
            self.ctx, {'shock_id': r1['shock_id']})[0]
        r3 = self.impl.shock_to_file(
            self.ctx, {'shock_id': r1['shock_id'],
                       'file_path': self.cfg['scratch'] + '/foo.txt'})[0]
        self.delete_shock_node(r1['shock_id'])
        self.assertEqual(r1['shock_id'], r2['shock_id'])
        self.assertEqual(r2.get('handle'), None)
        self.assertEqual(r3['attributes'], {'id': 25})

    def test_own_node_owned_with_new_handle(self):
        fp = self.write_file('ownfile24.txt', 'ownfile24')
        r1 = self.impl.file_to_shock(
            self.ctx, {'file_path': fp, 'attributes': {'id': 24}})[0]
        r2 = self.impl.own_shock_node(
            self.ctx, {'shock_id': r1['shock_id'], 'make_handle': 1})[0]
        r3 = self.impl.shock_to_file(
            self.ctx, {'shock_id': r1['shock_id'],
                       'file_path': self.cfg['scratch'] + '/foo.txt'})[0]
        self.delete_shock_node(r1['shock_id'])
        self.assertEqual(r1['shock_id'], r2['shock_id'])
        self.check_handle(r2['handle'], r2['handle']['hid'], r1['shock_id'],
                          '98592d7841bf95c2e7ad49d894f77eb3', 'ownfile24.txt')
        self.assertEqual(r3['attributes'], {'id': 24})

    def test_own_node_copy_with_new_handle(self):
        fp = self.write_file('ownfile27.txt', 'ownfile27')
        r1 = self.impl.file_to_shock(
            self.ctx, {'file_path': fp, 'attributes': {'id': 27}})[0]
        sid = r1['shock_id']
        r = requests.put(
            # need to expand test rig for multiple users
            # can't delete this shock node now
            self.shockURL + '/node/' + sid + '/acl/owner?users=kbasetest2',
            headers={'Authorization': 'OAuth ' + self.token})
        r.raise_for_status()

        r2 = self.impl.own_shock_node(
            self.ctx, {'shock_id': sid, 'make_handle': 1})[0]
        r3 = self.impl.shock_to_file(
            self.ctx, {'shock_id': r1['shock_id'],
                       'file_path': self.cfg['scratch'] + '/foo.txt'})[0]
        self.delete_shock_node(r2['shock_id'])
        self.assertNotEqual(r1['shock_id'], r2['shock_id'])
        self.check_handle(r2['handle'], r2['handle']['hid'], r2['shock_id'],
                          'a3a568735be55a9ac810cf433c9bb9ef', 'ownfile27.txt')
        self.assertEqual(r3['attributes'], {'id': 27})

    # def test_own_node_copy_with_no_handle(self):
    #     fp = self.write_file('ownfile28.txt', 'ownfile28')
    #     r1 = self.impl.file_to_shock(
    #         self.ctx, {'file_path': fp, 'attributes': {'id': 28}})[0]
    #     sid = r1['shock_id']
    #     r = requests.put(
    #         # need to expand test rig for multiple users
    #         # can't delete this shock node now
    #         self.shockURL + '/node/' + sid + '/acl/owner?users=kbasetest2',
    #         headers={'Authorization': 'OAuth ' + self.token})
    #     r.raise_for_status()

    #     r2 = self.impl.own_shock_node(self.ctx, {'shock_id': sid})[0]
    #     r3 = self.impl.shock_to_file(
    #         self.ctx, {'shock_id': r1['shock_id'],
    #                    'file_path': self.cfg['scratch'] + '/foo.txt'})[0]
    #     self.delete_shock_node(r2['shock_id'])
    #     self.assertNotEqual(r1['shock_id'], r2['shock_id'])
    #     self.assertEqual(r2['handle'], None)
    #     self.assertEqual(r3['attributes'], {'id': 28})

    def test_own_err_node_not_found(self):
        self.fail_own(
            {'shock_id': '79261fd9-ae10-4a84-853d-1b8fcd57c8f23'},
            'Error getting ACLs for Shock node ' +
            '79261fd9-ae10-4a84-853d-1b8fcd57c8f23: Node not found',
            exception=ShockException)

    def test_own_err_no_node_provided(self):
        self.fail_own(
            {'shock_id': ''}, 'Must provide shock ID')

    def test_translate_ws_name(self):
        self.assertEqual(self.impl.ws_name_to_id(self.ctx, self.ws_info[1])[0],
                         self.ws_info[0])

    def test_translate_ws_name_bad_ws(self):
        badws = 'superbadworkspacename&)^&%)&*)&^&^&('
        with self.assertRaises(WorkspaceError) as context:
            self.impl.ws_name_to_id(self.ctx, badws)
        self.assertEqual('Illegal character in workspace name {}: &'
                         .format(badws),
                         str(context.exception.message))

    def test_save_and_get_objects(self):
        print('**** test_save_and_get_objects ****')
        objs = [{'name': 'whee1',
                 'type': 'Empty.AType-0.1',
                 'data': {'thingy': 1}
                 },
                {'name': 'whee2',
                 'type': 'Empty.AType-1.0',
                 'data': {'thingy': 2}
                 }
                ]
        ws = self.ws_info[0]
        self.impl.save_objects(self.ctx, {'id': ws, 'objects': objs})
        ret = self.impl.get_objects(
            self.ctx,
            {'object_refs': [str(ws) + '/whee2', str(ws) + '/whee1']})
        o1 = ret[0]['data'][0]
        o2 = ret[0]['data'][1]
        self.assertEquals(o1['info'][1], 'whee2')
        self.assertEquals(o1['info'][2], 'Empty.AType-1.0')
        self.assertEquals(o1['data'], {'thingy': 2})
        self.assertEquals(o2['info'][1], 'whee1')
        self.assertEquals(o2['info'][2], 'Empty.AType-0.1')
        self.assertEquals(o2['data'], {'thingy': 1})

        pret = self.ws.get_objects2(
            {'objects': [{'ref': str(ws) + '/whee1'},
                         {'ref': str(ws) + '/whee2'}]})['data']
        p1 = pret[0]['provenance'][0]
        p2 = pret[1]['provenance'][0]

        # this is enough to check that provenance is being saved
        self.assertEquals(
            p1['description'],
            'KBase SDK method run via the KBase Execution Engine')
        self.assertEquals(
            p2['description'],
            'KBase SDK method run via the KBase Execution Engine')
        self.assertEquals(p1['service'], 'DataFileUtil')
        self.assertEquals(p2['service'], 'DataFileUtil')

    def test_save_objects_no_objects(self):
        self.fail_save_objects({'id': 1},
                               'Required parameter objects missing')

    def test_save_objects_no_id(self):
        self.fail_save_objects({'objects': [{}]},
                               'Required parameter id missing')

    def test_save_objects_no_data(self):
        self.fail_save_objects({'id': self.ws_info[0],
                                'objects': [{'name': 'foo',
                                             'type': 'Empty.AType'
                                             }
                                            ]
                                },
                               'Object 1, foo, has no data',
                               exception=WorkspaceError)

    def test_get_objects_ws_exception(self):
        self.fail_get_objects(
            {'object_refs': ['bad%ws/1/1']},
            'Error on ObjectSpecification #1: Illegal character in ' +
            'workspace name bad%ws: %',
            exception=WorkspaceError)

    def test_get_objects_no_objs(self):
        self.fail_get_objects({'object_refs': []},
                              'No objects specified for retrieval')

    def test_get_objects_bad_handle(self):
        infile = self.write_file('foobar', 'foobar')
        ret1 = self.impl.file_to_shock(
            self.ctx, {'file_path': infile, 'make_handle': 1})[0]
        handle_id = ret1['handle']['hid']
        ws = self.ws_info[0]
        info = self.impl.save_objects(
            self.ctx,
            {'id': ws,
             'objects': [{'name': 'bad_handle',
                          'type': 'Empty.AHandle',
                          'data': {'hid': handle_id}
                          }
                         ]
             })[0][0]
        self.delete_shock_node(ret1['shock_id'])
        err = ('Handle error for object {}/{}/{}: The Handle Manager ' +
               'reported a problem while attempting to set Handle ACLs: ' +
               'Unable to set acl(s) on handles {}'
               ).format(ws, info[0], info[4], handle_id)
        self.fail_get_objects({'object_refs': [str(ws) + '/bad_handle']},
                              err, exception=HandleError)

        gret = self.impl.get_objects(
            self.ctx,
            {'object_refs': [str(ws) + '/bad_handle'],
             'ignore_errors': 1})[0]['data']
        self.assertIsNone(gret[0])
        self.hs.delete_handles([handle_id])

    def test_get_objects_ignore_errors(self):
        objs = [{'name': 'whoop',
                 'type': 'Empty.AType-0.1',
                 'data': {'thingy': 1}
                 }
                ]
        ws = self.ws_info[0]
        self.impl.save_objects(self.ctx, {'id': ws, 'objects': objs})
        gret = self.impl.get_objects(
            self.ctx,
            {'object_refs': [str(ws) + '/fakefakefake', str(ws) + '/whoop'],
             'ignore_errors': 1})[0]['data']
        self.assertIsNone(gret[0])
        self.assertEqual(gret[1]['data'], {'thingy': 1})

    def test_versions(self):
        wsver, shockver = self.impl.versions(self.ctx)
        self.assertTrue(semver.match(wsver, '>=0.4.0'))
        self.assertTrue(semver.match(shockver, '>=0.9.0'))

    def fail_own(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.impl.own_shock_node(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def fail_copy(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.impl.copy_shock_node(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def fail_download(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.impl.shock_to_file(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def fail_upload(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.impl.file_to_shock(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def fail_pack(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.impl.pack_file(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def fail_save_objects(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.impl.save_objects(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def fail_get_objects(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.impl.get_objects(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def fail_download_staging_file(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.impl.download_staging_file(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def test_fail_download_staging_file(self):
        invalid_input_params = {'test_params': 'test_params_str'}
        error_msg = "missing 'staging_file_subdir_path' parameter"
        self.fail_download_staging_file(invalid_input_params, error_msg)

    @patch.object(DataFileUtil, "STAGING_FILE_PREFIX", new='/kb/module/work/tmp/')
    def test_download_staging_file(self):
        tmp_dir = self.cfg['scratch']
        test_file = "file1.txt"
        unpack_dir = os.path.join(tmp_dir, self.ctx['user_id'], 
                                            'test_download_staging_file')
        test_file_path = os.path.join(unpack_dir, test_file)
        if not os.path.exists(unpack_dir):
            os.makedirs(unpack_dir)
        shutil.copy('data/'+test_file, test_file_path)

        params = {
            'staging_file_subdir_path': 'test_download_staging_file/file1.txt'
        }

        ret1 = self.impl.download_staging_file(
                self.ctx,
                params
            )[0]
        self.assertRegexpMatches(ret1['copy_file_path'], tmp_dir + '/.*/' + 'file1.txt')

    @patch.object(DataFileUtil, "STAGING_FILE_PREFIX", new='/kb/module/work/tmp/')
    def test_download_staging_file_compressed_file(self):
        tmp_dir = self.cfg['scratch']
        test_file = "file1.txt.gz"
        unpack_dir = os.path.join(tmp_dir, self.ctx['user_id'], 
                                        'test_download_compressed_staging_file')
        test_file_path = os.path.join(unpack_dir, test_file)
        if not os.path.exists(unpack_dir):
            os.makedirs(unpack_dir)
        shutil.copy('data/'+test_file, test_file_path)

        params = {
            'staging_file_subdir_path': 'test_download_compressed_staging_file/file1.txt.gz'
        }

        ret1 = self.impl.download_staging_file(
                self.ctx,
                params
            )[0]
        self.assertRegexpMatches(ret1['copy_file_path'], tmp_dir + '/.*/' + 'file1.txt')

    @patch.object(DataFileUtil, "STAGING_FILE_PREFIX", new='/kb/module/work/tmp/')
    def test_download_staging_file_archive_file(self):
        tmp_dir = self.cfg['scratch']
        test_file = "zip1.zip"
        unpack_dir = os.path.join(tmp_dir, self.ctx['user_id'], 
                                                'test_download_archive_staging_file')
        test_file_path = os.path.join(unpack_dir, test_file)
        if not os.path.exists(unpack_dir):
            os.makedirs(unpack_dir)
        shutil.copy('data/'+test_file, test_file_path)

        params = {
            'staging_file_subdir_path': 'test_download_archive_staging_file/zip1.zip'
        }

        ret1 = self.impl.download_staging_file(
                self.ctx,
                params
            )[0]
        self.assertRegexpMatches(ret1['copy_file_path'], tmp_dir + '/.*/' + 'zip1.zip')
        self.assertTrue(set(['tar1', 'zip1.zip']) <= 
                    set(os.listdir(os.path.dirname(ret1['copy_file_path']))))
        self.assertEqual(os.stat(os.path.join("data", "zip1.zip")).st_size,
                            os.stat(ret1['copy_file_path']).st_size)

    def fail_download_web_file(self, params, error, 
                                        exception=ValueError, startswith=False):
        with self.assertRaises(exception) as context:
            self.impl.download_web_file(self.ctx, params)
        if startswith:
            self.assertTrue(str(context.exception.message).startswith(error),
                            "Error message {} does not start with {}".format(
                                str(context.exception.message),
                                error))
        else:    
            self.assertEqual(error, str(context.exception.message))

    def test_fail_download_web_file(self):
        invalid_input_params = {'file_url': 'file_url_str'}
        error_msg = "missing 'download_type' parameter"
        self.fail_download_web_file(invalid_input_params, error_msg)

        invalid_input_params = {'download_type': 'download_type_str'}
        error_msg = "missing 'file_url' parameter"
        self.fail_download_web_file(invalid_input_params, error_msg)   

        invalid_input_params = {
                        'download_type': 'invalid_download_type',
                        'file_url': 'http://www.google.com'}
        error_msg = "[invalid_download_type] download_type is invalid.\n"
        error_msg += "Please use one of ['Direct Download', 'FTP', 'DropBox', 'Google Drive']"
        self.fail_download_web_file(invalid_input_params, error_msg) 

        invalid_input_params = {
                        'download_type': 'Direct Download',
                        'file_url': 'invalid_URL'}
        error_msg = "Cannot connect to URL: invalid_URL"
        self.fail_download_web_file(invalid_input_params, error_msg, startswith=True)

    def test_fail_download_web_file_google_drive(self):
        # invalid Google Drive params
        invalid_input_params = {
                        'download_type': 'Google Drive',
                        'file_url': 'http://www.google.com'}
        error_msg = "Invalid Google Drive Link: http://www.google.com"
        self.fail_download_web_file(invalid_input_params, error_msg)


        invalid_input_params = {
                        'download_type': 'Google Drive',
                        'file_url': 'https://drive.google.com/invalid_link'}
        error_msg = 'Unexpected Google Drive share link.\n'
        error_msg += 'URL: https://drive.google.com/invalid_link'
        self.fail_download_web_file(invalid_input_params, error_msg)

    def test_fail_download_web_file_dropbox(self):
        # invalid DropBox params
        invalid_input_params = {
                        'download_type': 'DropBox',
                        'file_url': 'http://www.dropbox.com'}
        error_msg = "Invalid DropBox Link: http://www.dropbox.com"
        self.fail_download_web_file(invalid_input_params, error_msg) 

    def test_fail_download_web_file_ftp(self):
        # invalid FTP params
        invalid_input_params = {
                        'download_type': 'FTP',
                        'file_url': 'http://www.google.com'}
        error_msg = "Invalid FTP Link: http://www.google.com"
        self.fail_download_web_file(invalid_input_params, error_msg)  

        fake_ftp_url = 'ftp://FAKE_USER:FAKE_PASSWORD'
        fake_ftp_url += '@ftp.com/Sample1.fastq'
        invalid_input_params = {
                        'download_type': 'FTP',
                        'file_url': fake_ftp_url}
        error_msg = "Currently we only support anonymous FTP"
        self.fail_download_web_file(invalid_input_params, error_msg)  

        invalid_input_params = {
                        'download_type': 'FTP',
                        'file_url': 'ftp://FAKE_SERVER/Sample1.fastq'}
        error_msg = "Cannot connect:"
        self.fail_download_web_file(invalid_input_params, error_msg, 
                                                            startswith=True) 

        fake_ftp_url = 'ftp://anonymous:FAKE_PASSWORD'
        fake_ftp_url += '@ftp.dlptest.com/24_Hour/Sample1.fastq'
        invalid_input_params = {
                        'download_type': 'FTP',
                        'file_url': fake_ftp_url}
        error_msg = "Cannot login:"
        self.fail_download_web_file(invalid_input_params, error_msg, 
                                                            startswith=True)  

        invalid_input_params = {
                        'download_type': 'FTP',
                        'file_url': 'ftp://ftp.uconn.edu/48_hour/nonexist.txt'}
        error_msg = "File nonexist.txt does NOT exist in FTP path: "
        error_msg += "ftp.uconn.edu/48_hour"
        self.fail_download_web_file(invalid_input_params, error_msg) 

    def test_download_direct_link_uncompress_file(self):
        # Box direct download link of 'file1.txt'
        file_url = 'https://anl.box.com/shared/static/'
        file_url += '4ero6ld3322gnfcbssegglbdbpdvpzae.txt'
        params = {
            'download_type': 'Direct Download',
            'file_url': file_url
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'file1.txt')
        self.assertEqual(os.stat(os.path.join("data", "file1.txt")).st_size,
                    os.stat(ret1['copy_file_path']).st_size)

    def test_download_direct_link_with_no_content_disposition(self):
        # direct download link with no 'content-disposition' header
        file_url = 'http://molb7621.github.io/workshop/_downloads/SP1.fq'
        params = {
            'download_type': 'Direct Download',
            'file_url': file_url
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'SP1.fq')

    def test_download_direct_link_compress_file(self):
        # Box direct download link of 'file1.txt.bzip'
        file_url = 'https://anl.box.com/shared/static/'
        file_url += '67iny8ew2ee7vnycpculjvpsg74i5dav.bzip'
        params = {
            'download_type': 'Direct Download',
            'file_url': file_url
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'file1.txt')
        self.assertEqual(os.stat(os.path.join("data", "file1.txt")).st_size,
                    os.stat(ret1['copy_file_path']).st_size) 

    def test_download_direct_link_archive_file(self):
        # Box direct download link of 'zip1.zip'
        file_url = 'https://anl.box.com/shared/static/'
        file_url += 'ra6utd1qd9fdr6f0dgoqi6jhe4uy2xe8.zip'
        params = {
            'download_type': 'Direct Download',
            'file_url': file_url
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'zip1.zip')
        self.assertTrue(set(['tar1', 'zip1.zip']) <= 
                    set(os.listdir(os.path.dirname(ret1['copy_file_path']))))
        self.assertEqual(os.stat(os.path.join("data", "zip1.zip")).st_size,
                    os.stat(ret1['copy_file_path']).st_size) 

    def test_download_dropbox_link_uncompress_file(self):
        # dropbox link of 'file1.txt'
        file_url = 'https://www.dropbox.com/s/'
        file_url += 'w5ct52rp95cukwq/file1.txt?dl=0'
        params = {
            'download_type': 'DropBox',
            'file_url': file_url
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'file1.txt')
        self.assertEqual(os.stat(os.path.join("data", "file1.txt")).st_size,
                    os.stat(ret1['copy_file_path']).st_size)

    def test_download_dropbox_link_missing_question_mark(self):
        # dropbox link missing question mark of 'file1.txt'
        file_url = 'https://www.dropbox.com/s/'
        file_url += 'w5ct52rp95cukwq/file1.txt'
        params = {
            'download_type': 'DropBox',
            'file_url': file_url
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'file1.txt')
        self.assertEqual(os.stat(os.path.join("data", "file1.txt")).st_size,
                    os.stat(ret1['copy_file_path']).st_size)

    def test_download_dropbox_link_compress_file(self):
        # dropbox link of 'file1.txt.gz'
        file_url = 'https://www.dropbox.com/s/'
        file_url += 'tw0vvif7hpqhi90/file1.txt.gz?dl=0'
        params = {
            'download_type': 'DropBox',
            'file_url': file_url
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'file1.txt')
        self.assertEqual(os.stat(os.path.join("data", "file1.txt")).st_size,
                    os.stat(ret1['copy_file_path']).st_size)

    def test_download_dropbox_link_archive_file(self):
        # dropbox link of 'zip1.zip'
        file_url = 'https://www.dropbox.com/s/'
        file_url += 'l95ynq1vswfjdn9/zip1.zip'
        params = {
            'download_type': 'DropBox',
            'file_url': file_url
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'zip1.zip')
        self.assertTrue(set(['tar1', 'zip1.zip']) <= 
                    set(os.listdir(os.path.dirname(ret1['copy_file_path']))))
        self.assertEqual(os.stat(os.path.join("data", "zip1.zip")).st_size,
                    os.stat(ret1['copy_file_path']).st_size)

    def test_download_google_drive_link_uncompress_file(self):
        # google drive link of 'file1.txt'
        file_url = 'https://drive.google.com/open?'
        file_url += 'id=0B0exSa7ebQ0qX01mZ3FaRzhuMDQ'
        params = {
            'download_type': 'Google Drive',
            'file_url': file_url
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'file1.txt')
        self.assertEqual(os.stat(os.path.join("data", "file1.txt")).st_size,
                    os.stat(ret1['copy_file_path']).st_size)

    def test_download_google_drive_link_compress_file(self):
        # google drive link of 'file1.txt.gzip'
        file_url = 'https://drive.google.com/file/d/'
        file_url += '0B0exSa7ebQ0qU1U5YmxMRktkbmc/view?usp=sharing'
        params = {
            'download_type': 'Google Drive',
            'file_url': file_url
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'file1.txt')
        self.assertEqual(os.stat(os.path.join("data", "file1.txt")).st_size,
                    os.stat(ret1['copy_file_path']).st_size)

    def test_download_google_drive_link_archive_file(self):
        # google drive link of 'zip1.zip'
        file_url = 'https://drive.google.com/open?'
        file_url += 'id=0B0exSa7ebQ0qcEhRaDJoVDJSTkk'
        params = {
            'download_type': 'Google Drive',
            'file_url': file_url
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'zip1.zip')
        self.assertTrue(set(['tar1', 'zip1.zip']) <= 
                    set(os.listdir(os.path.dirname(ret1['copy_file_path']))))
        self.assertEqual(os.stat(os.path.join("data", "zip1.zip")).st_size,
                    os.stat(ret1['copy_file_path']).st_size)

    def test_download_ftp_link_uncompress_file(self):

        fq_filename = "file1.txt"

        ftp_connection = ftplib.FTP('ftp.uconn.edu')
        ftp_connection.login('anonymous', 'anonymous@domain.com')
        ftp_connection.cwd("/48_hour/")

        if fq_filename not in ftp_connection.nlst():
            fh = open(os.path.join("data", fq_filename), 'rb')
            ftp_connection.storbinary('STOR file1.txt', fh)
            fh.close()

        params = {
            'download_type': 'FTP',
            'file_url': 'ftp://ftp.uconn.edu/48_hour/file1.txt',
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'file1.txt')
        self.assertEqual(os.stat(os.path.join("data", fq_filename)).st_size,
                                    os.stat(ret1['copy_file_path']).st_size)

    def test_download_ftp_link_compress_file(self):

        fq_filename = "file1.txt.bz"

        ftp_connection = ftplib.FTP('ftp.uconn.edu')
        ftp_connection.login('anonymous', 'anonymous@domain.com')
        ftp_connection.cwd("/48_hour/")

        if fq_filename not in ftp_connection.nlst():
            fh = open(os.path.join("data", fq_filename), 'rb')
            ftp_connection.storbinary('STOR file1.txt.bz', fh)
            fh.close()

        params = {
            'download_type': 'FTP',
            'file_url': 'ftp://ftp.uconn.edu/48_hour/file1.txt.bz',
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'file1.txt')
        self.assertEqual(os.stat(os.path.join("data", "file1.txt")).st_size,
                            os.stat(ret1['copy_file_path']).st_size)

    def test_download_ftp_link_archive_file(self):

        fq_filename = "zip1.zip"

        ftp_connection = ftplib.FTP('ftp.uconn.edu')
        ftp_connection.login('anonymous', 'anonymous@domain.com')
        ftp_connection.cwd("/48_hour/")

        if fq_filename not in ftp_connection.nlst():
            fh = open(os.path.join("data", fq_filename), 'rb')
            ftp_connection.storbinary('STOR zip1.zip', fh)
            fh.close()

        params = {
            'download_type': 'FTP',
            'file_url': 'ftp://ftp.uconn.edu/48_hour/zip1.zip',
        }

        ret1 = self.impl.download_web_file(self.ctx, params)[0]
        self.assertIsNotNone(ret1['copy_file_path'])
        self.assertEqual(os.path.basename(ret1['copy_file_path']),
                         'zip1.zip')
        self.assertTrue(set(['tar1', 'zip1.zip']) <= 
                    set(os.listdir(os.path.dirname(ret1['copy_file_path']))))
        self.assertEqual(os.stat(os.path.join("data", "zip1.zip")).st_size,
                            os.stat(ret1['copy_file_path']).st_size)

    def mock_retrieve_filepath(file_url):
        print 'Mocking _retrieve_filepath'
        print "Mocking connecting file_url: {}".format(file_url)
        copy_file_path = 'test_file_path'
        return copy_file_path

    @patch.object(DataFileUtil, "_retrieve_filepath", side_effect=mock_retrieve_filepath)
    def test_download_to_file_HTTPError(self, _retrieve_filepath):
        fake_http_url = 'http://www.google.com/fake'
        invalid_input_params = {
                        'download_type': 'Direct Download',
                        'file_url': fake_http_url}
        error_msg = "Error contacting server at {}. Code: ".format(fake_http_url)
        self.fail_download_web_file(invalid_input_params, error_msg, startswith=True)

    @patch.object(DataFileUtil, "_retrieve_filepath", side_effect=mock_retrieve_filepath)
    def test_download_to_file_URLError(self, _retrieve_filepath):
        fake_url = 'http://fake'
        invalid_input_params = {
                        'download_type': 'Direct Download',
                        'file_url': fake_url}
        error_msg = "Error contacting server at {}. Reason: ".format(fake_url)
        self.fail_download_web_file(invalid_input_params, error_msg, startswith=True)


