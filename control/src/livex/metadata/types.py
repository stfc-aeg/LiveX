"""Type hints and dataclasses for MetadataAdapter.

This module implements type hints and dataclasses for use in the LiveX metadata adapter. 

Tim Nicholls, STFC Detector Systems Software Group
"""

import shelve
from dataclasses import dataclass, field, fields
from functools import partial
from typing import Any, Callable, ClassVar, Dict, List, Optional, Tuple, Union

# Type hint for methods taking or returning parameter dictionaries
ParamDict = Dict[str, Any]


@dataclass
class MetadataField:
    """Metadata field data class.

    This dataclass represents a metadata field configured and loaded into metadata adapter.

    Attributes:
        store: class attribute for persistent metadata value storage using a shelf backend
        key: key name of field - required
        label: descriptive text label - required
        default: default value (if not loaded from persistent store) - required
        choices: list of choices for chooser fields - optional
        multi_choice: flag indicating multiple choices allowed - optional
        multi_line: flag indicating text field can be multiple lines in UI - optional
        persist: flag indicating field should be added to persistent store - optional
        user_input: flag indicating field should be exposed for user input - optional
        type: field type, internally generated from default or persistent store value
        value: field value, initialisied from default or from persistent store
    """

    store: ClassVar[Optional[shelve.Shelf]] = None
    key: str
    label: str
    default: Any
    choices: Optional[List[str]] = None
    multi_choice: Optional[bool] = False
    multi_line: Optional[bool] = False
    persist: Optional[bool] = False
    user_input: Optional[bool] = False
    type: str = field(init=False)
    value: Any = field(init=False)

    def __post_init__(self):
        """Post-initialise field.

        This method is called after initialisation of the object. If a persistent store is enabled
        and the field is present in it, the value is initialised to that, otherwise the default it
        used. The type is also determined from the initial value
        """

        # Use the default value for this field if there is no persistent store configured or the
        # field is not present therein
        if not self.persist or self.store is None or self.key not in self.store:
            self.value = self.default

        # Determine the type based on the initial value
        self.type = type(self.value).__name__

    @classmethod
    def set_store(cls, store_file: str) -> None:
        """Set the persistent metadata store.

        This class method sets the metadata persistent store to the file name specified. All
        subseqeuently instantiated fields will use that store to persist their value. This method
        should be called once at the class level (i.e. MetadataField.set_store("file_name")) before
        created metadata fields.

        :param store_file: name of persistent store file to open
        """
        cls.store = shelve.open(store_file, writeback=True)

    @classmethod
    def close_store(cls) -> None:
        """Close the persistent metadata store.

        This class method synchronises and closes the persistent store file.
        """
        if cls.store:
            cls.store.sync()
            cls.store.close()
            cls.store = None

    @property
    def value(self) -> Any:
        """Get the value of the field.

        This property getter method returns the current value of the metadata field. If the field is
        backed by persistent store and present, that value is returned. Otherwise the internally
        stored value is returned.

        :return: the current value of the field
        """
        if self.persist and self.store is not None and self.key in self.store:
            return self.store[self.key]
        else:
            return self._value

    @value.setter
    def value(self, value: Any):
        """Set the value of the field.

        This property setter method sets the currentl value of the field. If the field is backed by
        persistent store the value is set there, otherwise it will be stored internally.
        """
        # Early initialisation of dataclasses seem to set fields to properties, which cannot be
        # pickled into the store and cause an error, so return quietly in that case
        if isinstance(value, property):
            return

        # If persistent storage is enabled for this field and a store is configured, set the value
        # therein, otherwise set internally
        if self.persist and self.store is not None:
            self.store[self.key] = value
        else:
            self._value = value

    def build_accessor(self) -> Dict[str, Tuple[Callable, Union[Callable, None]]]:
        """Build an accessor instance for the field.

        This method builds a ParamterTree-compatible accessor dictionary for the attributes of the
        metadata field, allowing them to be traversed individually within an enclosing tree. The
        value attribute is provided with a setter to allow it to be written; all others are
        read-only.

        :return dictionary of accessor-like tuples for each attribute of the field
        """
        accessor = {}
        for attr in fields(self):
            accessor[attr.name] = (
                partial(getattr, self, attr.name),
                partial(setattr, self, attr.name) if attr.name == "value" else None,
            )

        return accessor
