import geopy.geocoders.nominatim as Nominatim

def geocode_addresses(addresses,city):
    """
    Géocode une liste d'adresses en utilisant l'API OpenRouteService.

    :param addresses: Liste d'adresses (chaînes de caractères) à géocoder.
    :param api_key: Clé API OpenRouteService.
    :return: Liste de tuples (adresse, latitude, longitude).
    """
    results = {}
    geolocator = Nominatim(user_agent="test")

    for address in addresses:
        try:
            # Appeler l'API pour obtenir les coordonnées
            location = geolocator.geocode(f"{address},{city}")
            if location:
                results[address] = [location.longitude,location.latitude]  # Latitude, Longitude
            
        except Exception as e:
            print(f"Erreur lors du géocodage de l'adresse '{address}': {e}")
    
    return results



def create_clusters (df_attraction,df_michelin,sportivity,price_category):
    return None
    