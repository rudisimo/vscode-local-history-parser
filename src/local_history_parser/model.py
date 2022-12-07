from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import fields
from typing import Any, Mapping

from .util import dict_factory


@dataclass
class ExtendedDataclass:
    """
    Dataclass with extended functionality for importing/exporting data from dictionaries.
    """

    @classmethod
    def from_dict(cls, obj: Mapping[str, Any], *init_args: Any, **init_kwargs: Any):
        field_names = set([f.name for f in fields(cls)])
        field_values = {k: v for k, v in obj.items() if k in field_names}

        return cls(*init_args, **init_kwargs, **field_values)

    def to_dict(self) -> Mapping[str, Any]:
        return asdict(self, dict_factory=dict_factory)
