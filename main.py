import os
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
from src.data_extraction.extract_websites import extract_websites
from src.data_extraction.extract_tripadvisor import extract_tripadvisor
from src.data_extraction.extract_michelin import extract_michelin
from src.data_processing.cleaning import clean_data
from src.data_processing.clustering import create_clusters
from src.route_optimization.itinerary_generator import generate_itinerary
from src.visualization.folium_map import create_map

# Catégories
COSTS = {1: 'affordable', 2: 'mid-range', 3: 'premium', 4: 'luxury'}
SPORTIVITY_LEVELS = {1: 'low', 2: 'moderate', 3: 'high', 4: 'extreme'}
LANGUAGES = {1: 'english', 2: 'french', 3: 'german', 4: 'spanish', 5: 'italian', 6: 'portuguese'}


def validate_city(city_name, country_name):
    """
    Valide et récupère le nom standardisé d'une ville avec le pays en anglais via l'API Nominatim d'OpenStreetMap.
    Permet d'envoyer à la fois le nom de la ville et du pays pour une recherche plus précise.
    
    Args:
        city_name (str): Le nom de la ville à valider.
        country_name (str): Le nom du pays dans lequel chercher la ville.
        
    Returns:
        str: Le nom standardisé de la ville et du pays en anglais, ou None si la ville n'est pas trouvée.
    """
    # Initialiser le géolocalisateur avec un user_agent
    geolocator = Nominatim(user_agent="city_validation_test")
    
    try:
        # Formater la requête avec la ville et le pays
        query = f"{city_name}, {country_name}"
        
        # Rechercher la ville dans le pays, en demandant les résultats en anglais
        location = geolocator.geocode(query, addressdetails=True, exactly_one=True, language='en')
        
        if location:
            # Extraction du nom de la ville et du pays en anglais
            address_parts = location.address.split(", ")
            # On prend la première partie (ville) et la dernière (pays)
            city, country = f"{address_parts[0]}, {address_parts[-1]}"
            print(f"City found: {city}, {country}")
            return city, country
        else:
            print(f"City '{city_name}' in '{country_name}' not found.")
            return validate_city(input("Enter the city: "),input("Enter the country: "))
    except GeopyError as e:
        print(f"Error querying city API: {e}")
        return None

def get_choice(prompt, options_dict):
    """
    Demande à l'utilisateur de choisir une option parmi un dictionnaire de choix.
    Si l'entrée est invalide, l'appelle récursivement pour redemander l'option.
    
    Args:
        prompt (str): Le message à afficher à l'utilisateur.
        options_dict (dict): Dictionnaire contenant les options valides avec les clés comme choix.
    
    Returns:
        str: La valeur correspondante à l'option choisie.
    """
    # Affiche les options possibles
    print(f"Available options:")
    for key, value in options_dict.items():
        print(f"{key}. {value}")
    
    try:
        # Demander le choix à l'utilisateur
        choice = int(input(prompt))
        
        # Vérifie que le choix est valide
        if choice in options_dict:
            return options_dict[choice]
        else:
            print(f"Invalid choice. Choose from {', '.join(str(i) for i in options_dict.keys())}.")
            return get_choice(prompt, options_dict)  # Appel récursif si le choix est invalide
    except ValueError:
        print(f"Please enter a valid number.")
        return get_choice(prompt, options_dict)  # Appel récursif si l'entrée n'est pas un nombre


# Vérification si un fichier existe et correspond aux paramètres
def data_exists(directory, filename):
    filepath = os.path.join(directory, filename)
    if os.path.exists(filepath):
        print(f"Data already exists: {filepath}")
        return filepath
    return None

# Sauvegarde des données avec les paramètres associés
def save_data(directory, filename, dataframe):
    if not filename.endswith(".csv"):
        filename += ".csv"
    filepath = os.path.join(directory, filename)
    os.makedirs(directory, exist_ok=True)
    dataframe.to_csv(filepath, index=False)
    print(f"DataFrame saved: {filepath}")

def load_data(filepath):
    with open(filepath, "r") as f:
        return json.load(f)["data"]

