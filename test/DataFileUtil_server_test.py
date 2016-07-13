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
        cls.shockURL = cls.cfg['shock-url']
        cls.ws = Workspace(cls.cfg['workspace-url'], token=cls.token)
        cls.hs = HandleService(url=cls.cfg['handle-service-url'],
                               token=cls.token)
        cls.impl = DataFileUtil(cls.cfg)
        suffix = int(time.time() * 1000)
        shutil.rmtree(cls.cfg['scratch'])
        os.mkdir(cls.cfg['scratch'])
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
        file_path2 = os.path.join(tmp_dir, 'output.txt')
        ret2 = self.impl.shock_to_file(
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
        file_path = self.write_file('input.txt', 'Test2!!!')
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': file_path})[0]
        shock_id = ret1['shock_id']
        file_path2 = os.path.join(self.cfg['scratch'], 'output.txt')
        ret2 = self.impl.shock_to_file(
            self.ctx,
            {'shock_id': shock_id, 'file_path': file_path2})[0]
        file_name = ret2['node_file_name']
        attribs = ret2['attributes']
        self.assertEqual(file_name, 'input.txt')
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
        self.assertEqual(file_name1, 'input1.txt')
        self.assertIsNone(attribs1)
        with open(outfile1, 'r') as fh:
            output = fh.read()
        self.assertEqual(output, 'filestoshock1')

        file_name2 = ret2[1]['node_file_name']
        attribs2 = ret2[1]['attributes']
        self.assertEqual(file_name2, 'input2.txt')
        self.assertIsNone(attribs2)
        with open(outfile2, 'r') as fh:
            output = fh.read()
        self.assertEqual(output, 'filestoshock2')

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
            {'file_path': file_path, 'gzip': 1})[0]
        shock_id = ret1['shock_id']
        file_path2 = os.path.join(tmp_dir, 'output.txt')
        ret2 = self.impl.shock_to_file(
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

    def test_gzip_already_gzipped(self):
        self.check_gzip_skip('input.txt.gz', 'gz test')
        self.check_gzip_skip('input.txt.tgz', 'tgz test')
        self.check_gzip_skip('input.txt.gzip', 'gzip test')

    def check_gzip_skip(self, input_file_name, contents):
        file_path = self.write_file(input_file_name, contents)
        ret1 = self.impl.file_to_shock(
            self.ctx,
            {'file_path': file_path, 'gzip': 1})[0]
        shock_id = ret1['shock_id']
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

    def test_unpack_archive(self):
        self.check_unpack_archive('data/tar1.tar')
        self.check_unpack_archive('data/tar1.tar.txt')
        self.check_unpack_archive('data/tar1.tgz')
        self.check_unpack_archive('data/tar1.tar.gz')
        self.check_unpack_archive('data/tar1.tar.gzip')
        self.check_unpack_archive('data/tar1.tbz')
        self.check_unpack_archive('data/tar1.tar.bz')
        self.check_unpack_archive('data/tar1.tar.bz2')
        self.check_unpack_archive('data/tar1.tar.bzip')
        self.check_unpack_archive('data/tar1.tar.bzip2')
        self.check_unpack_archive('data/zip1.zip')

    def check_unpack_archive(self, file_path):
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
        self.assertEquals(ret2['node_file_name'], fn)
        filecmp.cmp(file_path, td + '/' + ret2['node_file_name'])
        self.assertEqual(set(os.listdir(td + '/tar1')),
                         set(['file1.txt', 'file2.txt']))
        filecmp.cmp('data/file1.txt', td + '/tar1/file1.txt')
        filecmp.cmp('data/file2.txt', td + '/tar1/file2.txt')

    def test_uncompress(self):
        self.check_uncompress('data/file1.txt.bz')
        self.check_uncompress('data/file1.txt.bz.txt')
        self.check_uncompress('data/file1.txt.bz2')
        self.check_uncompress('data/file1.txt.bzip')
        self.check_uncompress('data/file1.txt.bzip2')
        self.check_uncompress('data/file1.txt.gz')
        self.check_uncompress('data/file1.txt.gzip')

    def check_uncompress(self, file_path):
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
        filecmp.cmp('data/file1.txt', td + '/' + ret2['node_file_name'])

    def test_bad_archive(self):
        self.fail_unpack(
            'data/bad_zip.zip', 'unpack', 'Dangerous archive file - entry ' +
            '[../bad_file.txt] points to a file outside the archive directory')
        self.fail_unpack(
            'data/bad_zip2.zip', 'unpack', 'Dangerous archive file - entry ' +
            '[tar1/../../bad_file2.txt] points to a file outside the ' +
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
        self.fail_unpack('data/tar1.tar', 'uncompress',
                         'File is tar file but only uncompress was specified')
        self.fail_unpack('data/tar1.tgz', 'uncompress',
                         'File is tar file but only uncompress was specified')
        self.fail_unpack('data/zip1.zip', 'uncompress',
                         'File is zip file but only uncompress was specified')

    def test_upload_err_no_file_provided(self):
        self.fail_upload(
            {'file_path': ''},
            'No file provided for upload to Shock.')

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
            {'objects': [{'ref': str(ws) + '/whee1',
                          'ref': str(ws) + '/whee2'}]})['data']
        p1 = pret[0]['provenance'][0]
        p2 = pret[0]['provenance'][0]
        # this is enough to check that provenance is being saved
        self.assertEquals(
            p1['description'],
            'KBase SDK method run via the KBase Execution Engine')
        self.assertEquals(
            p2['description'],
            'KBase SDK method run via the KBase Execution Engine')
        self.assertEquals(p1['service'], 'use_set_provenance')
        self.assertEquals(p2['service'], 'use_set_provenance')

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

    def fail_save_objects(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.impl.save_objects(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def fail_get_objects(self, params, error, exception=ValueError):
        with self.assertRaises(exception) as context:
            self.impl.get_objects(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))
