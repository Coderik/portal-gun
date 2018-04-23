.. _overview:

========
Overview
========

**Portal Gun** originates from the necessity to rent some GPU resources for **Deep Learning** and the natural aspiration to save some money. Of course, it might be useful in other use cases involving AWS Spot Instances.

Notice, though, that Portal Gun is not a generic tool. If you need full control over AWS resources from command line, use the `AWS CLI <https://aws.amazon.com/cli/>`_ instead.

.. _concepts:

Concepts
========

Portal
------

Portal Gun was design around the concept of *portals*, hence the name. A portal represents a remote environment and encapsulates such things as a virtual server (Spot Instance) of some type, an operating system of choice, libraries and frameworks, etc.

To *open* a portal means to request a Spot Instance. To *close* a portal means to cancel the request and terminate the instance. For example, if you are training a model, you open a portal for a training session and close it, when the training is finished. If you follow the recommended workflow (:ref:`see bellow <ref-workflow>`), you should be able to open the portal again and find everything exactly like you left it before.

A portal is defined by a *portal specification* file which describes a particular environment in JSON format.

Portal specification includes::
	- characteristics of a Spot Instance to be requested (instance type, key pair for secure connection, security group, availability zone, etc.);
	- software configuration (AMI, extra dependencies to be installed, etc.);
	- persistent data storage (see bellow);
	- data synchronization channels (see bellow).

Persistent Volume
-----------------

AWS Spot Instance are volatile by nature, therefore, some external storage is needed to persist the data. The most efficient option is `EBS Volume <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSVolumes.html?icmpid=docs_ec2_console>`_.

Portal Gun allows you to manage EBS Volumes from command line. It also automatically attaches and mounts volumes to instances according to the portal specifications. You might have a single volume to store everything (dataset, code, checkpoints of training, etc.) or use separate volumes for each type of data.

Channel
-------

*Channels* can be defined in portal specification to synchronize files between a Spot Instance and your local machine. Synchronization is done continuously using ``rsync`` and should be started explicitly with a command. Every channel is either *inbound* (files are moved from remote to local) or *outbound* (files are moved from local to remote).

For instance, you may edit scripts locally and configure a channel to send them to the remote instance after every save. You might configure another channel to automatically get some intermediate results from the remote instance to your local machine for preview. 

.. _ref-workflow:

Typical Workflow
================

A typical Deep Learning workflow with Portal Gun is as follows:
	1. Using Portal Gun create a new volume (e.g. named 'data') for all your data;
	2. Configure a portal backed by the 'data' volume and a non-GPU instance;
	3. Open the portal configured in step 2;
	4. Connect to the non-GPU instance and copy all necessary data to the 'data' volume;
	5. Close the portal configured in step 2;
	6. Configure a portal backed by the 'data' volume and a GPU instance;
	7. Open the portal configured in step 6;
	8. Run training on the GPU instance;
	9. Close the portal configured in step 6.