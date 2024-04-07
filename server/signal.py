import types
from collections.abc import MutableSequence


class Signal(MutableSequence):
    """
    Tiny pub/sub list implementation

    Partially inspired by:
    - https://github.com/aio-libs/aiosignal/blob/master/aiosignal/__init__.py
    """

    __slots__ = "_items"
    __class_getitem__ = classmethod(types.GenericAlias)

    def __init__(self, items=None):
        if items is not None:
            items = list(items)
        else:
            items = []
        self._items = items

    def __getitem__(self, index):
        return self._items[index]

    def __setitem__(self, index, value):
        self._items[index] = value

    def __delitem__(self, index):
        del self._items[index]

    def __len__(self):
        return self._items.__len__()

    def __iter__(self):
        return self._items.__iter__()

    def __reversed__(self):
        return self._items.__reversed__()

    def __eq__(self, other):
        return list(self) == other

    def __le__(self, other):
        return list(self) <= other

    def insert(self, pos, item):
        self._items.insert(pos, item)

    def __repr__(self):
        return f"<Signal( {self._items!r})>"

    def __hash__(self):
        return hash(tuple(self))

    def safe_remove(self, item):
        if item in self:
            self.remove(item)

    async def send(self, *args, **kwargs):
        for receiver in self:
            await receiver(*args, **kwargs)  # type: ignore
