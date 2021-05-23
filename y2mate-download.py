#!/usr/bin/python3.8
# -*- coding: utf-8 -*-

import AdvancedHTMLParser
import argparse
import copy
import requests
from os import getenv, path, remove
from tqdm import tqdm
from sys import argv, version_info

# AUTHOR AND PROJECT INFO
# ----------------------------------------------------
__project = {
    'title':        'Y2mate Downloader',
    'version':      'v-dev-0.0.4',
    'pyMinVersion': 3.8
}
__author = {
    'name':  'Francisca Cañellas',
    'alias': 'Franny',
    'email': 'francisca.leonor.alejandra.c@gmail.com'
}
# ----------------------------------------------------

def checkVersion( interrupt = False, verbose = False ):
    '''
    Check min python required version or exit
    '''
    v = float(
        '{}.{}{}'.format(
            str(version_info.major),
            str(version_info.minor),
            str(version_info.micro)
        )
    )

    if  v < __project['pyMinVersion']:
        outMsg = 'Python {} or above is required!'.format(
            __project['pyMinVersion']
        )
        _verbose( verbose, outMsg )
        
        # INTERRUPT OR RETURN ERROR MSG
        if interrupt:
            return { 'status': False, 'msg': outMsg }
        else:
            exit( outMsg )
    # NO ERROR REPORTED
    else:
        return { 'status': True }

def printHTTP( req ):
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

def printHTTPResponse( res, printContent = False ):
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

def getAudioFolderPath():
    '''
    Get audio folder path from Y2MATE_AUDIO_FOLDER
    enviroment variable.
    '''
    return getenv( 'Y2MATE_AUDIO_FOLDER', '' )

def getVideoFolderPath():
    '''
    Get video folder path from Y2MATE_VIDEO_FOLDER
    enviroment variable.
    '''
    return getenv( 'Y2MATE_VIDEO_FOLDER', './' )

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
        vID = list(
            filter(
                lambda e: 'v=' in e,
                parse.query.split( '&' )
            )
        )[0].replace( 'v=', '')
    # -------------------------------------------------------------------------
    
    _verbose( verbose, '[OK]' )
    return vID

def getOptions( vID, verbose = False, debug = False, mp3Convert = False ):
    '''
    Get available options from API.
    - vID:        Youtube video ID.
    - verbose:    Show info about process status.
    - debug:      Show debug info about HTTP requests.
    - mp3Convert: Get Options from Y2mate Youtube MP3 Converter
    '''
    
    if mp3Convert:
        optionsURL = 'https://www.y2mate.com/mates/en31/mp3/ajax'
    else:
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
        'user-agent':   'Mozilla/5.0 (X11; Linux x86_64)' \
            + 'AppleWebKit/537.36 (KHTML, like Gecko)' \
            + 'Chrome/90.0.4430.93 Safari/537.36'
    }

    if mp3Convert:
        headers['path'] = '/mates/en31/mp3/ajax'

    req = requests.Request( 'POST', optionsURL, headers = headers, data = data )
    prepared = req.prepare()
    
    _debug( debug, printHTTP( prepared ) )
    _verbose( verbose, 'Status: Getting download available options...', end='' )

    s = requests.Session()
    res = s.send( prepared, verify=True ) 

    if res.status_code == 200:
        # GET AVAILABLE OPTIONS
        if res.headers['Content-Type'] == 'application/json':
            parser = AdvancedHTMLParser.AdvancedHTMLParser()
            parser.parseStr( res.json()['result'] )
            
            # GET KID FROM SCRIPT CONTENT
            kID = res.json()['result'].split('k__id = "')[1].split('"')[0]
            
            # GET VIDEO TITLE
            title = parser.getElementsByClassName('caption')[0] \
                .children[0] \
                .innerText

            if mp3Convert:
                data = parseYoutubeMp3ConverterOptions( parser, verbose )
            else:
                data = parseYoutubeDownloaderOptions( parser, verbose )

            data['kID']   = kID
            data['title'] = title
            return data
        else:
            _verbose( verbose, '[Error]' )
            return None

    else:
        return None

def parseYoutubeMp3ConverterOptions( parser, verbose ):
    '''
    Parse data from Y2mate Youtube MP3 Converter
    '''

    ul = parser.getElementsByTagName('ul')[0]
    options = {}
    options['mp3'] = [
        int(
            li.children[0].getAttribute('onclick') \
                .replace( 'changeMp3Type(', '' ) \
                .split( ',' )[0]
        )
        for li in ul.children
    ]
    options['mp3'].sort()
    
    # ADD EXTRA DATA
    options['mp3'] = [
        { 'quality': o, 'size': '? MB', 'type': 'mp3' }
        for o in  options['mp3']
    ]
    return { 'options': options }

