import requests
from typing import List, Dict, Optional


class ScryFall:
    """
    Clase para interactuar con la API de ScryFall.
    Documentación oficial: https://scryfall.com/docs/api
    """

    BASE_URL = "https://api.scryfall.com"

    def buscar_colecciones(self) -> List[Dict]:
        """
        Obtiene colecciones (sets) desde ScryFall.
        Returns:
            List[Dict]: Lista de colecciones con datos relevantes, o lista vacía si no se encuentran.
        """
        try:
            url = f"{self.BASE_URL}/sets"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if "data" in data:
                return [
                    {
                        "id": set_data["id"],
                        "name": set_data["name"],
                        "code": set_data["code"],
                        "released_at": set_data["released_at"],
                        "card_count": set_data["card_count"],
                        "icon_svg_uri": set_data["icon_svg_uri"]
                    }
                    for set_data in data["data"]
                    if set_data["digital"] is False  # Filtrar solo colecciones físicas
                ]
            return []
        except requests.RequestException as e:
            print(f"Error en la API de ScryFall al buscar colecciones: {e}")
            return []

    def buscar_cartas(self, query: str, set_code: Optional[str] = None) -> List[Dict]:
        """
        Busca cartas por texto y/o código de colección con paginación.
        Args:
            query (str): Texto de búsqueda (e.g., "Castle").
            set_code (str, optional): Código de colección (e.g., "LEA").
        Returns:
            List[Dict]: Lista de cartas con datos relevantes, o lista vacía si no se encuentran.
        """
        try:
            url = f"{self.BASE_URL}/cards/search"
            params = {"q": f"{query} include:extras", "unique": "prints"}
            if set_code:
                params["q"] += f" set:{set_code}"

            all_cards = []
            while url:
                response = requests.get(url, params=params if not all_cards else {})
                response.raise_for_status()
                data = response.json()
                if "data" in data:
                    all_cards.extend(
                        {
                            "id": card["id"],
                            "name": card["name"],
                            "set": card["set"],
                            "set_name": card["set_name"],
                            "number": card.get("collector_number"),
                            "image_url": card["image_uris"]["normal"] if "image_uris" in card else None,
                            "colors": ",".join(card.get("colors", [])) if card.get("colors") else None,
                            "rarity": card.get("rarity")
                        }
                        for card in data["data"]
                    )
                url = data.get("next_page")
                if url:
                    print(f"Obteniendo más resultados... ({len(all_cards)} cartas encontradas hasta ahora)")

            print(f"Total cartas encontradas para '{query}': {len(all_cards)}")
            return all_cards
        except requests.RequestException as e:
            print(f"Error al buscar cartas: {e}")
            return []


if __name__ == "__main__":
    scryfall = ScryFall()
    colecciones = scryfall.buscar_colecciones()
    print(f"Colecciones encontradas: {len(colecciones)}")