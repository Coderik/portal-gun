.. _install:

============
Installation
============

**Portal Gun** has the following external dependencies:

- `boto3 <https://github.com/boto/boto3>`_ - to make requests to AWS;
- `Fabric <https://github.com/fabric/fabric>`_ - to execute commands over ssh;
- `marshmallow <https://github.com/marshmallow-code/marshmallow>`_ - for serialization.

Note that Python 3 is not supported yet, because Fabric is Python 2 only. Migration to Python 3 should be made after the first stable release of `Fabric 2 <http://bitprophet.org/blog/2017/04/17/fabric-2-alpha-beta/>`_.

Install or upgrade from the PyPI
================================

It is **strongly recommended** to install Portal Gun in **a virtual Python environment**.

To install the latest stable version from the PyPI:

::

    $ pip install -U portal-gun

To install the latest pre-release version from the PyPI:

::

    $ pip install -U portal-gun --pre