def main(city, country, language, num_activities, sportivity, price_category):
    city_standard = city.replace("'","-").replace(" ", "-").lower()
    country_standard = country.replace("'","-").replace(" ", "-").lower()
    # Params communs
    raw_params = {"city": city_standard, "country":country_standard}
    processed_params = {"city": city_standard, "country":country_standard,"language": language}
    cluster_params = {"city": city, "country":country, "language": language, "sportivity": sportivity, "price_category": price_category}
    itinerary_params = {**cluster_params, "num_activities": num_activities}

    raw_file = "df_" + "_".join(str(value) for value in raw_params.values()) + ".csv"
    processed_file = "df_" + "_".join(str(value) for value in processed_params.values()) + ".csv"
    cluster_file = "df_" + "_".join(str(value).replace(" ", "-").replace("'", "-").lower() for value in cluster_params.values()) + ".csv"
    itinerary_file = "df_" + "_".join(str(value).replace(" ", "-").replace("'", "-").lower() for value in itinerary_params.values()) + ".csv"

    # Étape 2 : Extraction des données (raw)
    raw_dir = "data/raw"
    raw_path = data_exists(raw_dir, raw_file)
    if raw_path:
        raw_data = load_data(raw_path)
    else:
        print("Extracting raw data...")
        tripadvisor_data = extract_tripadvisor(city_standard)
        michelin_data = extract_michelin(city_standard)
        raw_data = {"tripadvisor": tripadvisor_data, "michelin": michelin_data}
        save_data(raw_dir, raw_file, raw_data)

    # Étape 3 : Traitement des données (processed)
    processed_dir = "data/processed"
    processed_path = data_exists(processed_dir, processed_file)
    if processed_path:
        processed_data = load_data(processed_path)
    else:
        print("Cleaning and processing data...")
        processed_data = clean_data(raw_data, language)
        save_data(processed_dir, processed_file, processed_data)

    # Étape 4 : Clusterisation
    cluster_dir = "data/clusters"
    cluster_path = data_exists(cluster_dir, cluster_file)
    if cluster_path:
        clusters_data = load_data(cluster_path)
    else:
        print("Clustering data...")
        clusters_data = create_clusters(processed_data, sportivity=sportivity, price_category=price_category)
        save_data(cluster_dir, cluster_file, clusters_data)

    # Étape 5 : Génération de l'itinéraire
    itinerary_dir = "data/itinerary"
    itinerary_path = data_exists(itinerary_dir, itinerary_file, itinerary_params)
    if itinerary_path:
        itinerary_data = load_data(itinerary_path)
    else:
        print("Generating itinerary...")
        itinerary_data = generate_itinerary(clusters_data, num_activities=num_activities)
        save_data(itinerary_dir, itinerary_file, itinerary_data)

    # Étape 6 : Création de la carte
    print("Creating map visualization...")
    folium_map = create_map(itinerary_data)
    map_file = f"data/output/{city_standard.lower().replace(' ', '_')}_map.html"
    os.makedirs("data/output", exist_ok=True)
    folium_map.save(map_file)
    print(f"Map saved to {map_file}")

if __name__ == "__main__":
    # Input parameters
    city,country = validate_city(input("Enter the city: "),input("Enter the country: "))
    language = get_choice("Enter the number corresponding to your language: ", LANGUAGES)
    
    # Demander le nombre d'activités
    num_activities = int(input("Enter the number of activities: "))
    
    # Demander à l'utilisateur de choisir le niveau de sportivité
    sportivity = get_choice(f"Enter the number corresponding to your sportivity level: ({', '.join(str(i) for i in SPORTIVITY_LEVELS.keys())}): ", SPORTIVITY_LEVELS)
    
    # Demander à l'utilisateur de choisir la catégorie de prix
    price_category = get_choice(f"Enter the number corresponding to your price category: ({', '.join(str(i) for i in COSTS.keys())}): ", COSTS)
    
    # Run the travel planner
    main(city,country, language, num_activities, sportivity, price_category)

