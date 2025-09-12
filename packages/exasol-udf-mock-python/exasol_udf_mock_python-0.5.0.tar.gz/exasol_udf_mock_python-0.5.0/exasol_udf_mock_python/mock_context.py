from typing import List, Tuple, Iterator, Iterable, Any, Optional, Union
from collections.abc import Sized
from functools import wraps

import pandas as pd

from exasol_udf_mock_python.column import Column
from exasol_udf_mock_python.group import Group
from exasol_udf_mock_python.mock_meta_data import MockMetaData
from exasol_udf_mock_python.udf_context import UDFContext


def check_context(f):
    """
    Decorator checking that a MockContext object has valid current group context.
    Raises a RuntimeError if this is not the case.
    """
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self.no_context:
            raise RuntimeError('Calling UDFContext interface when the current group context '
                               'is invalid is disallowed')
        return f(self, *args, **kwargs)

    return wrapper


def validate_emit(row: Tuple, columns: List[Column]):
    """
    Validates that a data row to be emitted corresponds to the definition of the output columns.
    The number of elements in the row should match the number of columns and the type of each
    element should match the type of the correspondent column. Raises a ValueError if the first
    condition is false or a TypeError if the second condition is false.

    :param row:         Data row
    :param columns:     Column definition.
    """
    if len(row) != len(columns):
        raise ValueError(f"row {row} has not the same number of values as columns are defined")
    for i, column in enumerate(columns):
        if row[i] is not None and not isinstance(row[i], column.type):
            raise TypeError(f"Value {row[i]} ({type(row[i])}) at position {i} is not a {column.type}")


class MockContext(UDFContext):
    """
    Implementation of generic UDF Mock Context interface for a SET UDF with groups.
    This class allows iterating over groups. The functionality of the UDF Context are applicable
    for the current input group.

    Call `next_group` to iterate over groups. The `output_groups` property provides the emit
    output for all groups iterated so far including the output for the current group.

    Calling any function of the UDFContext interface when the group iterator has passed the end
    or before the first call to the `next_group` is illegal and will cause a RuntimeException.
    """

    def __init__(self, input_groups: Iterator[Group], metadata: MockMetaData):
        """
        :param input_groups:    Input groups. Each group object should contain input rows for the group.

        :param metadata:        The mock metadata object.
        """

        self._input_groups = input_groups
        self._metadata = metadata
        """ Mock context for the current group """
        self._current_context: Optional[StandaloneMockContext] = None
        """ Output for all groups """
        self._previous_output: List[Group] = []

    @property
    def no_context(self) -> bool:
        """Returns True if the current group context is invalid"""
        return self._current_context is None

    def next_group(self) -> bool:
        """
        Moves group iterator to the next group.
        Returns False if the iterator gets beyond the last group. Returns True otherwise.
        """

        # Save output of the current group
        if self._current_context is not None:
            self._previous_output.append(Group(self._current_context.output))
            self._current_context = None

        # Try get to the next input group
        try:
            input_group = next(self._input_groups)
        except StopIteration as e:
            return False
        if len(input_group) == 0:
            raise RuntimeError("Empty input groups are not allowed")

        # Create Mock Context for the new input group
        self._current_context = StandaloneMockContext(input_group, self._metadata)
        return True

    @property
    def output_groups(self):
        """
        Output of all groups including the current one.
        """
        if self._current_context is None:
            return self._previous_output
        else:
            groups = list(self._previous_output)
            groups.append(Group(self._current_context.output))
            return groups

    @check_context
    def __getattr__(self, name):
        return getattr(self._current_context, name)

    @check_context
    def get_dataframe(self, num_rows: Union[str, int], start_col: int = 0) -> Optional[pd.DataFrame]:
        return self._current_context.get_dataframe(num_rows, start_col)

    @check_context
    def next(self, reset: bool = False) -> bool:
        return self._current_context.next(reset)

    @check_context
    def size(self) -> int:
        return self._current_context.size()

    @check_context
    def reset(self) -> None:
        self._current_context.reset()

    @check_context
    def emit(self, *args) -> None:
        self._current_context.emit(*args)


