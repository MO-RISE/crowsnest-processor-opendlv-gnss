# generated by datamodel-codegen:
#   filename:  rotation.json
#   timestamp: 2023-04-28T09:01:10+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Rotation(BaseModel):
    __root__: List[float] = Field(
        ...,
        description='A rotation [roll, pitch, yaw] [radians] expressed in the BF frame of reference given as Euler angles according to the YPR convention',
        max_items=3,
        min_items=3,
        title='Rotation',
    )
