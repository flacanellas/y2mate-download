#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
# Author:  Francisca Cañellas
# Email:   francisca.leonor.alejandra.c@gmail.com
# Versión: DEV 0.0.1
# Date:    21-05-2021

import AdvancedHTMLParser
import argparse
import copy
import requests
from tqdm import tqdm
from sys import argv


def print_HTTP( req ):
    '''
    Debug HTTP prepared request
    '''
    return '{}\n{}\r\n{}\r\n\r\n{}\n{}\n\n'.format(
        '-----------START REQUEST-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
        '-----------STOP REQUEST------------'
    )

def print_HTTP_RESPONSE( res, printContent = False ):
    '''
    Debug HTTP response
    '''
    return '{}\n{},\n\n{}\n\n{}\n\n{}'.format(
        '---------START RESPONSE--------',
        str(res.status_code) + ' ' + res.reason + ' ' + res.request.url,
        res.content if printContent else '',
        res.headers,
        '---------STOP RESPONSE--------'
    )

def _verbose( show = False, msg = '', end = '\n' ):
    '''Show verbose message'''
    if show:
        print( msg, end = end )

def _debug( show = False, msg = '', end = '\n' ):
    '''Show debug message'''
    if show:
        print( msg, end = end )

def getVideoID( youtubeURL, verbose = False ):
    '''
    Parse the video ID from youtube url.
    
    Note: Time '[?t|&t]=' param is avoided.
    Formats admited:
    - https://www.youtube.com/watch?v=VIDEO-ID
    - https://yutu.be/VIDEO-ID
    
    Params:
    - v: Verbose. Show info about process status.
    '''
    _verbose( verbose, 'Status: Decoding video ID...', end = '' )
    parse = requests.utils.urlparse( youtubeURL )

    # CHECK SHORT VERSION & GET VIDEO ID
    # -------------------------------------------------------------------------
    if parse.netloc == 'youtu.be':
        vID = parse.path[1:]
    else:
        vID = list( filter( lambda e: 'v=' in e,  parse.query.split( '&' ) ) )[0].replace( 'v=', '' )
    # -------------------------------------------------------------------------
    
    _verbose( verbose, '[OK]' )
    return vID

def getOptions( vID, verbose = False, debug = False ):
    '''
    Get available options from API.
    - vID: Youtube video ID.
    - s:   Requests session object.
    - v:   Show info about process status.
    - d:   Show debug info about HTTP requests.
    '''

    optionsURL = 'https://www.y2mate.com/mates/es19/analyze/ajax'
    data = {
        'url':    'https://youtube.com/watch?v=' + vID,
        'q_auto': 0,
        'ajax':   1
    }
    headers = {
        'authority':    'www.2mate.com',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'method':       'POST',
        'path':         '/mates/es19/analyze/ajax',
        'referer':      'https://www.y2mate.com/es/youtube/' + vID,
        'scheme':       'https',
        'user-agent':   'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
    }
    req = requests.Request( 'POST', optionsURL, headers = headers, data = data )
    prepared = req.prepare()
    
    _debug( debug, print_HTTP( prepared ) )
    _verbose( verbose, 'Status: Getting download available options...', end='' )

    s = requests.Session()
    res = s.send( prepared, verify=True ) 

    if res.status_code == 200:
        # GET AVAILABLE OPTIONS
        if res.headers['Content-Type'] == 'application/json':
            parser = AdvancedHTMLParser.AdvancedHTMLParser()
            parser.parseStr( res.json()['result'] )
            
            # GET SCRIPT CONTENT
            kID = res.json()['result'].split('k__id = "')[1].split('"')[0]

            # GET VIDEO TITLE
            title = parser.getElementsByClassName('caption')[0].children[0].innerText
            
            # GET OPTIONS
            options = {}
            options['mp4'] = parseOptions( parser.getElementById('mp4') )
            options['mp3'] = parseOptions( parser.getElementById('mp3') )

            _verbose( verbose, '[OK]' )
            return { 'kID': kID, 'options': options, 'title': title }
        else:
            _verbose( verbose, '[Error]' )
            return None
    else:
        return None

def parseOptions( tab ):
    '''
    Process tab options table on result HTML when
    user paste video on download textbox at y2mate.com
    '''
    # PARSE MP4 DATA
    mp4Parser = AdvancedHTMLParser.AdvancedHTMLParser()
    mp4Parser.parseStr( tab[0].innerHTML )
    
    # PREPARE FOR SAVE MP4 DATA
    optionSample = { 'quality': None, 'size': None, 'type': None }
    options = []
    
    # PROCESS DATA
    for tr in mp4Parser.getElementsByTagName('tr')[1:-1]:
        trParser = AdvancedHTMLParser.AdvancedHTMLParser()
        trParser.parseStr( tr.innerHTML )
        tdList = trParser.getElementsByTagName('td')
        
        # FILL OPTION DATA
        option = copy.deepcopy( optionSample )
        option['size']    = tdList[1].innerText
        option['type']    = tdList[2].getChildren()[0].getAttribute('data-ftype')
        option['quality'] = tdList[2].getChildren()[0].getAttribute('data-fquality')
        
        option['quality'] = int( option['quality'].replace('p', '') )
        options.append( option )

    return options

def selectQuality( options, format, quality ):
    '''
    Select quality according given parameters.
    
    When format is not available the program exit.
    If quality is None, then max value is returned. Otherwise is the closest one.
    '''
    if format not in options:
        exit( '[Error]: Format specified not available!' )
    else:
        option = options[format]
        qualities = [ e['quality'] for e in option ]
        qualities.sort()

        # IF QUALITY IS NONE SELECT MAX QUALITY
        if quality == None:
            quality = max( qualities )
        
        # GET CLOSEST QUALITY FROM AVAILABLE
        else:
            quality = min( qualities, key = lambda x:abs( x - quality ) )
        
        return quality

