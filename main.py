#!/usr/bin/python

import requests
import sys
import time
import hashlib
import os
from requests.cookies import create_cookie
import json


def timestamp():
    return str(int(time.time() * 1000))


class YoudaoNoteSession(requests.Session):
    user_api_base = 'https://note.youdao.com/yws/api/personal'
    doc_download_base = 'https://note.youdao.com/ydoc/api/personal'

    def __init__(self):
        requests.Session.__init__(self)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }

    def _get_file_type(self, fileName):
        extName = os.path.splitext(fileName)[1]
        if extName == '.note':
            return 'note'
        else:
            return 'file'

    def _save_binary_response_to_file(self, res, destPath):
        if res.status_code == 200:
            with open(destPath, 'w') as fp:
                for chunk in res:
                    fp.write(chunk)

    def _download_to_file(self, fileEntry, saveDir):
        fileId = fileEntry['id']
        version = fileEntry['version']
        name = fileEntry['name']
        downloadUrl = '{user_api_base}/sync?method=download' \
                      '&fileId={fileId}' \
                      '&version={version}' \
                      '&cstk={cstk}' \
                      '&keyfrom=web' \
                      .format(
                          user_api_base=self.user_api_base,
                          fileId=fileId,
                          version=version,
                          cstk=self.cstk
                      )
        response = self.get(downloadUrl, stream=True)
        self._save_binary_response_to_file(
            res=response, destPath='%s/%s' % (saveDir, name))

    def _download_note_to_docx(self, id, saveDir, name):
        docxDownloadUrl = '{doc_download_base}/doc?method=download-docx' \
                          '&fileId={fileId}' \
                          '&cstk={cstk}' \
                          '&keyfrom=web' \
                          .format(
                              doc_download_base=self.doc_download_base,
                              fileId=id,
                              cstk=self.cstk
                          )
        response = self.get(docxDownloadUrl)
        fileName = '%s.docx' % os.path.splitext(name)[0]
        self._save_binary_response_to_file(
            res=response, destPath='%s/%s' % (saveDir, fileName))

    def _download_dir(self, id, dirName, saveDir):
        subDir = saveDir + '/' + dirName
        try:
            os.lstat(subDir)
        except OSError:
            os.mkdir(subDir)
        self._download_file_recursively(id, subDir)

    def _download_object(self, id, name, fileEntry, saveDir):
        if self._get_file_type(name) == 'note':
            print('Processing %s' % (name))
            self._download_note_to_docx(id, saveDir, name)
        else:
            print('Processing %s' % (name))
            self._download_to_file(fileEntry, saveDir)

    def _analyse_response(self, jsonObj, count, saveDir, lastId):
        for entry in jsonObj['entries']:
            fileEntry = entry['fileEntry']
            id = fileEntry['id']
            name = fileEntry['name']
            print('Processing %s' % (name))
            if fileEntry['dir']:
                self._download_dir(id, name, saveDir)
            else:
                self._download_object(id, name, fileEntry, saveDir)
            count = count + 1
            lastId = id
        return count, lastId

    def _download_file_recursively(self, id, saveDir):
        fileUrl = '{user_api_base}/file/{fileId}?' \
                  'all=true' \
                  '&f=true' \
                  '&len=30' \
                  '&sort=1' \
                  '&isReverse=false' \
                  '&method=listPageByParentId' \
                  '&keyfrom=web' \
                  '&cstk={cstk}' \
                  .format(
                      user_api_base=self.user_api_base,
                      fileId=id,
                      cstk=self.cstk
                  )
        lastId = None
        count = 0
        total = 1
        while count < total:
            if lastId == None:
                response = self.get(fileUrl)
            else:
                response = self.get(fileUrl + '&lastId=%s' % lastId)
            jsonObj = json.loads(response.content)
            total = jsonObj['count']
            count, lastId = self._analyse_response(
                jsonObj, count, saveDir, lastId)

    def getAll(self, saveDir):
        rootId = self.getRoot()
        self._download_file_recursively(rootId, saveDir)

    def getRoot(self):
        rootUrl = '{user_api_base}/file?method=getByPath&keyfrom=web&cstk={cstk}'.format(
            user_api_base=self.user_api_base,
            cstk=self.cstk)
        data = {
            'path': '/',
            'entire': 'true',
            'purge': 'false',
            'cstk': self.cstk
        }
        response = self.post(rootUrl, data=data)
        jsonObj = json.loads(response.content)
        return jsonObj['fileEntry']['id']

    def login(self):
        # 请根据实际情况从你的cookie中取出如下字段填充进来，取cookies的方法很简单，打开chrome的F12调试模式，看看xhr请求的header里面的cookie信息吧
        self.cookies.set('OUTFOX_SEARCH_USER_ID_NCOO', '')
        self.cookies.set('OUTFOX_SEARCH_USER_ID', '')
        self.cookies.set('__yadk_uid', '')
        self.cookies.set('_ga', '')
        self.cookies.set('YNOTE_USER', '')
        self.cookies.set('Hm_lvt_4566b2fb63e326de8f2b8ceb1ec367f2', '')
        self.cookies.set('P_INFO', '')
        self.cookies.set('JSESSIONID', '')
        self.cookies.set('Hm_lvt_30b679eb2c90c60ff8679ce4ca562fcc', '')
        self.cookies.set('YNOTE_CSTK', '')
        self.cookies.set('_gid', '')
        self.cookies.set('Hm_lpvt_30b679eb2c90c60ff8679ce4ca562fcc', '')
        self.cookies.set('YNOTE_SESS', '')
        self.cookies.set('YNOTE_PERS', '')
        self.cookies.set('YNOTE_LOGIN', '')
        self.cstk = ''


if __name__ == '__main__':
    if len(sys.argv) == 2:
        saveDir = sys.argv[1]
    else:
        saveDir = '.'
    sess = YoudaoNoteSession()
    sess.login()
    sess.getAll(saveDir)
