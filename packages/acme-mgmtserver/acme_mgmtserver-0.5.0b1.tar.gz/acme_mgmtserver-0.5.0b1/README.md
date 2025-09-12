ACME Management Server (ACMEMS): Now **"Macen"**
================================================

**Deprecated: The software has been rename to ["Macen"](https://github.com/mswart/macen)! Please, update to that one to receive future updates.**

[![PyPI version](https://img.shields.io/pypi/v/acme-mgmtserver.svg)](https://pypi.python.org/pypi/acme-mgmtserver) [![Python Versions](https://img.shields.io/pypi/pyversions/acme-mgmtserver.svg)](https://pypi.python.org/pypi/acme-mgmtserver) [![PyPi Status](https://img.shields.io/pypi/status/acme-mgmtserver.svg)](https://pypi.python.org/pypi/acme-mgmtserver)


[LetsEncrypt](https://letsencrypt.org) supports issuing free certificates by communication via ACME - the Automatically Certificate Management Evaluation protocol.

This tools is yet another ACME client ... but as a client/server model.


## Why yet another ACME client

Some aspects are special:

* **ACME handling can be put into own VM / container ...**: The server can be placed into an own VM, container, network segment to limit the security risk on compromised systems.
* **Only the server requires all the ACME dependencies**: The clients require only a SSL tool like OpenSSL and a HTTP client like wget or curl, no python, no build tools. Python with python-acme and its dependencies (PyOpenSSL, Cryptography, ...) is only needed for the server.
* **Supports distributed web servers**: All `.well-known/acme-challenges` requests for all domains can be served directly by the server. This makes it easy to validate domains when using multiple web server in distributed or fail-over fashion by forwarding all `.well-known/acme-challenges` requests.
* **Only the server needs the ACME account information**: It is not that security relevant, but only the ACME Management Server needs access to the account information / key for the ACME server like LetsEncrypt.
* **Caching CSR signs**: The returned signed certificate of a CSR is cached until the certificate is nearly expired (per default two week). If two machines have manual shared a key and CSR and they reusing both, they will both get from ACMEMS the same certificate back.

## License

GPL License

Copyright (c) 2015-2025, Malte Swart