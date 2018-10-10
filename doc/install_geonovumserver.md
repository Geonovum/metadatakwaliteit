# Metadatakwaliteit tool installeren
**Nota bene:** Deze documentatie kan verouderd zijn.

## metadatakwaliteit installeren
maak dir(s) aan:
```
/apps/metadatakwaliteit/git/
```

kopieer broncode (TODO: Github locatie)



## OWSLib en afhankelijkheden
```
# Centos dependencies voor OWSLib
yum install openssl-devel

# easy_install and gcc dependencies
yum install python-pip
yum install gcc

pip install six py-dateutil pytz requests

# OWSLib:
easy_install OWSLib
```

### test OWSLib
run python script:
```
from owslib.wms import WebMapService
wms = WebMapService('http://geodata.nationaalgeoregister.nl/natura2000/wms', version='1.3.0')
wms.identification.type
# should print: 'WMS'
wms.identification.title
# should print: 'Natura2000'
list(wms.contents)
# should print: ['natura2000']
```

###  patches OWSLib?
Might need to fix iso.py in OWSLib, to get contact etc!!!
Do this by fixing the file iso.py and then recompile the class, using:

### example dir Centos
**TODO: fix for python 2.7**

```
/usr/lib/python2.6/site-packages/OWSLib-0.16.0-py2.6.egg/owslib
```

Kopieer hierheen de owslib/patches voor:
* csw.py
* iso.py
* util.py

```
$ python

import py_compile
py_compile.compile("iso.py")
py_compile.compile("csw.py")
py_compile.compile("util.py")
```
