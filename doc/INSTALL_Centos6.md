# install log python 2.7.x on Centos6
Required by OWSLib

https://www.digitalocean.com/community/tutorials/how-to-set-up-python-2-7-6-and-3-3-3-on-centos-6-4

## steps

```
wget http://www.python.org/ftp/python/2.7.15/Python-2.7.15.tar.xz
xz -d Python-2.7.15.tar.xz
tar -xvf Python-2.7.15.tar

cd Python-2.7.15
./configure --prefix=/usr/local

make
make altinstall
```


### pip setuptools

```
wget --no-check-certificate https://pypi.python.org/packages/source/s/setuptools/setuptools-1.4.2.tar.gz

# Extract the files from the archive:
tar -xvf setuptools-1.4.2.tar.gz

# Enter the extracted directory:
cd setuptools-1.4.2

# Install setuptools using the Python we've installed (2.7.6)
python2.7 setup.py install
```

Pip for 2.7:
```
wget https://bootstrap.pypa.io/get-pip.py
python2.7 get-pip.py
```

## OWSLib and dependencies
Use pip2.7 to install in python 2.7
```
pip2.7 install six py-dateutil pytz requests
pip2.7 install OWSLib
```

Check:
```
cd /usr/local/lib/python2.7/site-packages/
```

### Patch OWSLib
```
cd /usr/local/lib/python2.7/site-packages/OWSLib-0.17.0-py2.7.egg/owslib


# only csw.py and util.py for Cookies. 

```
