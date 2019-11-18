#!/usr/bin/python
""" License:
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the University of North Carolina nor the names of
      its contributors may be used to endorse or promote products derived
      from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE."""

"""Script to extract CSW records from a CSW
Author: Thijs Brentjens (thijs@brentjensgeoict.nl) for Geonovum
"""
import sys
import ConfigParser
import os
import glob
import fileinput
import csv
import urllib2
import logging
import re
import time
import traceback
import requests
import cookielib

from datetime import date, datetime

from owslib.csw import CatalogueServiceWeb
from owslib.iso import *
from owslib.etree import etree

import StringIO

# -----------------
# Read config
# TODO: describe the config setup
# -----------------
config = ConfigParser.ConfigParser()
# /apps/metadatakwaliteit/git/metadatakwaliteit/src/python/config/
configdir = '/apps/metadatakwaliteit/git/metadatakwaliteit/src/python/config/'
config.read(configdir + 'config.cfg')

# the first argument is the CSW URL. If this is not present, then use the
# preconfigured URL.
if len(sys.argv) > 1:
    cswUrl = sys.argv[1]
else:
    cswUrl = config.get('CSW', 'baseUrl')
print cswUrl

maxRecords = config.getint('CSW', 'maxRecords')
totalMaxRecords = config.getint('CSW', 'totalMaxRecords')
#waitForRetry = config.getint('CSW', 'waitForRetry')
#nrRetry = config.getint('CSW', 'nrRetry')

# used to seperate values in CSV-cells
valuesep = config.get('DEFAULT', 'valueseparator')

# fetch entire CSW records, so use full
esn = "full"

# -----------------
# INIT output
# -----------------

outputdir = config.get('RESULTFILES', 'outputdir')

# TIMESTAMP
now = datetime.now()
strNow = now.strftime("%Y-%m-%d_%H%M%S")

# -----------------
# INIT error logging
# -----------------
errorfilename = outputdir + strNow + \
    config.get('RESULTFILES', 'errorlog') + '.log'
logging.basicConfig(filename=errorfilename, level=logging.ERROR)


successFullProcessed = 0
cswErrors = ""

# Util
# TODO: refactor, separate class?
# Read in a file as CSV, return array
# return an empty array if not found


def readConfigCSVFile(filename):
    csvValues = []
    try:
        csvfile = open(filename, "r")
        csvValues = list(csv.reader(csvfile))
        return csvValues
    except Exception:
        logging.error('Error loading file: ' + filename)

# change the unicode encoding
# results contain first two columns for identifier and organisationname, then per tested value 3 (!) columns: 1 the value, 2 the score, 3 the result
# if the passed in value does not contain properties, then assume a simple value, else use the score and the result
# Fixed issue #11: add calculating totals


def encodevalues(array, addtotals):
    newarray = []
    totalscore = 0
    for i, val in enumerate(array):
        testvalue = ''
        testscore = 0
        testresult = 0
        if val:
            # If the val is a MkmScore object, we can use the value, score and weight
            # if type(val) is str:
            if isinstance(val, MkmScore):
                try:
                    # we have a MkmScore, so use the score and calculate the
                    # result
                    testvalue = val.value
                    testscore = val.score
                    testresult = val.result
                    totalscore = totalscore + val.result
                except Exception as e:
                    logging.info(str(e))
            else:
                testvalue = val
                testscore = 2
                testresult = 1
        # inidices 0 - 3 are for fileidentifier, organisation, wijzigingsdatum, mdprofiel
        # then testvalue, score and result
        if i < 4:
            newarray.append(unicode(testvalue).encode('utf-8', 'ignore'))
        else:
            newarray.append(unicode(testvalue).encode('utf-8', 'ignore'))
            newarray.append(testscore)
            newarray.append(testresult)
    # now add totals, if required
    if addtotals:
        newarray.append(totalscore)
    return newarray

# an object to hold scores

class MkmScore:
    def __init__(self, value, score, result):
        self.value = value
        self.score = score
        self.result = result

    def recalculate(self):
        return false

# -----------------
# Metadata codelists
# ----------------
# for codelists, read CSV files

# ServiceTypes
# ------------
codelistServiceTypes = readConfigCSVFile(
    configdir + config.get('CODELISTS', 'codelistServices'))
logging.debug(codelistServiceTypes)

# Spatial Data ServiceTypes (for 19119 , INSPIRE)
# ------------
codelistSpatialDataServiceTypes = readConfigCSVFile(
    configdir + config.get('CODELISTS', 'codelistSpatialDataServiceTypes'))
logging.debug(codelistSpatialDataServiceTypes)

# Limitations
# ------------
codelistLimitations = readConfigCSVFile(
    configdir + config.get('CODELISTS', 'codelistLimitations'))
logging.debug(codelistLimitations)

# GMX codes
# ------------
codelistgmx = etree.parse(configdir + config.get('CODELISTS', 'codelistgmx'))
c = CodelistCatalogue(codelistgmx)
# for testing the codes
# print c.getcodelistdictionaries()
# example to get codes
# print c.getcodedefinitionidentifiers('CI_RoleCode')

# -----------------
# Read weightmatrices
# ----------------
weightsdatasets = readConfigCSVFile(
    configdir + config.get('SCORING', 'weightsdatasets'))
# create checks with scores from the file
# An array is fine to use
checksdatasets = []
for i, row in enumerate(weightsdatasets):
    if i > 0:
        # the first col is the checkid, that is the identifier for checks matrix?
        # NOTE: order of the points is inverted, to allow for 0=bad, 1=medium,
        # 2=good
        points = [int(row[4]), int(row[3]), int(row[2])]
        checksdatasets.append([int(row[0]), row[1], points])
logging.debug(checksdatasets)

# create checks with scores from the file
# An array is fine to use
weightsservices = readConfigCSVFile(
    configdir + config.get('SCORING', 'weightsservices'))
checksservices = []
for i, row in enumerate(weightsservices):
    if i > 0:
        # the first col is the checkid, that is the identifier for checks matrix?
        # NOTE: order of the points from the CSV is inverted, to allow for
        # using scores: 0=bad, 1=medium, 2=good
        points = [int(row[4]), int(row[3]), int(row[2])]
        checksservices.append([int(row[0]), row[1], points])
logging.debug(checksservices)

# -----------------
# for services, use another timeout than for CSW
# -----------------
timeoutsecs = config.getint('DEFAULT', 'timeoutsecs')


# -----------------
# Fetching CSW records
# ----------------
cswtimeoutsecs = config.getint('DEFAULT', 'cswtimeoutsecs')
csw = CatalogueServiceWeb(cswUrl, timeout=cswtimeoutsecs)

allfileidentifiers = []
allbronidentifiers = []
allemail = []
# titles should be unique per organisation
# TODO: implement this (issue #9)
alltitles = []


