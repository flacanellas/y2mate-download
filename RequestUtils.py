#!/usr/bin/python3.8
# -*- coding: utf-8 -*-

from urllib.parse import urlparse

def getContentType(type):
    '''Get Content-Type from the list'''
    contentType = {
        'form': 'application/x-www-form-urlencoded; charset=UTF-8',
        'html': 'text/html',
        'json': 'application/json; charset=UTF-8',
        'text': 'text/plain',
        'xml':  'application/xml'
    }

    return contentType[type] if type in contentType else None

def getChromeAgent():
    '''Return Google Chrome User Agent'''

    return 'Mozilla/5.0 (X11; Linux x86_64)' + \
        'AppleWebKit/537.36 (KHTML, like Gecko)' + \
        'Chrome/90.0.4430.93 Safari/537.36'

def urlGetNetloc(url):
    '''Get the netloc (network locality) of a url'''

    return urlparse(url).netloc
def urlGetPath(url):
    '''Get the path of a url'''

    return urlparse(url).path

def urlGetScheme(url):
    '''Get the scheme of a url'''

    return urlparse(url).scheme
