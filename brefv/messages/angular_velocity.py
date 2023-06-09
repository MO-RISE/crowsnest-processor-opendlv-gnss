# generated by datamodel-codegen:
#   filename:  angular_velocity.json
#   timestamp: 2023-04-28T09:01:10+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class AngularVelocity(BaseModel):
    __root__: List[float] = Field(
        ...,
        description="Angular velocity [Yaw-rate, Pitch-rate, Roll-rate] (rad/s) of a body with respect to the body's BF frame of reference.",
        max_items=3,
        min_items=3,
        title='Angular Velocity',
    )
