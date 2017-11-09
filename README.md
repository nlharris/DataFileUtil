[![Build Status](https://travis-ci.org/rsutormin/DataFileUtil.svg?branch=master)](https://travis-ci.org/rsutormin/DataFileUtil)

# DataFileUtil
---

## Utility functions for operating on files and data objects in KBase data stores like Shock and the Workspace


DataFileUtil is the lowest level wrapper around the KBase data stores, including the workspace, shock, and handle services. It thus handles operations on files, including file transfer and compression, as well as operations on KBase data objects.

Assuming DataFileUtil is being called in the context of a set of local SDK modules calling each other, all file operations occur in the KBase job execution environment.

For any given type of data, the developer should use the appropriate existing SDK module for that data type regardless of whether the data is an object or a file. This appropriate data type module should also contain the logic for deciding how the data is stored, including which KIDL type specification is used as well as which data store.

Some examples of methods available in DataFileUtil:
- Download from external URL
- File un/compression (gzip, tar, zip)
- Upload to shock
- Download from shock
- Download from staging area to scratch space in SDK Docker container
- Upload/download from WS
- Copy shock node and gain permissions, files and their metadata

All methods can be browsed in the DataFileUtil KIDL type spec:
https://github.com/kbaseapps/DataFileUtil/blob/master/DataFileUtil.spec


### KBase module development design pattern notes

Data that will be used frequently should be stored in a workspace object, if you can retrieve and parse it faster than the entire raw data file. Even better if there is a standard format for the data type, which can serve as the de facto data storage structure stored as a file shock and as a reference in an appropriate workspace object. If the data is too large you may need to split it into multiple workspace objects.

Note that there may be limits on the size of data, number of files, and time of data transfer as well as requirements for network speed.

### Code examples

Translate a workspace name to id:
```python
dfu = DataFileUtil(self.callback_url)
  if wsname:
      self.log('Translating workspace name to id')
      if not isinstance(wsname, six.string_types):
          raise ValueError('wsname must be a string')
      wsid = dfu.ws_name_to_id(wsname)
      self.log('translation done')
```

Download a file from shock:
```python
params = {'shock_id': handle['id'],
                  'unpack': 'uncompress',
                  'file_path': os.path.join(self.scratch, handle['id'])
                  }
        # download
dfu = DataFileUtil(self.callback_url)
ret = dfu.shock_to_file(params)
```

Download files from external URL:
```python
fwdpath = dfu.download_web_file(
                        {'file_url': fwd,
                        'download_type': download_type}).get(
                                        'copy_file_path')
revpath = dfu.download_web_file(
            {'file_url': rev,
            'download_type': download_type}).get(
                            'copy_file_path') if rev else None
```





#### Documentation dependencies

SDK, SDK module, docker container, execution environment, narrative, code cell, shock, shock node, shock service, app chain, workspace, workspace object, workspace service, reference, handle service, scratch space.


