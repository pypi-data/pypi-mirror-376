pycrdfcli
=========

Description
-----------
A simple Python script to interact with CRDF (crdf.fr) APIs from CLI.


Usage
-----
```
$ pip install pycrdfcli

$ pycrdfcli
usage: pycrdfcli.py [-h] [-k API_KEY] [-i INPUT_FILE] [-a {submit,check,info_key}]

version: 1.2

options:
  -h, --help            show this help message and exit
  -k, --api-key API_KEY
                        API key (could either be provided in the "SECRET_CRDF_API_KEY" env var)
  -i, --input-file INPUT_FILE
                        Input file (either list of newline-separated FQDN, or a list newline-separated of CRDF refs)
  -a, --action {submit,check,info_key}
                        Action to do on CRDF (default 'submit')
```
  

Changelog
---------
* version 1.2 - 2025-09-14: Publication on pypi.org and few fixes


Copyright and license
---------------------

pycrdfcli is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

pycrdfcli is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  

See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU General Public License along with pycrdfcli. 
If not, see http://www.gnu.org/licenses/.

Contact
-------
* Thomas Debize < tdebize at mail d0t com >