def get_scalar_input(inp: Any) -> Iterable[Iterable[Any]]:
    """
    Figures out if the SCALAR parameters are provided as a scalar value or a tuple
    and also if there is a wrapping container around.
    Unless the parameters are already in a wrapping Sized container, returns parameters as an iterable
    wrapped into a one-item list, e.g [(param1, [param2, ...])]. Otherwise, returns the original input.

    :param  inp:        Input parameters.
    """

    if inp is not None:
        if (not isinstance(inp, Iterable)) or isinstance(inp, str):
            return [(inp,)]
        try:
            row1 = next(iter(inp))
            if (not isinstance(row1, Iterable)) or isinstance(row1, str):
                return [inp]
            elif not isinstance(inp, Sized):
                return list(inp)
            else:
                return inp
        except StopIteration:
            pass
    return [tuple()]


class StandaloneMockContext(UDFContext):
    """
    Implementation of generic UDF Mock Context interface a SCALAR UDF or a SET UDF with no groups.

    For Emit UDFs the output in the form of the list of tuples can be
    accessed by reading the `output` property.
    """

    def __init__(self, inp: Any, metadata: MockMetaData):
        """
        :param  inp:        Input rows for a SET UDF or parameters for a SCALAR one.
                            In the former case the input object must be an iterable of rows. This, for example,
                            can be a Group object. It must implement the __len__ method. Each data row must be
                            an indexable container, e.g. a tuple.
                            In the SCALAR case the input can be a scalar value, or tuple. This can also be wrapped
                            in an iterable container, similar to the SET case.

        :param metadata:    The mock metadata object.
        """
        if metadata.input_type.upper() == 'SCALAR':
            self._input = get_scalar_input(inp)
        else:
            self._input = inp
        self._metadata = metadata
        self._data: Optional[Any] = None
        self._iter: Optional[Iterator[Tuple[Any, ...]]] = None
        self._name_position_map = \
            {column.name: position
             for position, column
             in enumerate(metadata.input_columns)}
        self._output = []
        self.next(reset=True)

    @property
    def output(self) -> List[Tuple[Any, ...]]:
        """Emitted output so far"""
        return self._output

    @staticmethod
    def _is_positive_integer(value):
        return value is not None and isinstance(value, int) and value > 0

    def get_dataframe(self, num_rows='all', start_col=0):
        if not (num_rows == 'all' or self._is_positive_integer(num_rows)):
            raise RuntimeError("get_dataframe() parameter 'num_rows' must be 'all' or an integer > 0")
        if not (self._is_positive_integer(start_col) or start_col == 0):
            raise RuntimeError("get_dataframe() parameter 'start_col' must be an integer >= 0")
        if self._data is None:
            return None
        columns_ = [column.name for column in self._metadata.input_columns[start_col:]]

        i = 0
        dfs: list[pd.DataFrame] = []
        while num_rows == 'all' or i < num_rows:
            dfs.append(pd.DataFrame.from_records(
                [self._data[start_col:]], columns=columns_))
            if not self.next():
                break
            i += 1
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
            df.reset_index(inplace=True, drop=True)
            return df
        return None

    def __getattr__(self, name):
        return None if self._data is None else self._data[self._name_position_map[name]]

    def next(self, reset: bool = False):
        if self._iter is None or reset:
            self.reset()
        else:
            try:
                new_data = next(self._iter)
                self._data = new_data
                validate_emit(self._data, self._metadata.input_columns)
                return True
            except StopIteration as e:
                self._data = None
                return False

    def size(self):
        return len(self._input)

    def reset(self):
        self._iter = iter(self._input)
        self.next()

    def emit(self, *args):
        if len(args) == 1 and isinstance(args[0], pd.DataFrame):
            tuples = [tuple(x) for x in args[0].astype('object').values]
        else:
            tuples = [args]
        for row in tuples:
            validate_emit(row, self._metadata.output_columns)
        self._output.extend(tuples)
