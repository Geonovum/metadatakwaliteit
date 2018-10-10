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

"""Script to update email scores of CSV files with Monitoring scores
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
emailfilename = ""
# test: 2015-04-03_114940emailadressen.csv
strNow = ""
# the first argument is the CSW URL. If this is not present, then use the
# preconfigured URL.
if len(sys.argv) > 1:
    emailfilename = sys.argv[1]
    strNow = emailfilename.split(config.get('RESULTFILES', 'emaillist'))[
        0]  # everyting before the emailadresses filename start
else:
    #cswUrl = config.get('CSW', 'baseUrl')
    raise Exception("No filename given", "No filename given")

# used to seperate values in CSV-cells
valuesep = config.get('DEFAULT', 'valueseparator')

# -----------------
# INIT output
# -----------------

outputdir = config.get('RESULTFILES', 'outputdir')

# -----------------
# INIT error logging
# -----------------
errorfilename = outputdir + strNow + \
    config.get('RESULTFILES', 'errorlog') + '_emails.log'
# TODO: level of logging via config
logging.basicConfig(filename=errorfilename, level=logging.ERROR)


# Util
# TODO: refactor, separate class
# Read in a file as CSV, return array
# return an empty array if not found
def readCSVFile(filename):
    csvValues = []
    try:
        csvfile = open(filename, "r")
        csvValues = list(csv.reader(csvfile))
        return csvValues
    except Exception:
        logging.error('Error loading file: ' + filename)

# emailColposition: 0 based
# read in emailadesses


def updateEmailadresses(filenamedataset, checkscores, emailadressenFile, emailColPosition, totalPosition):
    try:
        readfile = open(filenamedataset, "rb")
        csvreader = csv.reader(readfile, delimiter=',', quotechar='"')
        # copy the file
        # replace the original file name
        filenamedatasetTemp = filenamedataset.replace(".csv", "_email.csv")
        writefile = open(filenamedatasetTemp, "w")
        csvwriter = csv.writer(writefile, delimiter=',',
                               quotechar='"', quoting=csv.QUOTE_MINIMAL)
        index = -1
        rowindex = -1
        emailScores = []
        emailScores = list(csv.reader(emailadressenFile))
        # emailadressenFile contains the scores of emails
        # emailScores = csv.reader(emailadressenFile, delimiter=',',quotechar='"')
        for row in csvreader:
            index += 1
            # lookup scores from emailaddresses
            for emailRow in emailScores:
                if row[emailColPosition] == emailRow[1]:
                    score = emailRow[2]
                    # TODO: if this is 1, then score is 2?
                    score = int(score) * 2
                    # for services and datasets: checkscores index for email is
                    # 6
                    result = checkscores[6][2][score]
                    # the next value is the score, then the result
                    # update the total too
                    row[emailColPosition + 1] = str(score)
                    row[emailColPosition + 2] = str(result)  # lookup score
                    row[totalPosition] = str(int(row[totalPosition]) + result)
            csvwriter.writerow(row)
        readfile.close()
        writefile.close()
    except Exception as e:
        logging.error(str(e))
        return False

# -----------------
# Read weightmatrices
# ----------------
weightsdatasets = readCSVFile(
    configdir + config.get('SCORING', 'weightsdatasets'))
# create checks with scores from the file
checksdatasets = []
for i, row in enumerate(weightsdatasets):
    if i > 0:
        # the first col is the checkid, that is the identifier for checks matrix
        # NOTE: order of the points is inverted, to allow for 0=bad, 1=medium,
        # 2=good
        points = [int(row[4]), int(row[3]), int(row[2])]
        checksdatasets.append([int(row[0]), row[1], points])
logging.debug(checksdatasets)

# create checks with scores from the file
# An array is fine to use
weightsservices = readCSVFile(
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
# INIT emailadressen list (close at the end)
# -----------------
emailadressenFile = open(outputdir + emailfilename, 'r')
# not a writer, but a reader


# For reading and writing:
# create a CSV reader and a CSV writer
# if the apropriate row is found (because of an email match), update the scoere
# Take into account the quoting of the values
# http://www.dreamincode.net/forums/topic/196479-editing-a-csv-file/

# TODO: improve CSV header
# add a time and date to the file
# open file for appending the values to
filenamedataset = outputdir + strNow + \
    config.get('RESULTFILES', 'datasetsresult1') + '.csv'

# update emailadresses: 4th and 5th param are indices for columns in the
# scores CSV
updateEmailadresses(filenamedataset, checksdatasets, emailadressenFile, 20, 41)

# TODO: fix reopening the file. This is needed to reset the csv reader?
emailadressenFile.close()
emailadressenFile = open(outputdir + emailfilename, 'r')
# for services:
filenameservice = outputdir + strNow + \
    config.get('RESULTFILES', 'servicesresult1') + '.csv'
# update emailadresses: 4th and 5th param are indices for columns in the
# scores CSV
updateEmailadresses(filenameservice, checksservices, emailadressenFile, 20, 44)

# -----
# close all open files
# ----
emailadressenFile.close()
