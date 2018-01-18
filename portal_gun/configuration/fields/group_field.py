from portal_gun.configuration.fields.base_field import BaseField


class GroupField(BaseField):
	def __init__(self, group, is_required):
		BaseField.__init__(self, is_required)
		self._group = group

	def items(self):
		return self._group.items()
