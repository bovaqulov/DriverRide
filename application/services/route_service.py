from application.services.base import BaseService
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class CityService:
    city_id: Optional[int] = None
    title: Optional[str] = None
    translate: Optional[Dict[str, str]] = None

    def get_localized_name(self, language: str = 'uz') -> str:
        """Berilgan til uchun shahar nomini qaytaradi"""
        if self.translate and language in self.translate:
            return self.translate[language]
        return self.title or ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CityService':
        """Dict dan CityService obyektini yaratadi"""
        return cls(
            city_id=data.get('city_id'),
            title=data.get('title'),
            translate=data.get('translate')
        )

@dataclass
class RouteService:
    route_id: Optional[int] = None
    from_city: Optional[CityService] = None
    to_city: Optional[CityService] = None

    def get_route_name(self, language: str = 'uz', separator: str = ' - ') -> str:
        """Yo'nalish nomini formatlash"""
        from_name = self.from_city.get_localized_name(language) if self.from_city else ''
        to_name = self.to_city.get_localized_name(language) if self.to_city else ''
        return f"{from_name}{separator}{to_name}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RouteService':
        """Dict dan RouteService obyektini yaratadi"""
        return cls(
            route_id=data.get('route_id'),
            from_city=CityService.from_dict(data['from_city']) if data.get('from_city') else None,
            to_city=CityService.from_dict(data['to_city']) if data.get('to_city') else None
        )


@dataclass
class RoutesResponse:
    """API javobi uchun to'liq struktura"""
    data: List[RouteService] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, api_response: Dict[str, Any]) -> 'RoutesResponse':
        """API javobidan RoutesResponse obyektini yaratadi"""
        routes = []

        # "data" kaliti ostida route ro'yxati keladi
        for route_data in api_response.get('data', []):
            route = RouteService.from_dict(route_data)
            routes.append(route)

        return cls(data=routes)

    def get_route_by_id(self, route_id: int) -> Optional[RouteService]:
        """ID bo'yicha yo'nalishni topish"""
        for route in self.data:
            if route.route_id == route_id:
                return route
        return None

    def get_routes_by_city(self, city_name: str, language: str = 'uz') -> List[RouteService]:
        """Shahar nomi bo'yicha yo'nalishlarni filter qilish"""
        filtered_routes = []
        for route in self.data:
            # Qidirishni localizatsiya qilingan nomlar orqali ham amalga oshirish
            if (route.from_city and city_name.lower() in route.from_city.get_localized_name(language).lower()) or \
                    (route.to_city and city_name.lower() in route.to_city.get_localized_name(language).lower()):
                filtered_routes.append(route)
        return filtered_routes

    def get_cities(self) -> List[CityService]:
        """Barcha shaharlarni olish (duplikatlarsiz)"""
        cities = []
        seen_ids = set()

        for route in self.data:
            if route.from_city and route.from_city.city_id not in seen_ids:
                cities.append(route.from_city)
                seen_ids.add(route.from_city.city_id)

            if route.to_city and route.to_city.city_id not in seen_ids:
                cities.append(route.to_city)
                seen_ids.add(route.to_city.city_id)

        return sorted(cities, key=lambda x: x.city_id or 0)


# Konvertatsiya funksiyalari

class RouteServiceAPI(BaseService):
    async def get_routes(self):
        data = await self._request(
            "routes/all",
            "GET"
        )
        return self._convert_routes_api_response(data)

    def _convert_routes_api_response(self, api_response: Dict[str, Any]) -> List[RouteService]:
        """API javobini RouteService obyektlar ro'yxatiga aylantiradi"""
        routes = []
        for route_data in api_response.get('data', []):
            route = RouteService.from_dict(route_data)
            routes.append(route)
        return routes

