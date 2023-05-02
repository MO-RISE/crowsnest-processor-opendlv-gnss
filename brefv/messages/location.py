# generated by datamodel-codegen:
#   filename:  location.json
#   timestamp: 2023-04-28T09:01:10+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Location(BaseModel):
    __root__: List[float] = Field(
        ...,
        description='A location [x, y, z] [m] relative to a body�s geometric center, expressed in the BF frame of reference',
        max_items=3,
        min_items=3,
        title='Location',
    )
