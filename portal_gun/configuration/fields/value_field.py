from portal_gun.configuration.fields.base_field import BaseField


class ValueField(BaseField):
	def __init__(self, field_type, is_required):
		BaseField.__init__(self, is_required)
		self._field_type = field_type

	def field_type(self):
		return self._field_type

	def __str__(self):
		return '{}|{}'.format(self._field_type.__name__, 'required' if self._is_required else 'optional')

	__repr__ = __str__
