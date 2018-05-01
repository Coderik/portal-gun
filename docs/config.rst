.. _config:

=============
Configuration
=============

Application Config
==================

Portal Gun reads basic configuration from a file in JSON format. By default it looks for a file named ``config.json`` in the following locations (in that order):

1. script running path
2. ``~/.portal-gun/``

When Portal Gun is installed in a virtual Python environment (recommended), script running path is ``/virtual-env-path/bin/``.

A custom location and filename may be specified using ``-c, --config`` argument.

----

Values to set in the configuration file:

.. code-block:: json

	{
		"aws_region": "current AWS region",
		"aws_access_key": "access key for your AWS account",
		"aws_secret_key": "secret key for your AWS account"
	}

Credentials (access and secret keys) for programmatic access on behalf of your AWS account can be found in the `IAM Console <https://console.aws.amazon.com/iam/home>`_. **It is recommended to create a separate user** for programmatic access via Portal Gun.

AWS Access Rights
=================

Portal Gun requires the following access rights::

	iam:PassRole

	ec2:DescribeAccountAttributes

	ec2:DescribeAvailabilityZones
	ec2:DescribeSubnets

	ec2:CreateVolume
	ec2:ModifyVolume
	ec2:AttachVolume
	ec2:DetachVolume
	ec2:DeleteVolume
	ec2:DescribeVolumes
	ec2:DescribeVolumeStatus
	ec2:DescribeVolumeAttribute
	ec2:DescribeVolumesModifications

	ec2:RequestSpotFleet
	ec2:CancelSpotFleetRequests
	ec2:RequestSpotInstances
	ec2:CancelSpotInstanceRequests
	ec2:ModifySpotFleetRequest
	ec2:ModifyInstanceAttribute
	ec2:DescribeSpotFleetRequests
	ec2:DescribeSpotInstanceRequests
	ec2:DescribeSpotFleetInstances
	ec2:DescribeSpotPriceHistory
	ec2:DescribeSpotFleetRequestHistory
	ec2:DescribeInstances
	ec2:DescribeInstanceStatus
	ec2:DescribeInstanceAttribute

	ec2:CreateTags
	ec2:DeleteTags
	ec2:DescribeTags

`IAM Policy <https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html>`_ is the most convenient way to grant required permissions.
Create a new policy and attach it to a user which will be used for programmatic access via Portal Gun.

Reference policy granting required permissions can be found `here <_static/reference_policy.json>`_. You can make it more strict, for instance, by limiting access right to a particular region.

Additional Resources
====================

- `Controlling Access Using Policies <https://docs.aws.amazon.com/IAM/latest/UserGuide/access_controlling.html>`_