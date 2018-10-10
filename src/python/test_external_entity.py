# sample URL with errors:

#https://www.nationaalgeoregister.nl/geonetwork/srv/en/csw?Service=CSW&Request=GetRecordById&Version=2.0.2&id=9d973c4a-ef03-4785-b7f6-942e86b385f7&outputSchema=http://www.isotc211.org/2005/gmd&elementSetName=full

# from owslib.etree import etree
from owslib.iso import *
import urllib2
from lxml import etree

url = "https://www.nationaalgeoregister.nl:443/geonetwork/srv/dut/csw?service=CSW&request=GetRecordById&version=2.0.2&outputSchema=http://www.isotc211.org/2005/gmd&elementSetName=full&id=d0eb1b7e-9e3b-4f36-a47f-bb656cedbb7c"

#
print "OLD: "
print "============================="
try:
    parser = etree.XMLParser(no_network=True, resolve_entities=False)
    xmldoc = etree.parse(url, parser)
    roottag = str(xmldoc)
    print "root: " + str(roottag)
    if roottag != "{http://www.isotc211.org/2005/gmd}MD_Metadata":
        # pare the MD_Metadata elem
        xmldoc = xmldoc.xpath("//gmd:MD_Metadata", namespaces={"gmd":"http://www.isotc211.org/2005/gmd"})[0]
        print "New XML doc root: " + xmldoc.tag
    mdfile = MD_Metadata(xmldoc) # could be a CSW response or a MD_metadata elem
    print mdfile
    md_ident = mdfile.identification.md_identifier
    print "md_ident: " + md_ident
except Exception as e:
    print e
print "============================="
print "NEW: "
print "============================="
f = urllib2.urlopen(url)
data = f.read()
f.close()
xmldoc = etree.fromstring(data)

# parser = etree.XMLParser(no_network=True, resolve_entities=False)
# xmldoc = etree.parse(url, parser)
roottag = str(xmldoc)
print "root: " + str(roottag)
if roottag != "{http://www.isotc211.org/2005/gmd}MD_Metadata":
    # pare the MD_Metadata elem
    xmldoc = xmldoc.xpath("//gmd:MD_Metadata", namespaces={"gmd":"http://www.isotc211.org/2005/gmd"})[0]
    print "New XML doc root: " + xmldoc.tag
mdfile = MD_Metadata(xmldoc) # could be a CSW response or a MD_metadata elem
print mdfile
md_ident = mdfile.identification.md_identifier
print "md_ident: " + md_ident
