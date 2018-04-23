.. _commands:

========
Commands
========

Print top-level help message::

    $ portal -h

Add ``-h`` (or ``--help``) flag after commands and command groups to print corresponding help messages. For instance, print help message for the ``volume`` group including the list of commands::

    $ portal volume -h

**Top-level command options:**

.. cmdoption:: -c CONFIG, --config CONFIG

    Set name and location of configuration file.

.. _volume_cmd:

Persistent Volumes
==================

This section documents a group of commands that are used to manage persistent volumes. For information on how to configure attachment of persistent volumes to instances see :ref:`Portal Specification <portal_spec>` section.

Create
------

Create a new EBS volume::

	$ portal volume create

Every volume requires **size** (in Gb) and **availability zone** to be specified. **Name** is optional, but recommended. If these three properties are not set using the command options, they will be requested from the standard input.

Upon successful creation of a new volume its ``<Volume-Id>`` will be provided.

**Command options:**

.. cmdoption:: -n NAME, --name NAME

    Set name for new volume.

.. cmdoption:: -s SIZE, --size SIZE

    Set size (in Gb) for new volume.

.. cmdoption:: -z ZONE, --zone ZONE

    Set availability zone for new volume.

.. cmdoption:: -S SNAPSHOT, --snapshot SNAPSHOT

    Set Id of a snapshot to create new volume from.

.. cmdoption:: -t key:value [key:value ...], --tags key:value [key:value ...]

    Set user tags for new volume.

List
----

List existing EBS volume::

	$ portal volume list

By default ``list`` command outputs only the volumes created by Portal Gun on behalf of the current AWS user. To list all volumes use ``-a`` flag.

**Command options:**

.. cmdoption:: -a, --all

    Show all volumes, not only ones created by Portal Gun.

Update
------

Update an AWS volume::

	$ portal volume update <Volume-Id>

**Command options:**

.. cmdoption:: -n NAME, --name NAME

    Update name of volume.

.. cmdoption:: -s SIZE, --size SIZE

    Update size of volume.

.. cmdoption:: -t key:value [key:value ...], --tags key:value [key:value ...]

    Add user tags for volume.

Delete
------

Delete an AWS volume::

	$ portal volume delete <Volume-Id>

By default ``delete`` command deletes only the volumes created by Portal Gun on behalf of the current AWS user. To force deletion of a volume use ``-f`` flag.

**Command options:**

.. cmdoption:: -f, --force

    Delete any volume, even not owned.

----

.. _portal_cmd:

Portals
=======

*Portal* is the main concept of the Portal Gun (see :ref:`Concepts <concepts>` for details). 

Init
----

Create a draft *portal specification* file::

    $ portal init <Portal-Name>

A file with the name ``<Portal-Name>.json`` will be created. Modify this file to set the appropriate values. **TODO: add link to spec doc**

Open
----

To open a portal means to request and configure a Spot Instance according to the *portal specification*. Open a portal::

    $ portal open <Portal-Name>

Ssh
---

Once the portal is opened, connect to the remote instance via ssh::

    $ portal ssh <Portal-Name>

For long-running tasks like training a model it is particularly useful to be able to close current ssh session without interrupting the running task. One way of achieving this is offered by ``tmux``. "It lets you switch easily between several programs in one terminal, detach them (they keep running in the background) and reattach them to a different terminal." - tmux `wiki <https://github.com/tmux/tmux/wiki>`_. You can run ``tmux`` within ssh session and then run the long task within ``tmux`` session. Portal Gun allows you to use tmux session automatically with ``-t`` command option.

**Command options:**

.. cmdoption:: -t [session], --tmux [session]

    Automatically open tmux session upon connection. Default session name is `portal`.

Info
----

Check information about a portal::

    $ portal info <Portal-Name>

Information includes portal status (open or closed). If portal is open, information about the instance and attached volumes is provided.

When Portal Gun is used in a shell script, it might be useful to get specific bits of information without the rest of the output. In this case use command option ``-f`` to get the value of one particular field. Supported fields are:

* name - portal name;
* status - portal status (open or close);
* id - instance id;
* type - instance type;
* user - remote user;
* host - remote host;
* ip - public IP of instance;
* remote - user@host
* key - local ssh key file

For instance, to copy a file from remote instance to local machine you can use Portal Gun to look up connection details::

    $ scp -i "`portal info <Portal-Nane> -f key`" `portal info <Portal-Nane> -f remote`:/path/to/file /local/folder/

**Command options:**

.. cmdoption:: -f FIELD, --field FIELD

    Print value for a specified field (name, status, id, type, user, host, ip, remote, key).

Close
-----

To close a portal means to cancel a Spot Instance request and terminate the instance itself. Close a portal::

    $ portal close <Portal-Name>

----

.. _channel_cmd:

Channels
========

Channels are used to sync remote and local folders. A channel has direction, source and target folders, and other properties. Every channel belongs to a portal and should be configured in the corresponding portal specification file (see :ref:`Portal Specification <portal_spec>` for details). 

Channel
-------

Start syncing specified folders::

    $ portal channel <Portal-Name>

Synchronization of files over the channels is done continuously using ``rsync``. Data transfer happens every time a new file appears or an existing file is changed in the source folder.

To stop synchronization press ``^C``.