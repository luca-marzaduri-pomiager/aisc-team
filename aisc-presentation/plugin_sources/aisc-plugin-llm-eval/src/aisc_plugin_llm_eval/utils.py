from operator import itemgetter
from typing import Any, Sequence

from aisc_plugin_interface import Measure, metric


def add_metrics(cls):
    """Class decorator that automatically adds @metric decorated export methods."""

    # NOTE: metric_names is a class method
    for name in cls.metric_names():

        @metric(name)
        def fct(
            self, evaluation_output: list[dict[str, float | None]], _name=name
        ) -> list[Measure]:
            measures = []
            for i, sample in enumerate(evaluation_output):
                score = sample.get(_name, None)
                if score is not None:
                    measures.append(
                        Measure(
                            name=_name,
                            score=score,
                            description=str(i) if len(evaluation_output) > 1 else None,
                        )
                    )
            return measures

        setattr(cls, f"export_metric_{name}", fct)

    return cls


def get_items(
    obj: Sequence[Any],
    *indices: int,
    batch: bool = False,
) -> tuple[Any, ...] | tuple[tuple[Any, ...], ...]:
    """
    Parameters
    ----------
    obj : sequence
        Source sequence
    *indices : int
        Indices to extract
    batch : bool
        Controls the shape of the returned data.

        If False (default):
            Returns a flat tuple containing the selected elements,
            preserving their original order.

        If True:
            Interprets each selected element as a row and returns
            a tuple of columns (i.e. the transpose of the rows).

    Examples
    --------
    >>> data = [(1, "a"), (2, "b"), (3, "c")]

    # get_subsequence behavior
    >>> get_items(data, 0, 2)
    (1, 3)

    >>> get_items(data, 1)
    (2,)

    # get_batch behavior
    >>> get_items(data, 0, 2, batch=True)
    ((1, 3), ('a', 'c'))

    >>> get_items(data, 1, batch=True)
    ((2,), ('b',))
    """

    if not indices:
        return ()

    items = itemgetter(*indices)(obj)

    # normalize itemgetter behavior
    if len(indices) == 1:
        items = (items,)

    if not batch:
        return items

    # batch mode: transpose rows -> columns
    if not isinstance(items[0], tuple):
        items = (items,)

    return tuple(zip(*items))
