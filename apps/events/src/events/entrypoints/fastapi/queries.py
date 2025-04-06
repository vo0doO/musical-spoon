from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator


def truncated_now():
    return datetime.now().replace(second=0, microsecond=0)


class EventsQuery(BaseModel):
    datetime_from: datetime = Field(
        default_factory=truncated_now, description='Start datetime filter', examples=['2025-01-01T00:00']
    )
    datetime_to: datetime | None = Field(default=None, description='End datetime filter', examples=['2025-12-31T00:00'])
    page: int = Field(default=1, ge=1, description='Page number')
    items_count: int = Field(default=20, ge=1, description='Number of items per page')

    model_config = {'extra': 'forbid'}

    @model_validator(mode='after')
    def validate_dates(self):
        now = truncated_now()

        if self.datetime_from and self.datetime_from < now:
            raise HTTPException(status_code=400, detail='datetime_from cannot be earlier than now')

        if self.datetime_to and self.datetime_to < now:
            raise HTTPException(status_code=400, detail='datetime_to cannot be earlier than now')

        if self.datetime_from and self.datetime_to and self.datetime_from > self.datetime_to:
            raise HTTPException(status_code=400, detail='datetime_from cannot be greater than datetime_to')

        return self
