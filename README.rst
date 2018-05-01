==========
Portal Gun
==========

Command line tool that automates routine tasks associated with the management of Spot Instances on Amazon EC2 service.

Documentation
=============

Full documentation can be found at `http://portal-gun.readthedocs.io <http://portal-gun.readthedocs.io>`_.

Installation
============

It is **strongly recommended** to install Portal Gun in **a virtual Python environment**.

To install the latest stable version from the PyPI::

    $ pip install -U portal-gun

To install the latest pre-release version from the PyPI::

    $ pip install -U portal-gun --pre

Refer to the documentation for details regarding `general configuration <http://portal-gun.readthedocs.io/en/stable/config.html>`_
and `portal specification <http://portal-gun.readthedocs.io/en/stable/portal_spec.html>`_.

Basic Usage
===========

1. Persistent volumes
---------------------

Use ``volume`` group of commands to work with EBS volumes.

Create a new volume::

    $ portal volume create

List created volumes::

    $ portal volume list

Update previously created volume::

    $ portal volume update <Volume-Id> [-n <New-Name>] [-s <New-Size>]

Delete previously created volume::

    $ portal volume delete <Volume-Id>

2. Portals
----------

Create draft specification for a new portal::

    $ portal init <Portal-Name>

Open a portal (request a new Spot Instance)::

    $ portal open <Portal-Name>

Connect to the Spot Instance via ssh::

    $ portal ssh <Portal-Name>

Connect to the Spot Instance via ssh and attach to a tmux session (session name is optional)::

    $ portal ssh <Portal-Name> -t [<Session-Name>]

Close opened portal (cancel Spot Instance request)::

    $ portal close <Portal-Name>

Get information about a portal::

    $ portal info <Portal-Name>


3. Channels
-----------

Start syncing files across the channels configured for a portal::

    $ portal channel <Portal-Name>

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/Coderik/portal-gun/blob/master/LICENSE>`_ file for details.