def getRecs(maxRecords, start, mdtype, csvfilename, cswErrors, successFullProcessed, fileIdentifierList, cookieJar):
    # DOC: Only get ISO records, so set the outputSchema
    outputschema = 'http://www.isotc211.org/2005/gmd'
    # On timeouts, do a retry of the same request once. Issue #4
    # The error is reported and after 3 attempts, the process breaks.
    attempts = 0
    maxAttempts = 3
    while attempts < maxAttempts and attempts >= 0:  # TODO: make configurable CSW attempts
        try:
            timestamp = datetime.now()
            logging.debug('Time of request: ' + timestamp.strftime("%Y-%m-%d %H:%M:%S") + '. Metadata type: ' + str(
                mdtype) + ', outputschema: ' + outputschema + ', maxRecords: ' + str(maxRecords) + ', start: ' + str(start))
            if not fileIdentifierList:
                if not mdtype:
                    csw.getrecords(None, outputschema=outputschema,
                                   maxrecords=maxRecords, startposition=start, esn=esn)
                else:
                    # sortBy="fileIdentifier:A"
                    # discoveryQuery = PropertyIsEqualTo('csw:ServiceType', 'discovery')
                    # Example: filter on a property. Current OWSLib version has
                    # limited filter capabilities
                    csw.getrecords(qtype=mdtype, outputschema=outputschema,
                                   maxrecords=maxRecords, startposition=start, esn=esn)
                # There is no need to continue, since fetching seems to be done
                # okay
            else:
                # csw.getrecordbyid(id=fileIdentifierList, outputschema=outputschema, esn='full', cookies=cookieJar)
                # TODO: is it okay to disable cookies now? This gives
                # errors. But OWSLib has some improvements in handling cookies?
                csw.getrecordbyid(id=fileIdentifierList,
                                  outputschema=outputschema, esn='full')
            attempts = -1
        except Exception as e:
            attempts += 1
            traceback.print_exc()
            logging.error('Error getting CSW Records. Retrying after ' + str(
                cswtimeoutsecs) + ' seconds. Number of attempts done: ' + str(attempts))
            logging.debug('Message: ' + str(e))
            if mdtype:
                cswErrors += mdtype + ":\n"
            if fileIdentifierList:
                cswErrors += "ERROR getting record with id: " + \
                    str(fileIdentifierList) + " \n"
                logging.debug('ERROR with fileIdentifier: ' +
                              str(fileIdentifierList))
            else:
                cswErrors += "ERROR getting " + \
                    str(maxRecords) + " records from startposition: " + \
                    str(start) + " \n"
            logging.error("--------------------------------------------------------")
            time.sleep(cswtimeoutsecs)
        # wait a while, to avoid too much calls to NGR
        time.sleep(0.3)
    # Remove all files?
    if attempts == maxAttempts:
        strmdtype = ' '
        if mdtype != None:
            strmdtype = 'for ' + str(mdtype) + ' '
        attempterror = 'Severe error: CSW Records ' + strmdtype + \
            'cannot be fetched. Number of records: ' + \
            str(maxRecords) + ', starting at index: ' + str(start)
        logging.error(attempterror)
        logging.error("--------------------------------------------------------")
        writeSummary(cswErrors)
        logging.error("--------------------------------------------------------")
        raise Exception(attempterror, attempterror)
    csvfile = open(csvfilename, 'a')
    csvwriter = csv.writer(csvfile, delimiter=',',
                           quotechar='"', quoting=csv.QUOTE_ALL)
    if len(csw.records) == 0:
        logging.error("--------------------")
        logging.error("No CSW response for fileIdentifier(s) : " +
                      ','.join(fileIdentifierList))
        logging.error("--------------------")
        cswErrors += "No CSW response for fileIdentifier(s) : " + ','.join(
            fileIdentifierList) + "\n"
        writeSummary(cswErrors)
        logging.error("--------------------------------------------------------")
    for rec in csw.records:
        try:
            # use OWSLib to read elements in python
            # First: all elements, for datasets/series
            fileidentifier = csw.records[rec].identifier
            if fileidentifier == None:
                fileidentifier == "no identifier found -- see errorlog"
            logging.debug(
                "\n------------------------------------------------------------")
            logging.debug(
                "Start processing record with fileidentifier: " + fileidentifier)
            wijzigingsdatum = csw.records[rec].datestamp
            mdprofiel = csw.records[rec].stdver
            # TODO: add a check for wijzigingsdatum after dec 2019 and mdprofiel version not for 2.0
            # ------------------
            # Metadata fileidentifier checks
            # ------------------
            fileidentifierscore = checkuuidfileidentifier(
                fileidentifier, mdtype)
            # ------------------
            # Juridische toegangs checks
            # ------------------
            #juridischetoegangsrestricties   = ""
            # if csw.records[rec].identification.accessconstraints:
            juridischetoegangsrestricties = checkjuridischetoegangsrestricties(
                csw.records[rec].identification.accessconstraints, mdtype)
            # ------------------
            # Juridische gebruiksrestricties checks
            # ------------------
            # if csw.records[rec].identification.useconstraints: # was
            # .classification
            if csw.records[rec].identification.useconstraints != None:
                useconstraints = csw.records[rec].identification.useconstraints
            else:
                useconstraints = None
            juridischegebruiksrestricties = checkjuridischegebruiksrestricties(
                useconstraints, mdtype)
            # ------------------
            # Overige beperingen checks
            # ------------------
            overigebeperkingenarr = csw.records[
                rec].identification.otherconstraints
            overigebeperkingen = checkoverigebeperkingen(
                overigebeperkingenarr, mdtype)
            # score for overigebeperkingen_beschrijving
            # overigebeperkingen_beschrijving_score = 0
            overigebeperkingen_url = overigebeperkingen[0]
            overigebeperkingen_beschrijving = overigebeperkingen[1]
            # Issue 4: fix the line seperators that GN adds sometimes for the title and abstract:
            # ---------
            # Title
            # ---------
            title = csw.records[rec].identification.title
            if title != None:
                title = title.replace("\n", " ")
            else:
                title = ""
            title = checktitle(title, mdtype)
            # ---------
            # Abstract
            # ---------
            abstracttxt = csw.records[rec].identification.abstract
            abstract = checkabstract(abstracttxt, mdtype)
            # ---------
            # Keywords
            # ---------
            keywordsarr = csw.records[rec].identification.keywords
            keywords = checkkeywords(keywordsarr, mdtype)
            # ---------
            # MD_Identifier, bron identifier
            # ---------
            if mdtype != 'service':
                uuidbrontxt = csw.records[rec].identification.md_identifier
                try:
                    uuidbron = checkuuidbron(
                        uuidbrontxt, fileidentifier, mdtype)
                except Exception as e:
                    logging.info(
                        'Error in uuidbron. See record with fileIdentifier: ' + fileidentifier)
                    logging.debug('Message: ' + str(e))
                    uuidbron = uuidbrontxt
            # ---------
            # Extent, boundingbox
            # ---------
            boundingboxelem = ""
            boundingbox = ""
            if csw.records[rec].identification.extent:
                try:
                    boundingboxelem = csw.records[
                        rec].identification.extent.boundingBox
                    boundingbox = checkbbox(boundingboxelem, mdtype)
                except Exception as e:
                    logging.info(
                        'Error in boundinbox extent. See record with fileIdentifier: ' + fileidentifier)
                    logging.debug('Message: ' + str(e))
                    # Reset the boundingbox values
                    boundingbox = ""
            online = ""
            contact = csw.records[rec].contact
            contactorg = ""
            # ------------------
            # email check
            # ------------------
            contactemail = ""
            if len(contact) > 0:
                try:
                    contactorg = csw.records[rec].contact[0].organization
                    contactemail = csw.records[rec].contact[0].email
                except Exception as e:
                    logging.info(
                        'Error in contact information. See record with fileIdentifier: ' + fileidentifier)
            if contactemail in allemail:
                logging.debug("Email address exists already")  # + contactemail
            else:
                try:
                    allemail.append(contactemail)
                    # or include the fileidentifier as well? Then we have a row
                    # per md record
                    emailwriter.writerow(encodevalues(
                        [contactorg, contactemail], addtotals=False))
                except Exception as e:
                    logging.info(
                        'Error in contact information email. See record with fileIdentifier: ' + fileidentifier)
            # Now calculate the email score
            try:
                contactemail = checkemail(contactemail, mdtype)
            except Exception as e:
                logging.info(
                    'Error in email address. See record with fileIdentifier: ' + fileidentifier)
            # see: https://github.com/geopython/OWSLib/blob/master/owslib/iso.py as well
            # ------------------
            # URLs checken
            # ------------------
            onlineresources = ""
            # urls consist of a url and protocol
            urls = ""
            urlstxt = ""
            protocols = ""
            protocolstxt = ""
            online = None
            if csw.records[rec].distribution:
                online = csw.records[rec].distribution.online
            # if len(online) > 0:
            onlineresources = checkonlineresources(online)
            cntr = len(onlineresources)
            for cntr, i in enumerate(onlineresources):
                try:
                    # do a basic check if the URL is resolvable
                    urlstxt += str(i[0]) + " (HTTP " + str(i[2]) + ")"
                    protocolstxt += str(i[1])
                    if cntr < len(onlineresources) - 1:
                        urlstxt += valuesep
                        protocolstxt += valuesep
                except Exception as e:
                    logging.info(
                        'Error in onlineresources content. See record with fileIdentifier: ' + fileidentifier)
                    logging.debug('Message: ' + str(e))
            # now calculate the score depending on the servicetype
            urls = checkurlsbasic(urlstxt, protocolstxt, mdtype)
            protocols = checkprotocol(protocolstxt, mdtype)
            # ------------------
            # Service metadata
            # ------------------
            # For services, get some other elements as well, for example: the
            # servicetype and operateson URLs
            if mdtype == 'service':
                # ------------------
                # Spatial Data Service type
                # ------------------
                servicetype = ""
                try:
                    servicetype = checkservicetype(
                        csw.records[rec].serviceidentification.type, protocolstxt)
                except Exception as e:
                    logging.info(
                        'Error in servicetype. See record with fileIdentifier: ' + fileidentifier)
                    logging.debug('Message: ' + str(e))
                if servicetype == None:
                    servicetype = ""
                # ------------------
                # Connect point linkage
                # ------------------
                # operations contain connectpoint
                connectpoints = ""
                try:
                    operations = csw.records[
                        rec].serviceidentification.operations
                    # operations is an array with for each operation another
                    # object containing : name, dcplist and connectpoint.
                    # connectpoint is an CI_OnlineResource object, containing
                    # the link
                    logging.debug(
                        fileidentifier + ': operations length: ' + str(len(operations)))
                    # servicetype is an MKMscore, so use the .value property
                    # protocolstxt is needed to determine what protocol to use
                    # for inspection of connectpoints
                    connectpoints = checkconnectpoint(
                        operations, urlstxt, servicetype.value, protocolstxt)
                except Exception as e:
                    logging.info(
                        'Error in operations to get connectpoints. See record with fileIdentifier: ' + fileidentifier)
                    logging.debug('Message: ' + str(e))
                if connectpoints == None:
                    connectpoints = ""
                # OperatesOn
                coupledresourceurls = ""
                try:
                    operateson = csw.records[
                        rec].serviceidentification.operateson
                    # operations is an array with for each operation another
                    # object containing : name, dcplist and connectpoint.
                    # connectpoint is an CI_OnlineResource object, containing
                    # the link
                    logging.debug(
                        fileidentifier + ': operateson length: ' + str(len(operateson)))
                    coupledresourceurls = checkcoupledresource(operateson)
                except Exception as e:
                    logging.info(
                        'Error in operateson to get coupledresourceurls. See record with fileIdentifier: ' + fileidentifier)
                    logging.debug('Message: ' + str(e))
                if coupledresourceurls == None:
                    coupledresourceurls = ""
            # ------------------
            # Writing the rows to a file
            # ------------------
            encodedrow = []
            # metadata_organisatie, fileidentifier, opendata / geogedeeld
            # geldig url,beschrijving beperking,juridische
            # toegangsrestricties,juridische gebruiksrestricties,
            # URL-online-protocol,URL-link_resource,metadata e-mail,titel
            # metadata,trefwoorden,rechthoek,samenvatting,uuid bron,uuid
            # metadata
            if mdtype == 'dataset' or mdtype == 'series':
                encodedrow = encodevalues([contactorg, fileidentifier, wijzigingsdatum, mdprofiel, overigebeperkingen_url, overigebeperkingen_beschrijving, juridischetoegangsrestricties,
                                           juridischegebruiksrestricties, protocols, urls, contactemail, title, keywords, boundingbox, abstract, uuidbron, fileidentifierscore], addtotals=True)
            if mdtype == 'service':
                encodedrow = encodevalues([contactorg, fileidentifier, wijzigingsdatum, mdprofiel, overigebeperkingen_url, overigebeperkingen_beschrijving, juridischetoegangsrestricties, juridischegebruiksrestricties,
                                           servicetype, urls, contactemail, title, keywords, abstract, connectpoints, coupledresourceurls, fileidentifierscore, protocols], addtotals=True)
            # this is only for the scores, to write to this file
            csvwriter.writerow(encodedrow)
        except Exception as e:
            # Some unhandled eception occurred. Log that error and the
            # fileidentifier
            errormsg = "ERROR: something went wrong with the record with identifier: "
            idf = csw.records[rec].identifier
            if idf == None:
                idf = "no identifier -- see errorlog"
            errormsg += idf + "\n"
            # Something unexpected went wrong, so to investigate that: still
            # add a row to the file, only with the fileIdentifier
            errorrow = ["ERROR", idf]
            csvwriter.writerow(errorrow)
            errormsg += str(rec) + "\n"
            errormsg += "Exception:" + "\n"
            errormsg += str(e) + "\n\n"
            logging.error(errormsg)
            logging.exception(e)
            logging.error("--------------------------------------------------------")
    successFullProcessed += maxRecords
    csvfile.close()

