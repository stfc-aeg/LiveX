import shelve
from dataclasses import dataclass, field, fields
from functools import partial
from typing import Any, ClassVar, Dict, List, Optional


@dataclass
class MetadataField:
    store: ClassVar[Optional[shelve.Shelf]] = None
    key: str
    label: str
    default: Any
    choices: Optional[List[str]] = None
    multi_choice: Optional[bool] = False
    persist: Optional[bool] = False
    user_input: Optional[bool] = False
    type: str = field(init=False)
    value: Any = field(init=False)

    def __post_init__(self):

        if not self.persist or self.store is None or self.key not in self.store:
            self.value = self.default

        self.type = type(self.value).__name__

    @classmethod
    def set_store(cls, store_file: str):
        cls.store = shelve.open(store_file, writeback=True)

    @classmethod
    def close_store(cls):
        if cls.store:
            cls.store.sync()
            cls.store.close()
            cls.store = None

    @property
    def value(self) -> Any:
        if self.persist and self.store is not None and self.key in self.store:
            return self.store[self.key]
        else:
            return self._value

    @value.setter
    def value(self, value: Any):
        if isinstance(value, property):
            return
        if self.persist and self.store is not None:
            self.store[self.key] = value
        else:
            self._value = value

    def build_accessor(self) -> Dict:
        accessor = {}
        for field in fields(self):
            accessor[field.name] = (
                partial(getattr, self, field.name),
                partial(setattr, self, field.name) if field.name == "value" else None,
            )

        return accessor
