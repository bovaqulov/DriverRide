from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UserService:
    """Telegram user model"""
    telegram_id: int
    username: Optional[str] = None
    full_name: str = ""
    phone: Optional[str] = None
    language: str = "uz"
    is_active: bool = True
    is_banned: bool = False
    total_rides: int = 0
    rating: float = 5.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class DriverService:
    id: Optional[int] = None
    telegram_id: Optional[int] = None
    from_location: str = ''
    to_location: str = ''
    status: str = 'online'
    amount: float = 0.0

@dataclass
class CarService:
    id: Optional[int] = None
    driver_id: Optional[int] = None
    car_number: str = ''
    car_model: str = ''
    car_color: str = ''
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class DriverTransactionService:
    id: Optional[int] = None
    driver_id: Optional[int] = None
    amount: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None