def downloadFile( kID, vID, fileName = '', format = None, quality = None, debug = False, verbose = False):
    '''
    Download a file from youtube with y2mate.com API
    Parameters:
    - kID:      Security ID generated by y2mate on their JavaScript Code.
    - vID:      Youtube video ID
    - fileName: FileName name
    - format:   Selected format with -f
    - quality:  Selected quality with -q
    - debug:    Show debug info
    - verbose:  Show status info
    '''

    if fileName == '':
        return None

    if format == None or quality == None:
        return None
    
    # GET DOWNLOAD LINK
    ###########################################################################
    getLinkURL = 'https://www.y2mate.com/mates/es/convert'
    data = {
        'type':     'youtube',
        '_id':      kID,
        'v_id':     vID,
        'ajax':     1,
        'token':    '',
        'ftype':    format,
        'fquality': quality
    }
    
    headers = {
        'authority':      'www.y2mate.com',
        'method':         'POST',
        'path':           'mates/es/convert',
        'scheme':         'https',
        'content-type':   'application/x-www-form-urlencoded; charset=UTF-8',
        'origin':         'https://wwwy2mate.com',
        'pragma':         'no-cache',
        'referer':        'https://y2mate.com/es/youtube/' + vID,
        'user-agent':     'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'x-request-with': 'XMLHttpRequest'
    } 
    
    req = requests.Request( 'POST', getLinkURL, headers = headers, data = data )
    prepared = req.prepare()

    _debug( debug, print_HTTP( prepared ) )
    _verbose( verbose, 'Status: Getting file download link...', end = '' ) 

    s = requests.Session()
    res = s.send( prepared, verify=True )
    
    if res.status_code == 200:
        parser = AdvancedHTMLParser.AdvancedHTMLParser()
        parser.parseStr( res.json()['result'] )

        # GET DOWNLOAD LINK
        fileLink = parser.getElementsByTagName('a')[0].href

        _verbose( verbose, '[OK]' )
        
        # DOWNLOAD FILE
        # ---------------------------------------------------------------------
        _verbose( verbose, 'Status: Downloading file...', end = '' )
        
        chunk = 1024
        filePath = r'./' + fileName

        res = requests.get( fileLink, stream = True )
        fileSize = int( res.headers.get( 'content-length', 0 ) )
        
        # SAVE FILE STREAM
        # ---------------------------------------------------------------------
        with open( filePath, 'wb' ) as f, tqdm(
            desc=fileName, total = fileSize, unit = 'iB', unit_scale = True, unit_divisor = chunk
        ) as bar:
            for data in res.iter_content( chunk_size = chunk ):
                size = f.write( data )
                bar.update( size )
        # ---------------------------------------------------------------------
       
        _verbose( verbose, '[OK]' )
        # ---------------------------------------------------------------------
    else:
        _verbose( verbose, '[error]' )

    ###########################################################################


# CLI ARGUMENTS
# ------------------------------------------------------------------------------------------------------------------------
ap = argparse.ArgumentParser( description = """Download Youtube video or audio""" )
ap.version = '0.0.1'
ap.add_argument( '-v', '--version', action = 'version', help = 'Show version of this program.' )
ap.add_argument( '-d', '--debug', action = 'store_true', dest = 'isDebug', help = 'Show debug info.'  )
ap.add_argument( '-ve', '--verbose', action = 'store_true', dest = 'isVerbose', help = 'Show process status and info.' )
ap.add_argument( '-f', '--format', action = 'store', dest = 'format', choices = [ 'mp3', 'mp4' ], \
    required = True, default = 'mp3', help = 'Specify output format.' )
ap.add_argument( '-q', '--quality', action = 'store', dest = 'quality', type = int, help = 'Specify output quality.' )
ap.add_argument( '-sio', '--show-info-only', action = 'store_true', dest = 'showInfoOnly', \
    help = 'Only get and show info about format and qualities availables.' )
ap.add_argument( 'url', nargs = '?', action = 'store' )
args = ap.parse_args()
# ------------------------------------------------------------------------------------------------------------------------

# IF SOME RESULTS GIVE NONE START AGAIN
while True:
    vID     = getVideoID( args.url, verbose = args.isVerbose )
    result  = getOptions( vID, debug = args.isDebug, verbose = args.isVerbose )

    if result == None:
        _verbose( args.isVerbose, 'Status: Error getting options... restarting process!' )
        continue
    
    # SHOW INFO ONLY
    # -------------------------------------------------------------------------
    if args.showInfoOnly:
        q_postFix = { 'mp3': 'kbps', 'mp4': 'p' }
        f_separator = { 'mp3': '   ', 'mp4': '\t   ' }

        for format in result['options'].keys():
            print('\n {}\n----------------------'.format( format.capitalize() ))
            print(' Quality | Size')

            for details in result['options'][format]:
                # FIX UNKNOWN SIZE
                if len( details['size'].split() ) == 1:
                    details['size'] = 'UNKNOWN'

                print(' {}{}{}'.format(
                    str(details['quality']).strip() + q_postFix[format],
                    f_separator[format],
                    details['size'].strip()
                ))
            print('----------------------')
    # -------------------------------------------------------------------------
               
    else:
        quality = selectQuality( result['options'], args.format, args.quality )
        fileName = '{}.{}'.format( result['title'], args.format )
        downloadFile( result['kID'], vID, fileName = fileName, format = args.format, quality = quality, debug = args.isDebug, verbose = args.isVerbose ) 
    break
