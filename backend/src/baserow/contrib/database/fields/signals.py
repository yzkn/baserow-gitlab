from django.dispatch import Signal


field_created = Signal()
field_restored = Signal()
field_updated = Signal()
before_field_deleted = Signal()
field_deleted = Signal()
