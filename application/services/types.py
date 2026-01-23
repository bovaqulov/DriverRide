from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class DriverService(BaseModel):
    id: Optional[int] = None
    telegram_id: Optional[int] = None
    full_name: Optional[str] = None
    total_rides: Optional[int] = None
    phone: Optional[str] = None
    from_location: dict = {}
    to_location: dict = {}
    route_id: Optional["RouteService"] = None
    car_class: Optional[str] = None
    rating: Optional[int] = None
    status: str = 'offline'  # Default offline holati
    amount: int = 150000  # Integer tipida
    cars: List['CarService'] = []  # CarService obyektlar ro'yxati
    full_profile_image_url: str = ""

    class Config:
        from_attributes = True


@dataclass
class CityService:
    city_id: Optional[int] = None
    title: Optional[str] = None
    translate: Optional[dict] = None


@dataclass
class RouteService:
    route_id: Optional[int] = None
    from_city: Optional[CityService] = None
    to_city: Optional[CityService] = None


@dataclass
class TariffService:
    id: Optional[int] = None
    title: Optional[str] = None
    translate: Optional[dict] = None
    is_active: Optional[bool] = None



@dataclass
class CarService:
    id: Optional[int] = None
    driver_id: Optional[int] = None
    car_number: str = ''
    car_model: str = ''
    car_color: str = ''
    tariff: Optional[TariffService] = None  # Yangi qo'shildi
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        # API dan kelgan ma'lumotlarni qayta ishlash
        if isinstance(self.tariff, dict):
            self.tariff = TariffService(**self.tariff) if self.tariff else None


@dataclass
class DriverTransactionService:
    id: Optional[int] = None
    driver_id: Optional[int] = None
    amount: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# DriverService uchun konvertatsiya funksiyasi
def convert_api_response_to_driver_service(api_response: dict) -> DriverService:
    """API javobini DriverService obyektiga aylantiradi"""

    # Routedan shahar nomlarini olish
    from_location = {}
    to_location = {}

    if api_response.get('route_id'):
        route_id = RouteService(route_id=api_response.get('route_id', {}).get("route_id"))
        route = api_response['route_id']
        if route.get('from_city'):
            from_location = route['from_city']
        if route.get('to_city'):
            to_location = route['to_city']
    else:
        route_id = RouteService(route_id=0)
    # Mashinalarni konvertatsiya qilish
    cars = []
    for car_data in api_response.get('cars', []):
        car = CarService(
            id=car_data.get('id'),
            car_number=car_data.get('car_number', ''),
            car_model=car_data.get('car_model', ''),
            car_color=car_data.get('car_color', ''),
            tariff=car_data.get('tariff')
        )
        cars.append(car)

    # Car class ni aniqlash (birinchi mashinaning tariffi asosida)
    car_class = None
    if cars and cars[0].tariff:
        car_class = cars[0].tariff.title

    # DriverService obyektini yaratish
    driver = DriverService(
        id=api_response.get('id'),
        telegram_id=api_response.get('telegram_id'),
        full_name=api_response.get('full_name'),
        total_rides=api_response.get('total_rides', 0),
        phone=api_response.get('phone'),
        from_location=from_location,
        to_location=to_location,
        car_class=car_class,
        route_id=route_id,
        rating=api_response.get('rating', 5),
        status=api_response.get('status', 'offline'),
        amount=api_response.get('amount', 150000),
        cars=cars,
        full_profile_image_url=api_response.get('full_profile_image_url', '')
    )

    return driver
