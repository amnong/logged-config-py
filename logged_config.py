import collections
import logging
import copy


class LoggedConfiguration(collections.Mapping):
    def __init__(self, name, data):
        self._name = name
        self._data = {
            key: wrap_logged_config_value('%s.%s' % (self._name, key), item)
            for key, item in data.items()}
        self._logger = logging.getLogger(name)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._logger.info('Configuration "%s": setting %r to %r', self._name, key, value)
        value = wrap_logged_config_value('%s.%s' % (self._name, key), value)
        self._data[key] = value

    def __delitem__(self, key):
        self._logger.info('Configuration "%s": removing %r', self._name, key)
        del self._data[key]

    def __contains__(self, item):
        return item in self._data

    def __getattr__(self, attr):
        try:
            return self._data[attr]
        except KeyError:
            raise AttributeError('No such configuration attribute: %r' % attr) from None

    def __setattr__(self, attr, value):
        if attr in ('_name', '_data', '_logger'):
            super().__setattr__(attr, value)
            return
        self[attr] = value

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        return copy.copy(self)

    def __copy__(self):
        return type(self)('%s(copy)' % self._name, self._data)

    def __deepcopy__(self, memo):
        return type(self)('%s(copy)' % self._name, copy.deepcopy(self._data, memo))

    def to_dict(self):
        return _unwrap(self)

    def __repr__(self):
        return '{}({!r}, {!r})'.format(type(self).__name__, self._name, self._data)


class LoggedList(list):
    def __init__(self, name, data):
        self._name = name
        super().__init__((
            wrap_logged_config_value('%s[...]' % self._name, element)
            for element in data
            ))
        self._logger = logging.getLogger(name)

    def append(self, value):
        self._logger.info('Configuration "%s": appending %r', self._name, value)
        value = wrap_logged_config_value('%s[...]' % self._name, value)
        return super().append(value)

    def remove(self, value):
        self._logger.info('Configuration "%s": removing %r', self._name, value)
        return super().remove(value)

    def insert(self, index, value):
        self._logger.info('Configuration "%s": inserting %r at index %s', self._name, value, index)
        value = wrap_logged_config_value('%s[...]' % self._name, value)
        return super().insert(index, value)

    def pop(self, index):
        self._logger.info('Configuration "%s": popping from index %s', self._name, index)
        return super().pop(index)

    def clear(self):
        self._logger.info('Configuration "%s": clearing all values', self._name)
        return super().clear()

    def extend(self, iterable):
        self._logger.info('Configuration "%s": extending with %r', self._name, iterable)
        iterable = (wrap_logged_config_value('%s[...]' % self._name, value)
                    for value in iterable)
        return super().extend(iterable)

    def __copy__(self):
        return type(self)('%s(copy)' % self._name, self)

    def __deepcopy__(self, memo):
        return type(self)('%s(copy)' % self._name, (copy.deepcopy(item, memo) for item in self))

    def __repr__(self):
        return '{}({!r}, {})'.format(type(self).__name__, self._name, super().__repr__())


class LoggedSet(set):
    def __init__(self, name, data):
        self._name = name
        super().__init__((
            wrap_logged_config_value('%s[...]' % self._name, element)
            for element in data
            ))
        self._logger = logging.getLogger(name)

    def add(self, value):
        self._logger.info('Configuration "%s": adding %r', self._name, value)
        return super().add(value)

    def clear(self):
        self._logger.info('Configuration "%s": clearing all values', self._name)
        return super().clear()

    def difference_update(self, value):
        self._logger.info('Configuration "%s": difference-update with %r', self._name, value)
        return super().difference_update(value)

    def discard(self, value):
        self._logger.info('Configuration "%s": discarding %r (if present)', self._name, value)
        return super().discard(value)

    def pop(self, value):
        self._logger.info('Configuration "%s": popping %r', self._name, value)
        return super().pop(value)

    def remove(self, value):
        self._logger.info('Configuration "%s": removing %r', self._name, value)
        return super().remove(value)

    def symmetric_difference_update(self, value):
        self._logger.info('Configuration "%s": symmetric-difference-update with %r', self._name, value)
        return super().symmetric_difference_update(value)

    def update(self, value):
        self._logger.info('Configuration "%s": updating with %r', self._name, value)
        return super().update(value)

    def __copy__(self):
        return type(self)('%s(copy)' % self._name, self)

    def __deepcopy__(self, memo):
        return type(self)('%s(copy)' % self._name, (copy.deepcopy(item, memo) for item in self))

    def __repr__(self):
        return '{}({!r}, {})'.format(type(self).__name__, self._name, super().__repr__())


def wrap_logged_config_value(config_name, value):
    if isinstance(value, (list, tuple)):
        value = LoggedList(config_name, value)
    elif isinstance(value, set):
        value = LoggedSet(config_name, value)
    elif isinstance(value, dict):
        value = LoggedConfiguration(config_name, value)
    return value


def _unwrap(value, replace_sets_with_lists=False):
    if isinstance(value, LoggedConfiguration):
        return {k: _unwrap(v, replace_sets_with_lists) for k, v in value.items()}
    if isinstance(value, LoggedList) or replace_sets_with_lists and isinstance(value, LoggedSet):
        return [_unwrap(v, replace_sets_with_lists) for v in value]
    if isinstance(value, LoggedSet):
        return {_unwrap(v, replace_sets_with_lists) for v in value}
    return value
