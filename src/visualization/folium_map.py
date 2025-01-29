import openrouteservice
from openrouteservice import convert
import folium
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
# openroute_api_key = os.getenv("openroute_api_key")

openroute_api_key="5b3ce3597851110001cf624891408baad291457b99dc5636bd74271f"
client = openrouteservice.Client(key=openroute_api_key)  # Specify your personal API key


def create_map(clusters_data, sportivity_lv):
    
    data = clusters_data
    df_attractions = pd.DataFrame(data["attractions"])
    restaurant = data["michelin"]
    # Coordonnées du restaurant
    coords_restaurant = [restaurant["longitude"], restaurant["latitude"]]

    # Coordonnées des attractions
    coords_attractions = df_attractions[["longitude", "latitude"]].values.tolist()

    # Combiner les coordonnées
    coords = [coords_restaurant] + coords_attractions + [coords_restaurant]

    # Calculer l'itinéraire via l'API (client)
    routes = client.directions(coords, optimize_waypoints=True)

    zoom = 14 - (sportivity_lv + 1) // 2
    geometry = routes["routes"][0]["geometry"]

    # Décoder la géométrie du polyline
    decoded = convert.decode_polyline(geometry)

    # Calculer le centre de la carte basé sur la bbox des routes
    map_center = [
        (routes["bbox"][0] + routes["bbox"][2]) / 2,
        (routes["bbox"][1] + routes["bbox"][3]) / 2,
    ]
    location = list(reversed(map_center))
    # Créer la carte
    m = folium.Map(location=location, zoom_start=zoom)
    # Ajouter un marqueur pour le restaurant avec des informations détaillées
    restaurant_popup = f"""
        <b>{restaurant['name']}</b><br>
        {"<b>Address:</b> " + restaurant['address'] + "<br>" if restaurant['address'] else ""}
        {"<b>Stars:</b> " + str(restaurant['stars']) + "<br>" if restaurant['stars'] is not None else ""}
        {"<b>Michelin Link:</b> <a href='" + restaurant['link'] + "' target='_blank'>Visit</a><br>" if restaurant['link'] else ""}
        {"<b>Cuisine:</b> " + restaurant['cuisine'] + "<br>" if restaurant['cuisine'] else ""}
        {"<b>Cost:</b> " + restaurant['cost'] + "<br>" if restaurant['cost'] else ""}
        {"<b>Sustainable Gastronomy:</b> " + ('Yes' if restaurant['gastonomie_durable'] else 'No') + "<br>"}
        {"<b>Description:</b> " + restaurant['description'] + "<br>" if restaurant['description'] else ""}
    """
    folium.Marker(
        location=[restaurant["latitude"], restaurant["longitude"]],
        popup=folium.Popup(restaurant_popup, max_width=300),
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(m)

    # Ajouter des marqueurs pour chaque attraction avec des informations détaillées
    for _, attraction in df_attractions.iterrows():
        attraction_popup = f"""
            <b>{attraction['Title']}</b><br>
            {"<b>Description:</b> " + attraction['description'] + "<br>" if attraction.get('description') else ""}
            {"<b>Rank:</b> " + str(attraction['rank']) + "<br>" if attraction.get('rank') is not None else ""}
            {"<b>Count:</b> " + str(attraction['count']) + "<br>" if attraction.get('count') is not None else ""}
            {"<b>Good for age:</b> " + attraction['Good for age'] + "<br>" if attraction.get('Good for age') else ""}
            {"<b>Site:</b> " + attraction['site'] + "<br>" if attraction.get('site') else 'Not available<br>'}
            {"<b>Opening Times:</b> " + attraction['Opening times'] + "<br>" if attraction.get('Opening times') else 'Not available<br>'}
            {"<b>Website:</b> " + attraction['Website'] + "<br>" if attraction.get('Website') else 'Not available<br>'}
            {"<b>Admission Fees:</b> " + attraction['Admission Fees'] + "<br>" if attraction.get('Admission Fees') else 'Not available<br>'}
        """
        folium.Marker(
            location=[attraction["latitude"], attraction["longitude"]],
            popup=folium.Popup(attraction_popup, max_width=300),
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)

    # Calculer la distance totale et la durée
    total_distance = routes["routes"][0]["summary"]["distance"]  # en mètres
    total_duration = routes["routes"][0]["summary"]["duration"]  # en secondes

    # Calculer la distance et durée sous forme plus lisible
    distance_km = total_distance / 1000  # Convertir en km
    duration_minutes = total_duration / 60  # Convertir en minutes
    popup_text = (
        f"<b>Total distance:</b> {distance_km:.2f} km<br>"
        f"<b>Total duration:</b> {duration_minutes:.1f} minutes"
    )

    # Ajouter la polyline sur la carte
    folium.PolyLine(
        locations=[list(reversed(coord)) for coord in decoded["coordinates"]],
        color="blue",
        weight=5,
        tooltip=popup_text,
    ).add_to(m)
    return m



# Affichage de plusieurs clusters en sortie
'''
def create_map2(clusters_data, sportivity_lv):
    itinerary = []
    center = []
    for data in range(clusters_data):
        df_attractions = pd.DataFrame(data["attractions"])
        restaurant = data["michelin"]
        # Coordonnées du restaurant
        coords_restaurant = [restaurant["longitude"], restaurant["latitude"]]

        # Coordonnées des attractions
        coords_attractions = df_attractions[["longitude", "latitude"]].values.tolist()

        # Combiner les coordonnées
        coords = [coords_restaurant] + coords_attractions + [coords_restaurant]

        # Calculer l'itinéraire via l'API (client)
        routes = client.directions(coords, optimize_waypoints=True)

        zoom = 14 - (sportivity_lv + 1) // 2
        geometry = routes["routes"][0]["geometry"]

        # Décoder la géométrie du polyline
        decoded = convert.decode_polyline(geometry)

        # Calculer le centre de la carte basé sur la bbox des routes
        map_center = [
            (routes["bbox"][0] + routes["bbox"][2]) / 2,
            (routes["bbox"][1] + routes["bbox"][3]) / 2,
        ]
        location = list(reversed(map_center))
        # Créer la carte
        m = folium.Map(location=location, zoom_start=zoom)
        center.append(location)
        # Ajouter un marqueur pour le restaurant avec des informations détaillées
        restaurant_popup = f"""
            <b>{restaurant['name']}</b><br>
            {"<b>Address:</b> " + restaurant['address'] + "<br>" if restaurant['address'] else ""}
            {"<b>Stars:</b> " + str(restaurant['stars']) + "<br>" if restaurant['stars'] is not None else ""}
            {"<b>Michelin Link:</b> <a href='" + restaurant['link'] + "' target='_blank'>Visit</a><br>" if restaurant['link'] else ""}
            {"<b>Cuisine:</b> " + restaurant['cuisine'] + "<br>" if restaurant['cuisine'] else ""}
            {"<b>Cost:</b> " + restaurant['cost'] + "<br>" if restaurant['cost'] else ""}
            {"<b>Sustainable Gastronomy:</b> " + ('Yes' if restaurant['gastonomie_durable'] else 'No') + "<br>"}
            {"<b>Description:</b> " + restaurant['description'] + "<br>" if restaurant['description'] else ""}
        """
        folium.Marker(
            location=[restaurant["latitude"], restaurant["longitude"]],
            popup=folium.Popup(restaurant_popup, max_width=300),
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

        # Ajouter des marqueurs pour chaque attraction avec des informations détaillées
        for _, attraction in df_attractions.iterrows():
            attraction_popup = f"""
                <b>{attraction['Title']}</b><br>
                {"<b>Description:</b> " + attraction['description'] + "<br>" if attraction['description'] else ""}
                {"<b>Rank:</b> " + str(attraction['rank']) + "<br>" if attraction['rank'] is not None else ""}
                {"<b>Count:</b> " + str(attraction['count']) + "<br>" if attraction['count'] is not None else ""}
                {"<b>Good for age:</b> " + attraction['Good for age'] + "<br>" if attraction['Good for age'] else ""}
                {"<b>Site:</b> " + attraction['site'] + "<br>" if attraction['site'] else 'Not available<br>'}
                {"<b>Opening Times:</b> " + attraction['Opening times'] + "<br>" if attraction['Opening times'] else 'Not available<br>'}
                {"<b>Website:</b> " + attraction['Website'] + "<br>" if attraction['Website'] else 'Not available<br>'}
                {"<b>Admission Fees:</b> " + attraction['Admission Fees'] + "<br>" if attraction['Admission Fees'] else 'Not available<br>'}
            """
            folium.Marker(
                location=[attraction["latitude"], attraction["longitude"]],
                popup=folium.Popup(attraction_popup, max_width=300),
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)

        # Calculer la distance totale et la durée
        total_distance = routes["routes"][0]["summary"]["distance"]  # en mètres
        total_duration = routes["routes"][0]["summary"]["duration"]  # en secondes

        # Calculer la distance et durée sous forme plus lisible
        distance_km = total_distance / 1000  # Convertir en km
        duration_minutes = total_duration / 60  # Convertir en minutes
        popup_text = (
            f"<b>Total distance:</b> {distance_km:.2f} km<br>"
            f"<b>Total duration:</b> {duration_minutes:.1f} minutes"
        )

        # Ajouter la polyline sur la carte
        folium.PolyLine(
            locations=[list(reversed(coord)) for coord in decoded["coordinates"]],
            color="blue",
            weight=5,
            tooltip=popup_text,
        ).add_to(m)

        itinerary.append(m)
    if itinerary and center:
        return itinerary[0]
    else:
        return None
'''