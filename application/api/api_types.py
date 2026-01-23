from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, Union
from enum import Enum
import json

from application.services.route_service import RouteService


@dataclass
class PassengerTypes:
    id: int
    telegram_id: int
    language: str
    full_name: str
    total_rides: int
    phone: Optional[str] = None
    rating: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PassengerTypes':
        """Dictionary dan PassengerTypes obyektini yaratish"""
        # Kerakli maydonlarni ajratib olish
        return cls(
            id=data.get('id'),
            telegram_id=data.get('telegram_id'),
            language=data.get('language'),
            full_name=data.get('full_name'),
            total_rides=data.get('total_rides', 0),
            phone=data.get('phone'),
            rating=data.get('rating')
        )

    def to_dict(self) -> Dict[str, Any]:
        """PassengerTypes obyektini dictionary ga aylantirish"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'language': self.language,
            'full_name': self.full_name,
            'total_rides': self.total_rides,
            'phone': self.phone,
            'rating': self.rating
        }


class OrderStatus(str, Enum):
    CREATED = "created"
    SEARCHED = "searched"
    ASSIGNED = "assigned"
    ARRIVED = "arrived"
    STARTED = "started"
    ENDED = "ended"
    CANCELED = "canceled"
    REJECTED = "rejected"


@dataclass
class ContentObjectTypes:
    price: Union[str, int]
    route: Union[RouteService]
    from_location: Dict[str, Any]
    to_location: Dict[str, Any]
    cashback: int
    created_at: str
    tariff_id: Union[str, int]
    comment: Optional[str] = None
    start_time: Optional[str] = None
    passenger: int = 1
    has_woman: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentObjectTypes':
        """Dictionary dan ContentObjectTypes obyektini yaratish"""
        # Price ni string formatga o'tkazish
        price = data.get('price')
        if isinstance(price, (int, float)):
            price = str(price)

        # Datetime field'larini tekshirish
        created_at = data.get('created_at')
        start_time = data.get('start_time')

        return cls(
            price=price,
            from_location=data.get('from_location', {}),
            to_location=data.get('to_location', {}),
            cashback=data.get('cashback', 0),
            created_at=created_at,
            route=RouteService(**data.get("route", {})),
            tariff_id=data.get('tariff_id'),
            comment=data.get('comment'),
            start_time=start_time,
            passenger=data.get('passenger', 1),
            has_woman=data.get('has_woman', False)
        )

    def to_dict(self) -> Dict[str, Any]:
        """ContentObjectTypes obyektini dictionary ga aylantirish"""
        return {
            'price': self.price,
            'route': self.route,
            'from_location': self.from_location,
            'to_location': self.to_location,
            'cashback': self.cashback,
            'comment': self.comment,
            'start_time': self.start_time,
            'created_at': self.created_at,
            'passenger': self.passenger,
            'has_woman': self.has_woman
        }


@dataclass
class OrderTypes:
    id: int
    user: int
    creator: Union[PassengerTypes]
    content_object: Union[ContentObjectTypes]
    driver_details: Optional[Union[Dict[str, Any], Any]] = None
    status: str = OrderStatus.CREATED.value
    order_type: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderTypes':
        """Dictionary dan OrderTypes obyektini yaratish"""
        # Creator ni tekshirish va konvert qilish
        creator_data = data.get('creator')
        if isinstance(creator_data, dict):
            creator = PassengerTypes.from_dict(creator_data)
        elif isinstance(creator_data, PassengerTypes):
            creator = creator_data
        else:
            creator = None

        # Content object ni tekshirish va konvert qilish
        content_data = data.get('content_object')
        if isinstance(content_data, dict):
            content_object = ContentObjectTypes.from_dict(content_data)
        elif isinstance(content_data, ContentObjectTypes):
            content_object = content_data
        else:
            content_object = None

        # Driver details
        driver_details = data.get('driver_details')

        return cls(
            id=data.get('id'),
            user=data.get('user'),
            creator=creator,
            content_object=content_object,
            driver_details=driver_details,
            status=data.get('status', OrderStatus.CREATED.value),
            order_type=data.get('order_type', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """OrderTypes obyektini dictionary ga aylantirish"""
        # Creator ni dictionary ga aylantirish
        if isinstance(self.creator, PassengerTypes):
            creator_dict = self.creator.to_dict()
        elif isinstance(self.creator, dict):
            creator_dict = self.creator
        else:
            creator_dict = None

        # Content object ni dictionary ga aylantirish
        if isinstance(self.content_object, ContentObjectTypes):
            content_dict = self.content_object.to_dict()
        elif isinstance(self.content_object, dict):
            content_dict = self.content_object
        else:
            content_dict = None

        # Driver details
        driver_details_dict = self.driver_details
        if hasattr(self.driver_details, 'to_dict'):
            driver_details_dict = self.driver_details.to_dict()

        return {
            'id': self.id,
            'user': self.user,
            'creator': creator_dict,
            'content_object': content_dict,
            'driver_details': driver_details_dict,
            'status': self.status,
            'order_type': self.order_type
        }

    def to_json(self) -> str:
        """OrderTypes obyektini JSON string formatiga o'tkazish"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


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
                elif not isinstance(value, datetime):
                    data[field_name] = datetime.now()

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """DriverInfo obyektini dictionary ga aylantirish"""
        result = {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'full_name': self.full_name,
            'language': self.language,
            'is_banned': self.is_banned,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        return result


@dataclass
class LatestCar:
    car_class: str
    car_number: str
    car_model: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LatestCar':
        """Dictionary dan LatestCar obyektini yaratish"""
        return cls(
            car_class=data.get('car_class', ''),
            car_number=data.get('car_number', ''),
            car_model=data.get('car_model', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """LatestCar obyektini dictionary ga aylantirish"""
        return {
            'car_class': self.car_class,
            'car_number': self.car_number,
            'car_model': self.car_model
        }


class DriverStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


# Umumiy funksiya - har qanday dataclass uchun
def dict_to_dataclass(data: Dict[str, Any], target_class) -> Any:
    """
    Dictionary ni ma'lum bir dataclass ga aylantirish

    Args:
        data: Konvert qilinadigan dictionary
        target_class: Nisbatan konvert qilinadigan dataclass

    Returns:
        target_class: Konvert qilingan obyekt
    """
    if not hasattr(target_class, 'from_dict'):
        raise ValueError(f"{target_class.__name__} classida from_dict metodi mavjud emas")

    return target_class.from_dict(data)


def dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Dataclass obyektini dictionary ga aylantirish

    Args:
        obj: Konvert qilinadigan dataclass obyekti

    Returns:
        Dict[str, Any]: Konvert qilingan dictionary
    """
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__.copy()
    else:
        raise ValueError(f"Obyektni dictionary ga aylantirib bo'lmadi: {type(obj)}")