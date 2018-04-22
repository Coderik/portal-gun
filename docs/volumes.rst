.. _volumes:

==================
Persistent Volumes
==================

This section documents commands that are used to manage persistent volumes. For information on how to configure attachment of persistent volumes to instances see :ref:`Portals - Specification <portal-spec>` section.

Commands
========

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

.. cmdoption:: -f, --force

    Delete any volume, even not owned.
