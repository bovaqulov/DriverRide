from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, model_validator


class TariffService(BaseModel):
    id: int | None = None
    title: str | None = None
    translate: dict | None = None
    is_active: bool | None = None


class CarService(BaseModel):
    id: int | None = None
    driver_id: int | None = None
    car_number: str = ''
    car_model: str = ''
    car_color: str = ''
    tariff: TariffService | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CityService(BaseModel):
    city_id: int | None = None
    title: str | None = None
    translate: dict | None = None


class RouteService(BaseModel):
    route_id: int | None = None
    from_city: dict | None = None
    to_city: dict | None = None


class DriverTransactionService(BaseModel):
    id: int | None = None
    driver_id: int | None = None
    amount: float = 0.0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DriverService(BaseModel):
    id: int | None = None
    telegram_id: int | None = None
    full_name: str | None = None
    total_rides: int | None = None
    phone: str | None = None
    from_location: dict = {}
    to_location: dict = {}
    route_id: RouteService | None = None
    car_class: str | None = None
    rating: int | None = None
    status: str = 'offline'
    amount: int = 150000
    cars: list[CarService] = []
    full_profile_image_url: str = ""

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def _parse_api_response(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if isinstance(data.get('route_id'), dict):
            route = data['route_id']
            data['from_location'] = route.get('from_city', {})
            data['to_location'] = route.get('to_city', {})
        cars = data.get('cars', [])
        if cars and isinstance(cars[0], dict):
            tariff = cars[0].get('tariff')
            if isinstance(tariff, dict):
                data['car_class'] = tariff.get('title')
        return data
