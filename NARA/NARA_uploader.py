#!/usr/bin/python
# -*- coding: utf-8  -*-
'''
Bot to upload NARA images to Commons.

The bot expects a directory containing the images on the commandline and a text file containing the mappings.

The bot uses http://toolserver.org/~slakr/archives.php to get the description
'''

import sys, os.path, hashlib, base64, glob, re, urllib, time, unicodedata
sys.path.append("/Users/Dominic/pywikipedia")
#import wikipedia, config, query, upload
import shutil, socket

########################################################
### start effbot code
### source: http://effbot.org/zone/re-sub.htm#unescape-html
########################################################
#import re, htmlentitydefs
import htmlentitydefs

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)
########################################################
### end effbot code
########################################################

def getRecords(textfile):
    result = {}
    f = open(textfile, "r")

    for line in f.readlines():
        (filename, sep, arc) = line.partition(u' ')
        result[filename] = int(arc.strip())

    return result


#def findDuplicateImages(filename, site = wikipedia.getSite(u'commons', u'commons')):
#    '''
#    Takes the photo, calculates the SHA1 hash and asks the mediawiki api for a list of duplicates.
#
#    TODO: Add exception handling, fix site thing
#    '''
#    f = open(filename, 'rb')
#
#    hashObject = hashlib.sha1()
#    hashObject.update(f.read(-1))
#    return site.getFilesFromAnHash(base64.b16encode(hashObject.digest()))

def getDescription(fileId):
    url = u'http://toolserver.org/~slakr/archives.php?archiveHint=%s' % (fileId,)


    textareaRe = re.compile('^<textarea rows="\d+" cols="\d+">(.+)</textarea>$', re.MULTILINE + re.DOTALL)

    gotInfo = False
    matches = None
    maxtries = 10
    tries = 0
    while(not gotInfo):
        try:
            if ( tries < maxtries ):
                tries = tries + 1
                archivesPage = urllib.urlopen(url)
                matches = textareaRe.search(archivesPage.read().decode('utf-8'))
                gotInfo = True
            else:
                break
        except IOError:
            print(u'Got an IOError, let\'s try again')
        except socket.timeout:
            print(u'Got a timeout, let\'s try again')

    if (matches and gotInfo):
        return unescape(matches.group(1))
    return u''

def getTitle(fileId, description):
    titleRe = re.compile('^\|Title=(.+)$', re.MULTILINE)
    titleMatch = titleRe.search(description)
    titleText = truncateWithEllipsis(titleMatch.group(1), 120, "...")

    title = u'%s - NARA - %s.tif' % (titleText, fileId)
    return cleanUpTitle(title)

def cleanUpTitle(title):
    '''
    Clean up the title of a potential mediawiki page. Otherwise the title of
    the page might not be allowed by the software.

    '''
    title = title.strip()
    title = re.sub(u"[<{\\[]", u"(", title)
    title = re.sub(u"[>}\\]]", u")", title)
    title = re.sub(u"[ _]?\\(!\\)", u"", title)
    title = re.sub(u",:[ _]", u", ", title)
    title = re.sub(u"[;:][ _]", u", ", title)
    title = re.sub(u"[\t\n ]+", u" ", title)
    title = re.sub(u"[\r\n ]+", u" ", title)
    title = re.sub(u"[\n]+", u"", title)
    title = re.sub(u"[?!]([.\"]|$)", u"\\1", title)
    title = re.sub(u"[#%?!]", u"^", title)
    title = re.sub(u"[;]", u",", title)
    title = re.sub(u"[/+\\\\:]", u"-", title)
    title = re.sub(u"--+", u"-", title)
    title = re.sub(u",,+", u",", title)
    title = re.sub(u"[-,^]([.]|$)", u"\\1", title)
    title = title.replace(u" ", u"_")
    return title

def truncateWithEllipsis(s, limit, ellipsis=u"\u2026"):
    if len(s) > limit:
        for i in range(limit, 0, -1):
            if (unicodedata.category(s[i]) == 'Zs'
                and i + len(ellipsis) <= limit):
                return s[:i] + ellipsis
        return s[:-len(ellipsis)] + ellipsis
    else:
        return s

def main(args):
    '''
    Main loop.
    '''
    workdir = u''
    textfile = u''
    records = {}
    
    #site = wikipedia.getSite(u'commons', u'commons')
    #wikipedia.setSite(site)

    if not (len(args)==2):
        print(u'Too few arguments. Usage: NARA_uploader.py <directory> <textfile>')
        sys.exit()
    
    if os.path.isdir(args[0]):
        workdir = args[0]
    else:
        print(u'%s doesn\'t appear to be a directory. Exiting' % (args[0],))
        sys.exit()
        
    textfile = args[1]
    #records = getRecords(textfile)
    records = {"19-1065M.TIF": 534596}
    #print records

    sourcefilenames = glob.glob(workdir + u"/*.TIF")
    print(u'sourcefilenames: %r' % sourcefilenames )

    for sourcefilename in sourcefilenames:
        filename = os.path.basename(sourcefilename)
        # This will give an ugly error if the id is unknown

        print(u'filename: %r' % filename )
        if not records.get(filename):
             print(u'Can\'t find %s in %s. Skipping this file.' % (filename, textfile))
        elif os.path.getsize(sourcefilename) >= 1024 * 1024 * 100:
             print(u'%s too big. Skipping this file.' % (sourcefilename,))
        else:
            fileId = records.get(filename)
        
            #duplicates = findDuplicateImages(sourcefilename)
            duplicates = None
            if duplicates:
                print(u'Found duplicate image at %s' % duplicates.pop())
            else:
                # No metadata handling. We use a webtool
                description = getDescription(fileId)
                categories = u'{{Uncategorized-NARA|year=2011|month=September|day=21}}\n'
                description = description + categories

                print fileId
                print(u'fileId: %r' % fileId )
                title = getTitle(fileId, description)

                print(title)
                print(u'title: %r' % title )
                print(description)
                print(u'description: %r' % description )

                print(u'upload.UploadRobot args: %r' % {'url':sourcefilename.decode(sys.getfilesystemencoding()), 'description':description, 'useFilename':title, 'keepFilename':True, 'verifyDescription':False})
                print(u'This was a test of the [[Emergency Alert System]]. Bailing.')
                sys.exit(0)

                #bot = upload.UploadRobot(url=sourcefilename.decode(sys.getfilesystemencoding()), description=description, useFilename=title, keepFilename=True, verifyDescription=False)
                #bot.run()
 
if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    finally:
        print u'All done'
