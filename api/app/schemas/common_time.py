from pydantic import BaseModel, Field


class DurationDHM(BaseModel):
    days: int = Field(ge=0, le=30)
    hours: int = Field(ge=0, le=23)
    minutes: int = Field(ge=0, le=59)

    @property
    def total_minutes(self) -> int:
        return self.days * 1440 + self.hours * 60 + self.minutes