def parseYoutubeDownloaderOptions( parser, verbose ):
    '''
    Parse data from Y2mate Youtube Downloader
    ''' 
    
    # GET OPTIONS
    options = {}
    options['mp4'] = parseOptions( parser.getElementById('mp4') )
    options['mp3'] = parseOptions( parser.getElementById('mp3') )
    options['m4a'] = parseOptions( parser.getElementById('audio') )
    
    # FILTER AUDIO MP3 ITEMS (THERE PROBABLY REPEATED)
    options['m4a'] = list(
        filter(
            (lambda e: e['type'] != 'mp3'),
            options['m4a']
        )
    )

    _verbose( verbose, '[OK]' )
    return { 'options': options }
    
def parseOptions( tab ):
    '''
    Process tab options table on result HTML when
    user paste video on download textbox at y2mate.com
    '''
    # PARSE DATA
    parser = AdvancedHTMLParser.AdvancedHTMLParser()
    parser.parseStr( tab[0].innerHTML )
    
    # PREPARE FOR SAVE DATA
    optionSample = { 'quality': None, 'size': None, 'type': None }
    options = []
    
    # PROCESS DATA
    for tr in parser.getElementsByTagName('tr')[1:-1]:
        trParser = AdvancedHTMLParser.AdvancedHTMLParser()
        trParser.parseStr( tr.innerHTML )

        tdList = trParser.getElementsByTagName('td')

        # FILL OPTION DATA
        option = copy.deepcopy( optionSample )
        option['size']    = tdList[1].innerText
        # WHEN AUDIO TAB IS PROCESSED THERE IS BUTTON BEFORE A ELEMENT
        # ------------------------------------------------------------
        if len( tdList[2].getChildren() ) == 2:
            index = 1
        else:
            index = 0
        # ------------------------------------------------------------       
        option['type']    = tdList[2].getChildren()[index] \
            .getAttribute('data-ftype')

        option['quality'] = tdList[2].getChildren()[index] \
            .getAttribute('data-fquality')

        option['quality'] = int( option['quality'].replace('p', '') )
        options.append( option )

    return options

