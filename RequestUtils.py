#!/usr/bin/python3.8
# -*- coding: utf-8 -*-

from urllib.parse import urlparse

def urlGetPath(url):
    '''Get the path of a url'''

    return urlparse(url).path

def urlGetNetloc(url):
    '''Get the netloc (network locality) of a url'''

    return urlparse(url).netloc
