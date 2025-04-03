from datetime import date, timedelta

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator


def get_tomorrow():
    return date.today() + timedelta(days=1)


class EventsQuery(BaseModel):
    date_from: date = Field(default_factory=get_tomorrow, description='Start date filter', examples=['2025-01-01'])
    date_to: date = Field(default_factory=get_tomorrow, description='End date filter', examples=['2025-12-31'])
    page: int = Field(default=1, ge=1, description='Page number')
    items_count: int = Field(default=20, ge=1, description='Number of items per page')

    model_config = {'extra': 'forbid'}

    @model_validator(mode='after')
    def validate_dates(self):
        tomorrow = get_tomorrow()

        if self.date_from and self.date_from < tomorrow:
            raise HTTPException(status_code=400, detail='date_from cannot be earlier than tomorrow')

        if self.date_to and self.date_to < tomorrow:
            raise HTTPException(status_code=400, detail='date_to cannot be earlier than tomorrow')

        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise HTTPException(status_code=400, detail='date_from cannot be greater than date_to')

        return self
