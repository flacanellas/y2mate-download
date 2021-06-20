#!/usr/bin/python3.8
# -*- coding: utf-8 -*-

from urllib.parse import urlparse
import requests

class Request:
    '''Simple wrapper for make HTTP requests'''

    def __init__(
            self, method = 'GET', url = '', headers = {}, data = {}, \
            session = None, debug = False \
        ):
        self.__allowedMethods = ['GET', 'POST']
        self.__data     = data
        self.__debug    = debug
        self.__headers  = headers
        self.__method   = method
        self.__session  = session
        self.__url      = url
        self.request  = None
        self.response = None
    
    def addData(self, key = '', value = ''):
        '''Add data item to data dict'''

        if key == '' or value == '':
            print('[Error] Argument cannot be empty!')

        self.__data.update({ key: value })

    def addHeader(self, key = '', value = ''):
        '''Add header to this request'''

        if key == '' or value == '':
            print('[Error] Argument cannot be empty!')

        self.__headers.update({ key: value })

    def addHeaders(self, headers = dict):
        '''Add multiple headers to this request'''

        if type(headers) != type({}):
            print('[Error] Headers argument mus be an dictionary!')

        [self.addHeader(k,v) for k,v in headers.items()]

    def debugRequest(self):
        '''Prints HTTP request's data'''

        pr = self.__preparedRequest
        
        headers = '\r\n'.join(
            ' {}: {}'.format(k, v) for k,v in pr.headers.items()
        )
        debugText = '{start}\n{method} {uri}\n{headers}\n{stop}\n{body}\n\n' \
            .format(
                start   = '-' * 50,
                stop    = '-' * 50,
                body    = '' if not pr.body else pr.body,
                headers = headers,
                method  = pr.method,
                uri     = pr.url
            )
        print( debugText )

    def debugResponse(self):
        '''Prints HTTP Response's data'''

        r = self.response

        url = urlparse( r.request.url )
        header = '{} {} {}'.format( r.status_code, r.reason, url.path )
        
        headers = r.headers
        headers = '\r\n'.join(
            ' {}: {}'.format(k, v) for k,v in r.headers.items()
        )
        debugText = '{start}\n{header}\n{headers}\n\n{content}\n{stop}\n' \
            .format(
                start   = '-' * 50,
                stop    = '-' * 50,
                content = r.text,
                header  = header,
                headers = headers
            )

        print(debugText)

    def do(self):
        '''Do request and return the response'''

        if not self.__method.upper() in self.__allowedMethods:
            print( '[ERROR] Method \'{}\' not allowed!'.format(method) )
        
        if len(self.__url) == 0:
            print( '[ERROR] url is empty!' )

        if self.__session is None:
            self.__session = requests.Session()
        
        # PREPARE REQUEST
        # ----------------------------------------------------------------------
        # POST REQUEST
        if self.__method == 'POST':
            self.request = requests.Request( self.__method, self.__url, \
                self.__headers, data = self.__data )
        # GET REQUEST
        else:
            self.request = requests.Request( self.__method, self.__url, \
                self.__headers )
        # ----------------------------------------------------------------------

        self.__preparedRequest = self.request.prepare()

        if self.__debug:
            self.debugRequest()
        
        # SEND REQUEST
        self.response = self.__session \
            .send( self.__preparedRequest, verify = True )

        if self.__debug:
            self.debugResponse()

        return self.response

    def getCookies(self, cookies = []):
        '''Get cookie from HTTP request's response'''

        if not self.response:
            print('[Error] You do the request first!')

        _cookies = dict()
        [_cookies.update({c: self.response.cookies.get(c) }) for c in cookies]
        return _cookies

    def getAllCookies(self):
        '''Get all cookies from HTTP request's response'''

        if not self.response:
            print('[Error] You do the request first!')

        return dict( self.response.cookies )

    def getResponseHeader(self, key):
        '''Get header from response'''

        return self.response.headers[key]