# -----------------------
# Fetch CSW results
# -----------------------


def getAllRecs(maxRecords, mdtype, csvfilename, csvheader, cswErrors, successFullProcessed):
    # first, get all IDs
    # perform a getrecords request, with brief
    #
    # try:
    fileidentifiers = getMDIdentifiers(
        maxRecords, mdtype, cswErrors, successFullProcessed)
    logging.info("---- Nr of fileidentifiers: " + str(len(fileidentifiers)))
    # logging.debug(fileidentifiers)

    if cswErrors == -1:
        cswErrors = ""
    # loop over all records
    if csvheader != None:
        csvfile = open(csvfilename, 'a')
        csvwriter = csv.writer(csvfile, delimiter=',',
                               quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        csvwriter.writerow(csvheader)
        csvfile.close()
    print "---- Start: " + str(mdtype)
    logging.info("---- Start: " + str(mdtype))
    returned = maxRecords
    nextrecord = 1
    if len(fileidentifiers) == 0:
        try:
            getRecs(maxRecords, nextrecord, mdtype, csvfilename,
                    cswErrors, successFullProcessed)
        except Exception as e:
            logging.error('Error in getting Records from the CSW: ')
            logging.debug('Message: ' + str(e))
            logging.error("--------------------------------------------------------")
        nextrecord = csw.results['nextrecord']
        returned = csw.results['returned']
        matches = csw.results['matches']
        print "Returned: " + str(returned) + ". Next record: " + str(nextrecord) + " of totally: " + str(matches)
        logging.debug("Returned: " + str(returned) + ". Next record: " +
                      str(nextrecord) + " of totally: " + str(matches))
        while nextrecord > 0 and nextrecord < matches and nextrecord < totalMaxRecords:
            try:
                getRecs(maxRecords, nextrecord, mdtype, csvfilename,
                        cswErrors, successFullProcessed)
            except Exception as e:
                logging.error('Error in getting Records from the CSW: ')
                logging.debug('Message: ' + str(e))
                logging.error("--------------------------------------------------------")
            nextrecord = csw.results['nextrecord']
            returned = csw.results['returned']
            matches = csw.results['matches']
            print "Returned: " + str(returned)
            logging.debug("Returned number of records: " + str(returned))
            print "Next record: " + str(nextrecord) + " of totally: " + str(matches)
            logging.debug("Next record: " + str(nextrecord) +
                          " of totally: " + str(matches))
        print "---- finished: " + str(mdtype)
        logging.debug("---- finished: " + str(mdtype))
    else:
        # first get a cookie...
        # just perform a GetCapabilities request
        caps = urllib2.urlopen(
            cswUrl + "?request=GetCapabilities&service=CSW&version=2.0.2", None, timeoutsecs)
        # httpcode = str(doc.getcode())
        # print caps.info()
        cookie = caps.info().getheader('Set-Cookie')
        # TODO: use a cookie jar now, because of the requests module used
        # https://stackoverflow.com/questions/6878418/putting-a-cookie-in-a-cookiejar
        # jar = cookielib.CookieJar()
        print cookie
        caps.close()
        #
        # JSESSIONID=5618C2FEBED0B7EA17A6A0F8404235CC

        # using the cookiejar:
        cookieJar = cookielib.CookieJar()
        r = requests.get(
            cswUrl + "?request=GetCapabilities&service=CSW&version=2.0.2", cookies=cookieJar)
        # now the cookieJar is filled
        print cookieJar
        retryIdentifiers = []
        cntr = 1
        identifierbatch = []
        batchsize = 0
        for identifier in fileidentifiers:
            print str(cntr) + ") identifier: " + str(identifier)
            logging.debug(str(cntr) + ") identifier: " + str(identifier))
            try:
                getRecs(maxRecords, nextrecord, mdtype, csvfilename,
                        cswErrors, successFullProcessed, [identifier], cookie)
            except Exception as e:
                # TODO: retry?
                logging.error(
                    'Error in getting Records from the CSW: ' + str(identifier))
                logging.debug('Message: ' + str(e))
                logging.error("--------------------------------------------------------")
                # add this to the list to retry
                retryIdentifiers.append(identifier)
            cntr += 1
        # repeat this cycle once, to retry. If identifiers fail again, then
        # write them to a file
        if len(retryIdentifiers) > 0:
            logging.info(
                "============= Retry failed identifiers ================")
            logging.info(
                "Some identifiers could not be processed. Retry fetching records for these records. Number of failed identifiers: " + str(len(retryIdentifiers)))
            logging.info(
                "Start retrying after 30 seconds, as an extra margin for harvesting")
            time.sleep(30)
            cntr = 0
            failedIdentifiers = []
            for identifier in retryIdentifiers:
                print str(cntr) + ") retry for identifier: " + str(identifier)
                logging.debug(
                    str(cntr) + ") retry for identifier: " + str(identifier))
                try:
                    getRecs(maxRecords, nextrecord, mdtype, csvfilename,
                            cswErrors, successFullProcessed, [identifier], cookieJar)
                    # add a message to the summary errors, to show that it
                    # didn't fail in the 2nd attempt
                    cswErrors += "============= SUCCESS 2nd attempt ============= \n"
                    cswErrors += "SUCCESS: Retry succeeded for: " + \
                        str(identifier) + " \n"
                    cswErrors += "=============================================== \n"
                except Exception as e:
                    # TODO: retry?
                    logging.error(
                        '2nd Error in getting Records from the CSW for: ' + str(identifier))
                    cswErrors += "============= ERROR 2nd attempt ============= \n"
                    cswErrors += "ERROR: Retry also failed for: " + \
                        str(identifier) + " \n"
                    cswErrors += "=============================================== \n"
                    logging.debug('Message: ' + str(e))
                    # add this to the list to retry
                    failedIdentifiers.append(identifier)
                cntr += 1
            if len(failedIdentifiers) > 0:
                csvfailedidentifierlist = open(
                    outputdir + strNow + config.get('RESULTFILES', 'failedidentifierlist') + '.csv', 'a')
                csvfailedidentifierlistwriter = csv.writer(
                    csvfailedidentifierlist, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
                for fid in failedIdentifiers:
                    csvfailedidentifierlistwriter.writerow(
                        encodevalues([fid], addtotals=False))
                csvfailedidentifierlist.close()


def getMDIdentifiers(maxRecords, mdtype, cswErrors, successFullProcessed):
    fileidentifiers = []
    # DOC: Only get ISO records, so set the outputSchema
    outputschema = 'http://www.isotc211.org/2005/gmd'
    esn = 'brief'
    # OR: build up a list of unique identifiers differently?
    allRecordsFetched = False
    start = 0
    while allRecordsFetched == False:
        # On timeouts, do a retry of the same request once. Issue #4
        # The error is reported and after 3 attempts, the process breaks.
        attempts = 0
        maxAttempts = 3
        while attempts < maxAttempts and attempts >= 0:  # TODO: make configurable CSW attempts
            try:
                timestamp = datetime.now()
                logging.debug('Time of request: ' + timestamp.strftime("%Y-%m-%d %H:%M:%S") + '. Metadata type: ' + str(
                    mdtype) + ', outputschema: ' + outputschema + ', maxRecords: ' + str(maxRecords) + ', start: ' + str(start))
                if not mdtype:
                    csw.getrecords(None, outputschema=outputschema,
                                   maxrecords=maxRecords, esn=esn)
                else:
                    # sortBy="fileIdentifier:A"
                    # discoveryQuery = PropertyIsEqualTo('csw:ServiceType', 'discovery')
                    # Example: filter on a property. Current OWSLib version has limited filter capabilities
                    #csw.getrecords(qtype=mdtype, outputschema=outputschema, maxrecords=maxRecords, startposition=start, esn=esn, propertyname='csw:ServiceType',keywords=['discovery'])
                    # csw.getrecords(qtype=mdtype, outputschema=outputschema, maxrecords=maxRecords, startposition=start, esn=esn, propertyname='csw:AnyText',keywords=['Beheer PDOK'])
                    csw.getrecords(qtype=mdtype, outputschema=outputschema,
                                   maxrecords=maxRecords, esn=esn, startposition=start)
                # There is no need to continue, since fetching seems to be done
                # okay
                attempts = -1
            except Exception as e:
                attempts += 1
                logging.error('Error getting CSW Records. Retrying after ' + str(
                    cswtimeoutsecs) + ' seconds. Number of attempts done: ' + str(attempts))
                logging.debug('Message: ' + str(e))
                logging.error("--------------------------------------------------------")
                if mdtype:
                    cswErrors += mdtype + ":\n"
                cswErrors += "ERROR getting " + str(maxRecords) + " records\n"
                time.sleep(cswtimeoutsecs)
            # wait a while, to avoid too much calls to NGR
            time.sleep(0.3)
        # Remove all files?
        if attempts == maxAttempts:
            strmdtype = ' '
            if mdtype != None:
                strmdtype = 'for ' + str(mdtype) + ' '
            attempterror = 'Severe error: CSW Records identifiers ' + strmdtype + \
                'cannot be fetched. Number of records: ' + str(maxRecords)
            logging.error(attempterror)
            logging.error("--------------------------------------------------------")
            writeSummary(cswErrors)
            raise Exception(attempterror, attempterror)
        csvidentifierlist = open(
            outputdir + strNow + config.get('RESULTFILES', 'identifierlist') + '.csv', 'a')
        csvidentifierlistwriter = csv.writer(
            csvidentifierlist, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        matches = csw.results['matches']
        for rec in csw.records:
            try:
                fileidentifier = csw.records[rec].identifier
                title = csw.records[rec].identification.title
                if title != None:
                    title = title.replace("\n", " ")
                else:
                    title = ""
                # log identifiers separately
                if fileidentifier == None:
                    fileidentifier == "no identifier found -- see errorlog"
                if fileidentifier not in fileidentifiers:
                    fileidentifiers.append(fileidentifier)
                    csvidentifierlistwriter.writerow(encodevalues(
                        [fileidentifier, title], addtotals=False))
            except Exception as e:
                logging.error('Error processing identifiers')
                logging.debug('Message: ' + str(e))
                logging.error("--------------------------------------------------------")
        csvidentifierlist.close()
        start += maxRecords
        if len(csw.records) == 0 or start > matches:
            allRecordsFetched = True
    return fileidentifiers


# -----------------------
# START Checks
# -----------------------
# checkonlineresources fetches URLs and protocols from the onlineresources elements and checks resolvability of the url
# it adds the HTTP code
# If the service is an OGC-service, it tries to retrieve the Capabilities document
# it returns an array for each URL with: [url, protocol, httpcode]
def checkonlineresources(online):
    # distr info: obj.url, obj.protocol, obj.function, obj.description,
    # obj.name
    onlineresources = []
    if online != None:
        for k in online:
            protocol = ""
            httpcode = "0"
            url = ""
            if k.url != None:
                url = k.url
            if k.protocol != None:
                protocol = k.protocol
            # add an errorcode if protocol is missing but a URL is provided.
            # This will result in a score 0 for protocol?
            if url != "" and protocol == "":
                protocol = "--geen protocol bij url--"  # TODO: configurable
                # TODO: check if httpcode is okay, depending on the protocol
                # check if resolvable. Just use HTTP GET now
            httpcode = gethttpcode(url, protocol)
            onlineresources.append([url, protocol, httpcode])
    return onlineresources


def gethttpcode(url, protocol):
    httpcode = "0"
    if protocol == None:
        protocol = ""
    try:
        if url.startswith("http") == False:
            httpcode = "0"
            if protocol == "dataset" and len(url) > 10:  # TODO: document
                # if protocol is a dataset, don't try to resolve the URL, since it may be an internal path. This is okay.
                # use another HTTP code for this
                httpcode = "intern"
        else:
            if protocol.startswith("OGC:"):
                if url.find("?") == -1:
                    url += "?"
                url += "&request=GetCapabilities&service=" + \
                    protocol.split("OGC:")[1]
            attempts = 0
            # TODO: document number of attempts and retries? Make this
            # configurable?
            maxAttempts = 2
            while attempts < maxAttempts and attempts >= 0:
                try:
                    doc = urllib2.urlopen(url, None, timeoutsecs)
                    httpcode = str(doc.getcode())
                    doc.close()
                    if httpcode != None:
                        logging.debug("URL: " + url + " --> HTTP: " + httpcode)
                    attempts = -1
                except Exception as e:
                    attempts += 1
                    logging.info('Error opening URL: ' + str(url) +
                                 '. Retrying. Number of attempts done: ' + str(attempts))
                    logging.debug('Message: ' + str(e))
                    # TODO: Make the waiting time for URL retries configurable.
                    time.sleep(1)
                # wait a while, to avoid too much load
                time.sleep(0.1)
    except Exception as e:
        logging.error("Opening fails of URL: " + url)
        logging.debug(str(e))
        logging.error("--------------------------------------------------------")
    return httpcode


def checkcoupledresource(operatesonarray):
    """ Check the coupled reosurce urls and UUIDs in the metadata that is pointed to
    Services: for Check 12
    Logic: a valid coupled resource URL is resolvable and points to a metadata record in the nationaalgeoregister.nl (NGR). The uuid of the coupled resource is the uuid of the dataset in the metadata record that the URL points to. This is checked in the metadata document. If all is okay, the score is 2.
    if the URL points to another location than NGR: score 1. If the URL is not valid or the UUID is not found, the socre is 0.
    This is checked for all coupled resource URLs and corresponding UUIDs.
    """
    score = 0
    # if we find an url other than of nationaalgeoregister.nl, then the
    # maxscore will be 1
    maxscore = 2
    errors = 0
    coupledresourceurls = []
    for i in operatesonarray:
        try:
            url = str(i["href"])
            # what are valid URLs? nationaalgeoregister.nl and www.nationaalgeoregister.nl
            # TODO: make configurable?
            if url.find("http://nationaalgeoregister.nl") != 0 and url.find("http://www.nationaalgeoregister.nl") != 0 and url.find("https://nationaalgeoregister.nl") != 0 and url.find("https://www.nationaalgeoregister.nl") != 0:
                logging.debug(
                    'Coupled resource URL does not start with "http(s)://nationaalgeoregister.nl" or "http(s)://www.nationaalgeoregister.nl"' + url)
                maxscore = 1
            logging.debug("Operateson: " + str(i))
            uuidref = str(i["uuidref"])
            # add the uuidref and url to the array as strings
            coupledresourceurls.append("uuid: " + uuidref + " --> " + url)
            attempts = 0
            httpcode = "0"
            # TODO: document number of attempts and retries?
            doc = None
            while attempts < 3 and attempts >= 0:
                try:
                    doc = urllib2.urlopen(url, None, timeoutsecs)
                    # TODO: not httpcode!! But check the uuidref here, use a
                    # string compare?
                    httpcode = str(doc.getcode())
                    if httpcode != None:
                        logging.debug("URL: " + url + " --> HTTP: " + httpcode)
                    attempts = -1
                except Exception as e:
                    attempts += 1
                    logging.info('Error opening URL: ' + str(url) +
                                 '. Retrying. Number of attempts done: ' + str(attempts))
                    logging.debug('Message: ' + str(e))
                    # TODO: Make the waiting time for URL retries configurable.
                    time.sleep(1)
                # wait a while to avoid too much load
                time.sleep(0.1)
            if doc != None:
                # try to read doc, if not a MD_Metadata doc, this could be a CSW response as well
                # So just use a parser to find the MD_Metadata part first
                # see docs: http://lxml.de/parsing.html, Parser options. This prevents an error on loading external entities
                # TB: 2018-05-07: don't use the etree.parse function woth a URL
                # directly, because of issues with https
                f = urllib2.urlopen(url, None, timeoutsecs)
                data = f.read()
                f.close()
                xmldoc = etree.fromstring(data)
                roottag = str(xmldoc)  # was: xmldoc.getroot().tag
                logging.debug("root: " + str(roottag))
                if roottag != "{http://www.isotc211.org/2005/gmd}MD_Metadata":
                    # parse the MD_Metadata elem
                    # xmldoc = xmldoc.xpath("//gmd:MD_Metadata", namespaces={"gmd":"http://www.isotc211.org/2005/gmd"})[0]
                    # , namespaces={"gmd":"http://www.isotc211.org/2005/gmd"})[0]
                    xmldoc = xmldoc.findall(
                        "{http://www.isotc211.org/2005/gmd}MD_Metadata")[0]
                    logging.debug("New XML doc root: " + xmldoc.tag)
                # could be a CSW response or a MD_metadata elem
                mdfile = MD_Metadata(xmldoc)
                # now we have the metadata record, get the Dataset identifier:
                md_ident = mdfile.identification.md_identifier
                logging.debug("md_ident: " + md_ident)
                logging.debug("uuidref : " + uuidref)
                if md_ident != uuidref:
                    errors = errors + 1
                    logging.debug(
                        "Identifier from coupledresource / operateson not found in dataset metadata record that is referred to.")
                doc.close()
                # if resolvablehttpcode(httpcode):
                #    logging.debug('Coupledresource URL (from operatesOn) is resolvable: ' + url)
            else:
                errors = errors + 1
        except Exception as e:
            errors = errors + 1
            traceback.print_exc()
            logging.info('Error in coupledresourceurls content')
            logging.debug('Message: ' + str(e))
    if errors == 0 and len(operatesonarray) > 0:
        score = maxscore
    # the 12th check, so 11 is the index in the matrix
    result = checksservices[11][2][score]
    # TODO: make sperator configurable? And add the md_ident in front?
    coupledresourceurlstxt = valuesep.join(coupledresourceurls)
    # TODO: return two objects, also one for UUIDs? Just add them?
    return MkmScore(coupledresourceurlstxt, score, result)

# operations contains several elements, including the connectpoint


def checkconnectpoint(operations, resourcelocators, servicetype, protocolstxt):
    """ Check the connect point urls, related to the protocols and servicetype as well
    Services: for Check 11
    Logic: a valid connect point URL must be resolvable, at least 10 chracatres long, identical to the URL link resource. (that is: the part before a question mark ("?"))
    """
    # logging.debug("Connectpoint check for: resourcelocators: " + resourcelocators + ", servicetype: " + servicetype +", protocols: " + protocolstxt)
    # for other servicetypes, not required to have connectpoints, so start
    # from a score of 2
    score = 2
    # strip of HTTP Code of the resourcelocators
    # assume there is only one resourcelocator for a service, so the first is
    # the correct one
    reslocator = ""
    if resourcelocators != None:
        reslocator = resourcelocators.split(" (HTTP")[0]
    connectpoints = ""
    cparr = []
    matcherrors = 0
    resolveerrors = 0
    protocol = protocolstxt.split(valuesep)[0]
    if protocol == None:
        protocol = ""
    for i in operations:
        try:
            logging.debug('Connectpoints length: ' +
                          str(len(i["connectpoint"])))
            for c in i["connectpoint"]:
                # the url should be at least 10 chars long
                if len(c.url) > 10:
                    logging.debug('Connectpoint url: ' + str(c.url))
                    cparr.append(str(c.url))
                    # now check the url, with http code and protocol
                    # TODO: document of check of valid httpcodes
                    httpcode = gethttpcode(str(c.url), protocol)
                    logging.debug('Url: ' + str(c.url) + ' --> ' + httpcode)
                    resolvable = resolvablehttpcode(httpcode)
                    if resolvable == False:
                        resolveerrors += 1
                    if str(c.url).split("?")[0] != reslocator.split("?")[0]:
                        logging.debug(
                            str(c.url) + ' is not identical to resource locator: ' + reslocator)
                        matcherrors += 1
        except Exception as e:
            matcherrors += 1
            resolveerrors += 1
            logging.info('Error in connectpoints content.')
            logging.debug('Message: ' + str(e))
    # for view and download connectpoints are required
    logging.debug('Connectpoints found (#' +
                  str(len(cparr)) + '): ' + str(cparr))
    logging.debug('Servicetype: ' + str(servicetype))
    if (servicetype == "view" or servicetype == "download") and len(cparr) == 0:
        score = 0
    connectpoints = valuesep.join(cparr)  # TODO: separator configurable?
    if matcherrors > 0 and score > 0:
        score = 1
    if resolveerrors > 0:
        score = 0
    # nr 11, so 10 is the matrix index
    result = checksservices[10][2][score]
    return MkmScore(connectpoints, score, result)


def resolvablehttpcode(httpcode):
    """ Check if a URL is resolvable, by checking HTTP response codes. Utility function.
    """
    resolvable = False
    validhttpcodesstart = ["2", "3", "400", "403", "5"]
    for code in validhttpcodesstart:
        if httpcode.startswith(code):
            resolvable = True
            logging.debug('Resolvable, HTTP code: ' + httpcode)
    if resolvable == False:
        logging.debug('NOT resolvable, HTTP code: ' + httpcode)
    return resolvable

# the mdtype determines which weight to apply for the score


def checkurlsbasic(urlstxt, protocolstxt, mdtype):
    """ checkurlsbasic analyses the urls from the textstring (including http codes) and calculates the score
    Datasets: for Check 6
    Services: for Check 6
    Logic:, for datasets: if a URL is provided, each URL must be resolvable or must be internal (but with a corresponding service type of "dataset" then). If protocol is a dataset, don't try to resolve the URL, since it may be an internal path. This is okay.

    Valid codes are: HTTP 2xx-serie, HTTP 3xx-serie, HTTP 400 (the server is working, but the client has send an invalid request), HTTP 403 (the server is working, but requires authentication first)  and HTTP 5xx-series (the server is running, but an internal error has occurred. This might be valid, since the error could be caused by the client-request. The service is running on the provided URL, so this code is considered okay).
    Logic for services: at least one URL is required
    """
    # urlstxt consists of a list of urls, split by ;
    # for each url, check if it has been resolvable by inspecting the HTTP
    # code added to the URL
    score = 2
    if len(urlstxt) > 3:  # TODO: take into account that starts with " (HTTP " as well, so longer url is needed
        # start with an empty score if there are urls
        score = 0
    urls = urlstxt.split(valuesep)  # TODO: make configurable?
    errors = 0
    nrurls = 0
    for u in urls:
        if u != None:
            try:
                # u starts with " (HTTP 0)", so must be longer than
                if len(u) > 2 and u != " (HTTP 0)":
                    # TODO: assume http 2xx, 3xx and 5xx-series (all!) are the only okay HTTP codes?
                    # Or use others as well? Or just the start mubers, so 204 is also included
                    # for 400-series: HTTP 400 should be okay, since this means that the client sent a wrong request (but the service still exists / works there, e.g. TMS)
                    # TODO: use a list of HTTP codes that are okay.
                    # Configurable
                    nrurls = nrurls + 1
                    if u.find("(HTTP 2") == -1 and u.find("(HTTP 3") == -1 and u.find("(HTTP 5") == -1 and u.find("(HTTP 400") == -1 and u.find("(HTTP 403") == -1 and u.find("(HTTP intern)") == -1:
                        errors = errors + 1
            except Exception as e:
                logging.info("Checking URLs failed for: " + u)
                logging.debug(str(e))
                errors = errors + 1
    if mdtype == "dataset" or mdtype == "series":
        if errors == 0:
            score = 2
        # if we don't have urls, but the service type contains OGC: .. , download or website, then we have an error
        # TODO: document
        if (protocolstxt.find("OGC:") > -1 or protocolstxt.find("download") > -1 or protocolstxt.find("website") > -1) and nrurls == 0:
            score = 0
        # checkid = 6, so the index in the matrix is: 5
        result = checksdatasets[5][2][score]
    else:
        # there must be a URL as well, so check this
        if errors > 0 or nrurls == 0:
            score = 0
        else:
            score = 2
        result = checksservices[5][2][score]
    return MkmScore(urlstxt, score, result)

# protocoltxt analyses the protocols by looking if they are in the codelist
# the mdtype determines which weight to apply for the score


def checkprotocol(protocolstxt, mdtype):
    """ Check the protocol
    Datasets: for Check 5
    Services: for Check 5, servicetype
    Logic: each listed protocol must be in the codelist for servicetypes for a score = 2. If this is not the case, the score = 1. If no protocol is provided but a URL is (for check 6), then the score is 0.
    """
    # protocolstxt consists of a list of protocols, split by ;
    # for each protocol, check if it is in the codelist
    score = 2
    # if len(protocolstxt) > 2:
    # start with an empty score if there are urls
    #    score = 0
    protocols = protocolstxt.split(valuesep)  # TODO: make configurable?
    notinlist = 0
    missing = False
    for p in protocols:
        if p != None:
            try:
                if p == "--geen protocol bij url--":  # TODO: configurable?
                    score = 0
                    missing == True
                elif len(p) > 0:
                    # For serviceTypes: use the values from the codelist, since
                    # this one contains an array of (single valued) arrays
                    found = False
                    for st in codelistServiceTypes:
                        if p == st[0]:
                            found = True
                    if found == False:
                        notinlist = notinlist + 1
            except Exception as e:
                logging.debug("Protocol not in codelist, protocol: " + p)
                logging.debug(str(e))
                notinlist = notinlist + 1
    if missing:
        score = 0
    elif notinlist > 0:
        score = 1
    # elif notinlist == 0:
    #    score = 2
    if mdtype == "dataset" or mdtype == "series":
        # checkid = 5, so the index in the matrix is: 11-1=10
        result = checksdatasets[4][2][score]
    else:
        result = checksservices[13][2][score]
    return MkmScore(protocolstxt, score, result)


def checkjuridischegebruiksrestricties(restrictionsarr, mdtype):
    """ Check the juridische gebruikssrestricties
    Datasets: for Check 4
    Services: for Check 4
    Logic: otherRestrictions must be present or no value is provided for a score = 2. Other values and more than 1 value are not allowed.
    For logic / remarks, also see issue https://bitbucket.org/thijsbrentjens/metadatakwaliteit/issue/27
    """
    score = 2  # Might be empty, so start from score = 2
    restrictionstxt = ""
    if restrictionsarr != None:
        # restrictionsarr could contain multiple values
        logging.debug("Restrictions array (nr of objects: " +
                      str(len(restrictionsarr)) + "): " + str(restrictionsarr))
        if (len(restrictionsarr) != 0 and restrictionsarr[0] != "otherRestrictions") or len(restrictionsarr) > 1:
            score = 0
        restrictionstxt = valuesep.join(restrictionsarr)
    if mdtype == "dataset" or mdtype == "series":
        # checkid = 4, so the index in the matrix is: 3
        result = checksdatasets[3][2][score]
    else:
        result = checksservices[3][2][score]
    return MkmScore(restrictionstxt, score, result)


def checkjuridischetoegangsrestricties(restrictionsarr, mdtype):
    """ Check the juridische toegangsrestricties
    Datasets: for Check 3
    Services: for Check 3
    Logic: otherRestrictions must be present (1 or 2 times) for a score = 2 and must be the only value provided, otherwise the score is 0.
    For logic / remarks, also see issue https://bitbucket.org/thijsbrentjens/metadatakwaliteit/issue/27
    """
    score = 0  # has to be provided, so start from score 0
    restrictionstxt = ""
    errorfound = False
    try:
        if restrictionsarr != None:
            # otherRestricions must be found, only then the score could be 2
            # It might be there two times.
            for r in restrictionsarr:
                if r != "otherRestrictions":
                    errorfound = True
            if len(restrictionsarr) > 2:  # max 2 times otherRestrictions
                errorfound = True
                logging.debug("Too much occurrences of toegangsrestricties, found: " +
                              str(len(restrictionsarr)) + ", values: " + str(restrictionsarr))
            restrictionstxt = valuesep.join(restrictionsarr)
        else:
            errorfound = True
    except Exception as e:
        logging.info('Error in toegangsrestricties, score 0.')
        logging.debug(str(e))
        errorfound = True
    if errorfound == False and restrictionstxt != "":
        score = 2
    if mdtype == "dataset" or mdtype == "series":
        # checkid = 4, so the 3rd value in the matrix (index 2).
        result = checksdatasets[2][2][score]
    else:
        result = checksservices[2][2][score]
    return MkmScore(restrictionstxt, score, result)


def checkbbox(boundingbox, mdtype):
    """ Check the boundingbox / extent in Netherlands
    Datasets: for Check 10
    Logic: the extent must be in the area of NL + NCP (3.047,50.670,7.276,53.612). If no extent is provided, the score is 0.
    """
    score = 0
    result = 0
    bboxstr = ""
    try:
        bboxstr = boundingbox.minx + "," + boundingbox.miny + \
            "," + boundingbox.maxx + "," + boundingbox.maxy
        # TODO: make values bbox configurable?
        # larger: 2.0, 50.0, 8.0, 55.0
        if float(boundingbox.minx) >= 2.0 and float(boundingbox.miny) >= 50.0 and float(boundingbox.maxx) <= 8.0 and float(boundingbox.maxy) <= 57.0:
            score = 2
            logging.debug('Boudingbox ' + bboxstr + ' is in NL area')
        else:
            score = 1
            logging.debug('Boudingbox ' + bboxstr + ' is NOT in NL area')
    except Exception as e:
        logging.info('Error in boundinbox extent.')
        logging.info(str(e))
        try:
            bboxstr = boundingbox.minx + "," + boundingbox.miny + \
                "," + boundingbox.maxx + "," + boundingbox.maxy
        except Exception as e:
            logging.debug(
                'Error in boundinbox extent, bboxstr cannot be constructed')
            logging.debug(str(e))
    if mdtype == "dataset" or mdtype == "series":
        # checkid = 10, so the index in the matrix is: 9
        result = checksdatasets[9][2][score]
    return MkmScore(bboxstr, score, result)


def checkoverigebeperkingen(beperkingenarr, mdtype):
    """ Check both the URL and description of the Beperkingen.
    Datasets: for Check 1 and 2
    Services: for Check 1 and 2
    Logic: for Check 1: the combination of description and URL must be in the codelist for limitations, then score = 2, otherwise 0
    Logic: for Check 2: the combination of description and URL must be in the codelist for limitations, then score = 2, otherwise 0
    """
    beperkingurltxt = ""
    beschrijvingtxt = ""
    score1 = 0
    score2 = 0
    try:
        # maybe one element, then this must be a url
        if len(beperkingenarr) > 0:
            beperkingurltxt = beperkingenarr[0]
            if beperkingurltxt.lower().startswith("http") == False:
                beschrijvingtxt = beperkingenarr[0]
                beperkingurltxt = ""
        if len(beperkingenarr) >= 2:
            beschrijvingtxt = beperkingenarr[1]
            # elements may be turned around
            if beperkingurltxt.lower().startswith("http") == False:
                beperkingurltxt = beperkingenarr[1]
                beschrijvingtxt = beperkingenarr[0]
            # now loop over the codelist for limiations
        beschrijvingtxt = beschrijvingtxt.replace("\n", " ")
        beperkingurltxt = beperkingurltxt.replace("\n", " ")
        for codes in codelistLimitations:
            # Score if the value is in the second column of the codelist.
            # this makes sure that the URL matches with the textual code
            # Score if the value is in the first column of the codelist and a
            # valid URL is provided. This is the same logic for check 1 and 2
            if beperkingurltxt.lower().startswith(codes[1].lower()) and beschrijvingtxt.lower().startswith(codes[0].lower()):
                # if codes[1].lower().startswith(beperkingurltxt.lower()) and
                # codes[0].lower().startswith(beschrijvingtxt.lower()):
                score1 = 2
                score2 = 2
            # if beperkingurltxt.startswith(codes[1]) and codes[0].lower() == beschrijvingtxt.lower():
            # score2 = 2
    except Exception as e:
        logging.debug(str(e))
        score1 = 0
        score2 = 0
    if mdtype == "dataset" or mdtype == "series":
        # checkid = 11, so the index in the matrix is: 11-1=10
        result1 = checksdatasets[0][2][score1]
        result2 = checksdatasets[1][2][score2]
    else:
        result1 = checksservices[0][2][score1]
        result2 = checksservices[1][2][score2]
    results = [MkmScore(beperkingurltxt, score1, result1),
               MkmScore(beschrijvingtxt, score2, result2)]
    return results

# the abstract has checkid = 11 for datasets, 10 for services

def checkabstract(abstracttxt, mdtype):
    """ Check the abstract
    Datasets: for Check 11
    Services: for Check 10
    Logic: the abstract must be at least 25 characters and at max 2000 for a score = 2.
    """
    ascore = 0
    if abstracttxt != None:
        abstracttxt = abstracttxt.replace("\n", " ")
        # TODO: make min and max abstract length configurable?
        if len(abstracttxt) >= 25 and len(abstracttxt) <= 4000:
            ascore = 2
    else:
        abstracttxt = ""
    # Now fetch the result
    if mdtype == "dataset" or mdtype == "series":
        # checkid = 11, so the index in the matrix is: 11-1=10
        result = checksdatasets[10][2][ascore]
    else:
        result = checksservices[9][2][ascore]
    return MkmScore(abstracttxt, ascore, result)

# the keywords have checkid = 9 for datasets, 9 for services


def checkkeywords(keywordsarr, mdtype):
    """ Check the keywords
    Datasets: for Check 9
    Services: for Check 9
    Logic: there must be at least one keyword to get a score = 2. If keywords contain comma's (","), then a maimum of score = 1 is possible.
    """
    score = 0
    # keywordsarr is an array of objects, each containing a property "keywords" and info on a thesaurus
    # here we join the keywords from all objects to one array
    keywordsstr = ""
    if keywordsarr != None:
        keywords = []
        for k in keywordsarr:
            for i in k["keywords"]:
                i = i.replace("\n", " ")
                # exception for 1 keyword of INSPIRE
                if i.find(",") > -1 and i != "Gebiedsbeheer, gebieden waar beperkingen gelden, gereguleerde gebieden en rapportage-eenheden":
                    score = 1
                keywords.append(i)
        # if the score is already 1, then we know the keywords are not
        # correctly set
        if len(keywords) > 0 and score != 1:
            score = 2
        keywordsstr = valuesep.join(keywords)
    else:
        keywordsstr = ""
    # Now fetch the result
    if mdtype == "dataset" or mdtype == "series":
        # checkid = 9, so the index in the matrix is: 8
        result = checksdatasets[8][2][score]
    else:
        result = checksservices[8][2][score]
    return MkmScore(keywordsstr, score, result)

# Check uniqueness and syntax


def checkuuidfileidentifier(uuidtxt, mdtype):
    """ Check uniqueness and syntax of the UUID of the metadata record
    Datasets: for Check 13
    Services: for Check 13
    Logic: the UUID must be present, unique, in lower case, at least 10 characters and does not contain { or }
    """
    score = 0
    if uuidtxt != None:
        if uuidtxt in allfileidentifiers:
            score = 0
        else:
            score = checkuuidsyntax(uuidtxt)
        # add the identifier to the fileidentifier list
        allfileidentifiers.append(uuidtxt)
    if mdtype == "dataset" or mdtype == "series":
        # checkid = 9, so the index in the matrix is: 8
        result = checksdatasets[12][2][score]
    else:
        result = checksservices[12][2][score]
    return MkmScore(uuidtxt, score, result)


def checkuuidbron(uuidtxt, fileidentifier, mdtype):
    """ Check uniqueness and syntax of the UUID of the dataset / bron (MD_identifier)
    Datasets: for Check 12
    Logic: the UUID must be present, unique, in lower case, at least 10 characters and does not contain { or }
    """
    score = 0
    if uuidtxt != None:
        uuidcombi = [fileidentifier, uuidtxt]
        if uuidcombi in allbronidentifiers:
            # check if the fileidentifier is different, then it is okay,
            # otherwise score 0
            score = 0
        else:
            score = checkuuidsyntax(uuidtxt)
        # add the identifier to the fileidentifier list
        try:
            allbronidentifiers.append(uuidcombi)
        except Exception as e:
            logging.info(
                'Error in adding the uuidbron to the array. See record with fileIdentifier: ' + fileidentifier)
            logging.debug('Message: ' + str(e))
    else:
        uuidtxt = ""
    if mdtype == "dataset" or mdtype == "series":
        # checkid = 12, so the index in the matrix is: 11
        result = checksdatasets[11][2][score]
    return MkmScore(uuidtxt, score, result)


def checkuuidsyntax(uuidtxt):
    """ Check syntax of the UUID, utility function
    """
    score = 0
    if uuidtxt != None:
        if len(uuidtxt) < 10:
            score = 0
        elif uuidtxt.find("{") > -1 or uuidtxt.find("}") > -1 or uuidtxt.lower() != uuidtxt:
            score = 1
        else:
            score = 2
    return score


def checktitle(titletxt, mdtype):
    """ Check the title on length
    Datasets: for Check 8
    Services: for Check 8
    Logic: the title must be between 3 and 75 characters long.
    """
    score = 2
    if len(titletxt) > 75:
        score = 1
    if len(titletxt) < 3:
        score = 0
    if mdtype == "dataset" or mdtype == "series":
        # checkid = 8, so the index in the matrix is: 7
        result = checksdatasets[7][2][score]
    else:
        result = checksservices[7][2][score]
    return MkmScore(titletxt, score, result)


def checkemail(emailtxt, mdtype):
    """ Check the email address
    Datasets: for Check 7
    Services: for Check 7
    Logic: the emailaddress must conform to some loexigraphical rules. For now set the score to 0 for all cases, since a manual check / update of the score needs to be done afterwards.
    """
    score = 0  # only allow scores if the emailaddress is okay. Issue #17
    if emailtxt.find("@") == -1 or emailtxt.find(".") == -1 or len(emailtxt) < 3:
        score = 0
    if mdtype == "dataset" or mdtype == "series":
        # checkid = 7, so the index in the matrix is: 6
        result = checksdatasets[6][2][score]
    else:
        result = checksservices[6][2][score]
    return MkmScore(emailtxt, score, result)


# -----------------
# only for services
# -----------------
def checkservicetype(servicetype, protocolstxt):
    # see issue #28, if the protocol contains OGC:WMS, the servicetype must be view
    # if the protocol contains OGC:WFS, the servicetype must be download
    if protocolstxt == None:
        protocolstxt = ""
    score = 0
    for sdst in codelistSpatialDataServiceTypes:
        if servicetype == sdst[0]:
            score = 2
    if servicetype == "view" and protocolstxt.find("OGC:WMS") == -1 and protocolstxt.find("OGC:WMTS") == -1 and protocolstxt.find("UKST") == -1:
        score = 0
        logging.debug("Protocol and servicetype do not match; should be OGC:WMS, OGC:WMTS or UKST for protocol and service type = view. Protocols: " +
                      str(protocolstxt) + ", Servicetype: " + servicetype)
    if servicetype == "download" and protocolstxt.find("OGC:WFS") == -1 and protocolstxt.find("UKST") == -1 and protocolstxt.lower().find("atom") == -1 and protocolstxt.find("download") == -1 and protocolstxt.find("OGC:WCS") == -1 and protocolstxt.find("OGC:SOS") == -1:
        score = 0
        logging.debug("Protocol and servicetype do not match; should be OGC:WFS, OGC:WCS, OGC:SOS, UKST, contain Atom for protocol and service type = download. Protocols: " +
                      str(protocolstxt) + ", Servicetype: " + servicetype)
    result = checksservices[4][2][score]
    return MkmScore(servicetype, score, result)


def writeSummary(cswErrors):
    # if cswErrors == -1:
    #    cswErrors = ""
    # write to the summary, or append modus?
    summaryfile = open(newfilenamesummary, 'a')
    summaryfile.writelines("SAMENVATTING\n")
    summaryfile.writelines("===========================\n")
    summaryfile.writelines(str(now) + "\n")
    if len(str(cswErrors)) > 3:
        summaryfile.writelines("!!! De CSW geeft fouten !!!\n")
        summaryfile.writelines(
            "! Misschien niet alle gegevens konden opgehaald worden !\n")
        summaryfile.writelines(cswErrors + "\n")
        summaryfile.writelines("===========================\n")
    else:
        summaryfile.writelines("===========================\n")
        # summaryfile.writelines("Goed verlopen :)\n")
    summaryfile.writelines("Aantal records verwerkt: " +
                           str(successFullProcessed) + "\n")
    summaryfile.close()

# -----------------
# END CHECKS
# -----------------

newfilenamesummary = outputdir + strNow + '_summary.txt'
# -----------------
# INIT emailadressen list (close at the end)
# -----------------
emailadressenFile = open(outputdir + strNow +
                         config.get('RESULTFILES', 'emaillist') + '.csv', 'a')
emailwriter = csv.writer(emailadressenFile, delimiter=',',
                         quotechar='"', quoting=csv.QUOTE_ALL)

# -----------------
# START DATASETS
# -----------------
mdtype = 'dataset'  # and dataset series?

# TODO: better CSV header?
# add a time and date to the file
# open file for appending the values to
newfilenamedataset = outputdir + strNow + \
    config.get('RESULTFILES', 'datasetsresult1') + '.csv'

csvheader = ["metadata_organisatie", "fileidentifier", "wijzigingsdatum", "standaard_versie"]
for i, value in enumerate(weightsdatasets):
    if i > 0:
        # append the omschrijving of the scoringsmatrix
        csvheader.append(str(value[0]) + "_" + value[1])
        csvheader.append(str(value[0]) + "_" + value[1] + "_score")
        csvheader.append(str(value[0]) + "_" + value[1] + "_result")
# for the total score
csvheader.append("resultaat")  # TODO: config name?
# print csvheader
getAllRecs(maxRecords, mdtype, newfilenamedataset,
           csvheader, cswErrors, successFullProcessed)

mdtype = 'series'  # for dataset series, treat these as datasets as well
try:
    getAllRecs(maxRecords, mdtype, newfilenamedataset,
               None, cswErrors, successFullProcessed)
except Exception as e:
    logging.info('Error in processing the records for series')
    logging.debug('Message: ' + str(e))

# for services:
mdtype = 'service'
csvheader = ["metadata_organisatie", "fileidentifier", "wijzigingsdatum", "standaard_versie"]
for i, value in enumerate(weightsservices):
    if i > 0:
        # append the omschrijving if the scoringsmatrix
        csvheader.append(str(value[0]) + "_" + value[1])
        csvheader.append(str(value[0]) + "_" + value[1] + "_score")
        csvheader.append(str(value[0]) + "_" + value[1] + "_result")
# add the total score column description
csvheader.append("resultaat")
newfilenameservice = outputdir + strNow + \
    config.get('RESULTFILES', 'servicesresult1') + '.csv'
getAllRecs(maxRecords, mdtype, newfilenameservice,
           csvheader, cswErrors, successFullProcessed)

writeSummary(cswErrors)

# -----
# close all open files
# ----
emailadressenFile.close()
# or use as mdtype None to get all
# getAllRecs(maxRecords, None)
