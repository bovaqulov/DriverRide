from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class PassengerTypes:
    id: int
    telegram_id: int
    language: str
    full_name: str
    total_rides: int
    phone: str
    rating: float


@dataclass
class CarsTypes:
    id: int
    car_number: str
    car_model: str
    car_color: str
    car_class: str


@dataclass
class LocationTypes:
    longitude: float
    latitude: float


@dataclass
class AddressType:
    city: str
    location: Optional[LocationTypes] = None


class OrderStatus(str, Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    ARRIVED = "arrived"
    STARTED = "started"
    ENDED = "ended"
    REJECTED = "rejected"


@dataclass
class DriverDetailsTypes:
    id: int
    telegram_id: int
    full_name: str
    total_rides: int
    phone: str
    rating: float
    from_location: str
    to_location: str
    status: str
    amount: float
    cars: List[CarsTypes] = field(default_factory=list)
    status_display: str = ""
    profile_image: str = ""
    full_profile_image_url: str = ""


@dataclass
class ContentObjectTypes:
    type: str
    id: int
    from_location: Dict[str, Any]  # JSON sifatida keladi
    to_location: Dict[str, Any]  # JSON sifatida keladi
    price: str
    created_at: datetime
    travel_class: Optional[str] = None
    rate: float = 5.0
    passenger: int = 1  # float emas, int bo'lishi kerak
    has_woman: bool = False


@dataclass
class OrderTypes:
    id: int
    user: int
    creator: PassengerTypes
    driver: Optional[int] = None
    driver_details: Optional[DriverDetailsTypes] = None
    status: str = OrderStatus.CREATED.value
    order_type: str = ""
    content_object: Optional[ContentObjectTypes] = None
    content_type_name: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderTypes':
        """Dictionary dan OrderTypes obyektini yaratish"""
        data = data.copy()

        # Creator ni qayta ishlash
        creator_data = data.pop('creator', {})
        creator = PassengerTypes(**creator_data) if creator_data else None

        # Driver details ni qayta ishlash
        driver_details_data = data.pop('driver_details', None)
        driver_details = None
        if driver_details_data:
            cars_data = driver_details_data.pop('cars', [])
            cars = [CarsTypes(**car) for car in cars_data] if cars_data else []
            driver_details = DriverDetailsTypes(cars=cars, **driver_details_data)

        # Content object ni qayta ishlash
        content_object_data = data.pop('content_object', None)
        content_object = None
        if content_object_data:
            # from_location va to_location ni AddressType ga o'tkazish
            from_location_data = content_object_data.get('from_location', {})
            to_location_data = content_object_data.get('to_location', {})

            # LocationTypes ni yaratish
            from_location_obj = None
            to_location_obj = None

            if from_location_data and isinstance(from_location_data, dict):
                location_data = from_location_data.get('location')
                if location_data:
                    from_location_obj = AddressType(
                        city=from_location_data.get('city', ''),
                        location=LocationTypes(**location_data) if isinstance(location_data, dict) else None
                    )

            if to_location_data and isinstance(to_location_data, dict):
                location_data = to_location_data.get('location')
                if location_data:
                    to_location_obj = AddressType(
                        city=to_location_data.get('city', ''),
                        location=LocationTypes(**location_data) if isinstance(location_data, dict) else None
                    )

            # created_at ni qayta ishlash
            created_at_str = content_object_data.get('created_at', '')
            created_at = None
            if created_at_str:
                try:
                    if created_at_str.endswith('Z'):
                        created_at = datetime.fromisoformat(
                            created_at_str.replace('Z', '+00:00')
                        )
                    else:
                        created_at = datetime.fromisoformat(created_at_str)
                except (ValueError, AttributeError):
                    created_at = datetime.now()

            # Boshqa field'larni olish
            content_object = ContentObjectTypes(
                type=content_object_data.get('type', ''),
                id=content_object_data.get('id', 0),
                from_location=from_location_data,  # Original JSON saqlanadi
                to_location=to_location_data,  # Original JSON saqlanadi
                price=content_object_data.get('price', ''),
                created_at=created_at or datetime.now(),
                travel_class=content_object_data.get('travel_class'),
                rate=float(content_object_data.get('rate', 5.0)),
                passenger=int(content_object_data.get('passenger', 1)),
                has_woman=bool(content_object_data.get('has_woman', False))
            )

        # Qolgan field'larni olish
        status = data.pop('status', OrderStatus.CREATED.value)
        order_type = data.pop('order_type', '')
        content_type_name = data.pop('content_type_name', '')
        order_id = data.pop('id', 0)
        user = data.pop('user', 0)
        driver = data.pop('driver', None)

        return cls(
            id=order_id,
            user=user,
            driver=driver,
            creator=creator,
            driver_details=driver_details,
            content_object=content_object,
            status=status,
            order_type=order_type,
            content_type_name=content_type_name,
            **data
        )

    @property
    def from_city(self) -> str:
        """From location shahar nomini qaytarish"""
        if self.content_object and isinstance(self.content_object.from_location, dict):
            return self.content_object.from_location.get('city', '')
        return ""

    @property
    def to_city(self) -> str:
        """To location shahar nomini qaytarish"""
        if self.content_object and isinstance(self.content_object.to_location, dict):
            return self.content_object.to_location.get('city', '')
        return ""

    @property
    def formatted_price(self) -> str:
        """Narxni formatlangan holda qaytarish"""
        if self.content_object:
            return f"{self.content_object.price} so'm"
        return ""

    @property
    def status_enum(self) -> OrderStatus:
        """Statusni Enum sifatida qaytarish"""
        try:
            return OrderStatus(self.status)
        except ValueError:
            return OrderStatus.CREATED


from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


@dataclass
class DriverInfo:
    id: int
    telegram_id: int
    username: str
    full_name: str
    language: str
    is_banned: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DriverInfo':
        """Dictionary dan DriverInfo obyektini yaratish"""
        data = data.copy()

        # Datetime field'larini konvert qilish
        for field_name in ['created_at', 'updated_at']:
            if field_name in data:
                value = data[field_name]
                if isinstance(value, str):
                    try:
                        if value.endswith('Z'):
                            data[field_name] = datetime.fromisoformat(
                                value.replace('Z', '+00:00')
                            )
                        else:
                            data[field_name] = datetime.fromisoformat(value)
                    except ValueError:
                        data[field_name] = datetime.now()

        return cls(**data)


@dataclass
class LatestCar:
    car_class: str
    car_number: str
    car_model: str


class DriverStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"



@dataclass
class DriverItem:
    id: int
    telegram_id: int
    from_location: str
    to_location: str
    language: str
    status: str
    status_display: str
    amount: float
    cars_count: int
    driver_info: DriverInfo
    latest_car: LatestCar
    created_at: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DriverItem':
        """Dictionary dan DriverItem obyektini yaratish"""
        data = data.copy()

        # Nested obyektlarni yaratish
        driver_info_data = data.pop('driver_info', {})
        driver_info = DriverInfo.from_dict(driver_info_data) if driver_info_data else None

        latest_car_data = data.pop('latest_car', {})
        latest_car = LatestCar(**latest_car_data) if latest_car_data else None

        # Datetime field'larini konvert qilish
        if 'created_at' in data:
            value = data['created_at']
            if isinstance(value, str):
                try:
                    if value.endswith('Z'):
                        data['created_at'] = datetime.fromisoformat(
                            value.replace('Z', '+00:00')
                        )
                    else:
                        data['created_at'] = datetime.fromisoformat(value)
                except ValueError:
                    data['created_at'] = datetime.now()

        return cls(
            driver_info=driver_info,
            latest_car=latest_car,
            **data
        )

    @property
    def is_online(self) -> bool:
        """Driver online holatda ekanligini tekshirish"""
        return self.status == DriverStatus.ONLINE.value

    @property
    def formatted_amount(self) -> str:
        """Summani formatlangan holda qaytarish"""
        return f"{self.amount:,.0f}".replace(",", " ")

    @property
    def car_info(self) -> str:
        """Mashina haqida ma'lumot"""
        if self.latest_car:
            return f"{self.latest_car.car_model} ({self.latest_car.car_number})"
        return ""


@dataclass
class DriversResponse:
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[DriverItem]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DriversResponse':
        """Dictionary dan DriversResponse obyektini yaratish"""
        data = data.copy()

        # Results listini yaratish
        results_data = data.pop('results', [])
        results = [DriverItem.from_dict(item) for item in results_data]

        return cls(
            results=results,
            **data
        )

    def get_online_drivers(self) -> List[DriverItem]:
        """Faqat online driverlarni qaytarish"""
        return [driver for driver in self.results if driver.is_online]

    def get_drivers_by_location(self, from_location: str, to_location: str) -> List[DriverItem]:
        """Lokatsiyaga ko'ra driverlarni filter qilish"""
        return [
            driver for driver in self.results
            if driver.from_location.lower() == from_location.lower()
               and driver.to_location.lower() == to_location.lower()
               and driver.is_online
        ]

    def get_driver_by_id(self, driver_id: int) -> Optional[DriverItem]:
        """ID bo'yicha driverni topish"""
        for driver in self.results:
            if driver.id == driver_id:
                return driver
        return None

    def get_driver_by_telegram_id(self, telegram_id: int) -> Optional[DriverItem]:
        """Telegram ID bo'yicha driverni topish"""
        for driver in self.results:
            if driver.telegram_id == telegram_id:
                return driver
        return None