def selectQuality( options, format, quality ):
    '''
    Select quality according given parameters.
    
    When format is not available the program exit.
    If quality is None, then max value is returned.
    Otherwise is the closest one.
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

def downloadFile(
        kID, vID, mp3Convert = False, useCurrentDir = False, fileName = '',
        format = None, quality = None, debug = False, verbose = False
    ):
    '''
    Download a file from youtube with y2mate.com API
    Parameters:
    - kID:           Security ID generated by y2mate on their JavaScript Code.
    - vID:           Youtube video ID
    - useCurrentDir: Let you download files on current directory
    - fileName:      FileName name
    - format:        Selected format with -f
    - quality:       Selected quality with -q
    - debug:         Show debug info
    - verbose:       Show status info
    '''

    if fileName == '':
        return None

    if format == None or quality == None:
        return None

    # GET DOWNLOAD LINK
    ###########################################################################
    if mp3Convert:
        print( 'This may take a while, please be patient!\n' )

        getLinkURL = 'https://www.y2mate.com/mates/mp3Convert'
    else:
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
        'path':           getLinkURL.split('.com')[1],
        'scheme':         'https',
        'content-type':   'application/x-www-form-urlencoded; charset=UTF-8',
        'origin':         'https://wwwy2mate.com',
        'pragma':         'no-cache',
        'referer':        'https://y2mate.com/es/youtube/' + vID,
        'user-agent':     'Mozilla/5.0 (X11; Linux x86_64) ' \
            + ' AppleWebKit/537.36 ' \
            + '(KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'x-request-with': 'XMLHttpRequest'
    } 

    req = requests.Request( 'POST', getLinkURL, headers = headers, data = data )
    prepared = req.prepare()

    _debug( debug, printHTTP( prepared ) )
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
        
        # SET FILE PATH TO CURRENT DIRECTORY
        if useCurrentDir:
            filePath = './' + fileName
        # CHOSE FILE PATH FROM ENVIROMENT VARIABLES
        else:
            # AUDIO FILES
            if format in [ 'mp3', 'm4a' ]:
                saveDir = getAudioFolderPath()
            # VIDEO FILES
            else:
                saveDir = getVideoFolderPath()
            filePath = saveDir + fileName

        chunk = 1024 

        res = requests.get( fileLink, stream = True )
        
        # FILE NOT FOUND. SERVER ERROR
        if res.status_code == 404:
            _verbose( verbose, '[ERROR]')
            exit( '[Server Error]: File not found!' )
        
        # ASK FOR FILE OVERWRITE
        # ---------------------------------------------------------------------
        if path.exists( filePath ) and path.isfile( filePath ):
            while True:
                answer =  input(
                    'File \'{}\' already exists, overwride? [y/n]: '.format( filePath )
                ).lower()
                
                if not answer in [ 'y', 'n' ]:
                    continue
                else:
                    break

            if answer == 'y':
                remove( filePath )
                print( 'File \'{}\' deleted!'.format( filePath ) )
            # CHANGE FILE NAME FOR NOT OVERWRITE
            else:
                _fileName = fileName
                _path = filePath.split('/') 
                filePath = '/'.join( _path[:-1] ) + '/2_' + _path[-1] 
                fileName = '2_' + fileName
                print( 'File \'{}\' renamed to \'{}\''.format( _fileName, fileName ) )
        # ---------------------------------------------------------------------

        # SAVE FILE STREAM
        # ---------------------------------------------------------------------
        fileSize = int( res.headers.get( 'content-length', 0 ) )
        with open( filePath, 'wb' ) as f, tqdm(
            desc=fileName, total = fileSize, unit = 'iB', unit_scale = True,
            unit_divisor = chunk
        ) as bar:
            for data in res.iter_content( chunk_size = chunk ):
                size = f.write( data )
                bar.update( size )
        
        print('Saved at \'{}\'...'.format( filePath ))
        # ---------------------------------------------------------------------
       
        _verbose( verbose, '[OK]' )
        # ---------------------------------------------------------------------
    else:
        _verbose( verbose, '[error]' )

    ###########################################################################

def getProjectInfo( indentChar = ' ' ):
    '''
    Get Project info in string
    '''
    return  (
        '\n{i}{_1}\n{i}{title} {version}\n' \
        + '{i}{_2}\n{i}by {name} ({email})\n{i}{_3}\n'
    ).format(
            _1 = '-' * 29,
            title = __project['title'],
            version = __project['version'],
            _2 = '-' * 62,
            name = __author['name'],
            email = __author['email'],
            _3 = '-' * 62,
            i = indentChar
    )


# CLI PARAMETERS
# ------------------------------------------------------------------------------
ap = argparse.ArgumentParser(
    add_help = False,
    description = 'Download or Convert to MP3 a Youtube Video'
)
ap.version = '0.0.1'
# VERSION
# ==============================================================================
ap.add_argument( '-v', '--version', action = 'version', \
    help = 'Show version of this program.' )
# ==============================================================================

# DEBUG
# ==============================================================================
ap.add_argument( '-d', '--debug', action = 'store_true', dest = 'isDebug', \
    help = 'Show debug info.'  )
# ==============================================================================

# VERBOSE
# ==============================================================================
ap.add_argument( '-ve', '--verbose', action = 'store_true', \
    dest = 'isVerbose', help = 'Show process status and info.' )
# ==============================================================================

# FORMAT
# ==============================================================================
formatExclusiveGroup = ap.add_mutually_exclusive_group( required = True )
formatExclusiveGroup.add_argument( '-f', '--format', action = 'store', dest = 'format', \
    choices = [ 'm4a', 'mp3', 'mp4' ], default = 'mp3', \
    help = 'Specify output format.' )
# ==============================================================================

# QUALITY
# ==============================================================================
ap.add_argument( '-q', '--quality', action = 'store', dest = 'quality', \
    type = int, help = 'Specify output quality.' )
# ==============================================================================
# SHOW INFO ONLY
# ==============================================================================
ap.add_argument( '-sio', action = 'store_true', dest = 'showInfoOnly', \
    help = 'Only get and show info about format and qualities availables.' )
# ==============================================================================

# SHOW FORMAT ONLY
# ==============================================================================
ap.add_argument( '-sfo', action = 'store_true', dest = 'showFormatOnly', \
    help = 'Show specified format info Only.')
# ==============================================================================

# DOWNLOAD FILES ON CURRENT DIR
# ==============================================================================
ap.add_argument( '-cd', action = 'store_true', dest = 'useCurrentDir', \
    help = 'Download files on current dir.' )
# ==============================================================================

# MP3 CONVERT
# ==============================================================================
ap.add_argument( '--mp3-convert', action = 'store_true', dest = 'mp3Convert', \
    help = 'Use Y2mate\'s youtube MP3 converter service' )
# ==============================================================================

# OVERRIDE HELP COMMAND
# ==============================================================================
formatExclusiveGroup.add_argument( '-h', '--help', action = 'store_true', dest = 'showHelp', \
    help = 'Show this help message and exit.')
# ==============================================================================

# URL (POSITIONAL ARGUMENT)
# ==============================================================================
ap.add_argument( 'url', nargs = '?', action = 'store' )
# ==============================================================================

# CHECK VERSION
# ==============================================================================
result = checkVersion( interrupt = True )

if not result['status']:
    exit( result['msg'] )
# ==============================================================================

args = ap.parse_args()
# ------------------------------------------------------------------------------

# IF SOME RESULTS GIVE NONE START AGAIN
while True:
    try:
        # CHECK HELP
        if args.showHelp:
            print( getProjectInfo( indentChar = '' )[1:] )
            ap.print_help() 
            exit()

        # CHECK MP3 CONVERT AND FORMAT OPTION
        if args.format != 'mp3' and args.mp3Convert:
            _verbose( args.isVerbose, 'Status: CLI wrong parameters!' )
            exit( 'You must specified \'-f mp3\' to use \'--mp3-convert\' option!' )
        
        # CHECK FOR EMPTY VIDEO URL
        if args.url == None or args.url == '':
            _verbose( args.isVerbose, 'Status: You must give me a video url!' )
            exit( 'You must give me a video url!' )

        vID     = getVideoID( args.url, verbose = args.isVerbose )
        result  = getOptions(
            vID, debug = args.isDebug, verbose = args.isVerbose,
            mp3Convert = args.mp3Convert
        )

        if result == None:
            _verbose(
                    args.isVerbose,
                    'Status: Error getting options... restarting process!'
            )
            continue
        
        # SHOW INFO ONLY
        # ----------------------------------------------------------------------
        if args.showInfoOnly:
            q_postFix = { 'audio': 'kbps', 'mp4': 'p' }
            f_separator = { 'audio': '   ', 'mp4': '\t   ' }

            # SHOW FORMAT ONLY
            # ------------------------------------
            if args.showFormatOnly:
                formats = [ args.format ]
            else:
                formats = result['options'].keys()
            # ------------------------------------
            
            output = getProjectInfo()                

            # SET Y2MATE SERVICE TITLE
            # ----------------------------------------------
            output += '\n Service: '
            if args.mp3Convert:
                output += 'Y2mate Youtube MP3 Converter\n'
            else:
                output += 'Y2mate Youtube Downloader\n'
            # ----------------------------------------------
            
            # PROCESS FORMATS
            output += '\n Available options:\n'

            for format in formats:
                # CONVERT FORMAT TO SET KEY ACCESIBLE
                # ------------------------------------
                if format in [ 'audio', 'mp3' ]:
                    set_k = 'audio'
                else:
                    set_k = 'mp4'
                # ------------------------------------

                output += '\n {}\n {}'.format(
                    format.capitalize(),
                    '-' * 22
                )
                output += '\n Quality | Size'

                for details in result['options'][format]:
                    # FIX UNKNOWN SIZE
                    # -------------------------------------
                    if len( details['size'].split() ) == 1:
                        continue
                    # -------------------------------------

                    output += '\n {}{}{}'.format(
                        str(details['quality']).strip() + q_postFix[set_k],
                        f_separator[set_k],
                        details['size'].strip()
                    )
                output += '\n {}\n'.format( '-' * 22 )
            print( output )
        # ----------------------------------------------------------------------
                   
        else:
            quality = selectQuality(
                result['options'],
                args.format,
                args.quality
            )
            fileName = '{}.{}'.format( result['title'], args.format )

            downloadFile(
                result['kID'],
                vID,
                useCurrentDir = args.useCurrentDir,
                mp3Convert    = args.mp3Convert,
                fileName      = fileName,
                format        = args.format,
                quality       = quality,
                debug         = args.isDebug,
                verbose       = args.isVerbose
            ) 
    except KeyboardInterrupt:
        _verbose( args.isVerbose, 'Status: Task cancelled by user!' )
        exit( '\nCacelled by user!' )

    break
