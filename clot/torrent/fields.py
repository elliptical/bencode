"""This module implements descriptors to handle torrent fields."""


from datetime import datetime

from .validators import Bounded, Encoded, NonEmpty, Typed, UnixEpoch, ValidUrl


class Layout(type):
    """Metaclass providing methods to load and save all fields at once."""

    def __new__(cls, name, bases, mapping):
        """Create the class after expanding the original mapping."""
        fields = [value for value in mapping.values() if isinstance(value, Field)]

        def load_fields(self):
            for field in self._fields:
                field.loaded = False

            for field in self._fields:
                # The "encoding" and "codepage" fields are indirectly loaded right
                # before loading the first encoded field.  Prevent them from being
                # loaded again; otherwise the instance data dictionary will already
                # have the associated key popped and field values become None.
                if not field.loaded:
                    field.load_from(self)

        def save_fields(self):
            for field in self._fields:
                field.save_to(self)

        new_stuff = {
            '_fields': fields,
            load_fields.__name__: load_fields,
            save_fields.__name__: save_fields,
        }

        for key in new_stuff:
            if key in mapping:
                raise TypeError(f'{name!r} already has the {key!r} attribute')

        mapping.update(new_stuff)

        return super().__new__(cls, name, bases, mapping)


class Field(Typed):
    """Field with specific type and unrestricted values, including None."""

    def __init__(self, key, value_type, **kwargs):
        """Initialize self."""
        self.key = key
        self.loaded = None
        super().__init__(value_type, **kwargs)

    def __set_name__(self, owner, name):
        """Customize the name used to store the field value."""
        # pylint: disable=attribute-defined-outside-init
        self.name = name
        self.private_name = '_' + name

    def __get__(self, instance, owner=None):
        """Return the field value from the specified instance (or the descriptor itself)."""
        if instance is None:
            return self

        try:
            return getattr(instance, self.private_name)
        except AttributeError:
            return self.load_from(instance)

    def __set__(self, instance, value):
        """Set the field value in the specified instance."""
        if value is not None:
            self.validate(value)
        setattr(instance, self.private_name, value)

    def load_from(self, instance):
        """Initialize the field value from the instance data dictionary."""
        try:
            value = self.extract_value(instance)
        except KeyError:
            value = None
        else:
            self.validate(value)
            del instance.data[self.key]

        self.loaded = True
        setattr(instance, self.private_name, value)
        return value

    def save_to(self, instance):
        """Update the instance data dictionary with the field value."""
        try:
            value = getattr(instance, self.private_name)
        except AttributeError:
            pass
        else:
            if value is None:
                instance.data.pop(self.key, None)
            else:
                instance.data[self.key] = value


class Integer(Field, Bounded):
    """Integer field with optional lower and/or upper bounds."""

    def __init__(self, key, **kwargs):
        """Initialize self."""
        super().__init__(key, int, **kwargs)


class Bytes(Field, NonEmpty):
    """Bytes field with non-empty value."""

    def __init__(self, key, **kwargs):
        """Initialize self."""
        super().__init__(key, bytes, **kwargs)


class String(Field, Encoded, NonEmpty):
    """String field with nonempty value (stored as bytes)."""

    def __init__(self, key, **kwargs):
        """Initialize self."""
        super().__init__(key, str, **kwargs)


class Url(String, ValidUrl):    # pylint: disable=too-many-ancestors
    """String field looking like an URL (non-empty scheme and hostname required)."""


class Timestamp(Field, UnixEpoch, Bounded):
    """Timestamp field with required timezone info."""

    def __init__(self, key, **kwargs):
        """Initialize self."""
        super().__init__(key, datetime, **kwargs)