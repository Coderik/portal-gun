from portal_gun.configuration.fields.value_field import ValueField
from portal_gun.configuration.fields.group_field import GroupField


def vf(field_type, is_required):
	""" Make Value Field. """
	return ValueField(field_type, is_required)


def sf(is_required):
	""" Make String Field. """
	return ValueField(field_type=unicode, is_required=is_required)


def rsf():
	""" Make required String Field. """
	return ValueField(field_type=unicode, is_required=True)


def osf():
	""" Make optional String Field. """
	return ValueField(field_type=unicode, is_required=False)


def bf(is_required):
	""" Make Bool Field. """
	return ValueField(field_type=bool, is_required=is_required)


def rbf():
	""" Make required Bool Field. """
	return ValueField(field_type=bool, is_required=True)


def obf():
	""" Make optional Bool Field. """
	return ValueField(field_type=bool, is_required=False)


def gf(group, is_required):
	""" Make Group Field. """
	return GroupField(group, is_required)


def rgf(group):
	""" Make required Group Field. """
	return GroupField(group, is_required=True)


def ogf(group):
	""" Make optional Group Field. """
	return GroupField(group, is_required=False)

# Expose shortcut making functions
__all__ = ['vf', 'sf', 'rsf', 'osf', 'bf', 'rbf', 'obf', 'gf', 'rgf', 'ogf']
