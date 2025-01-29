import os
import warnings
import json
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
from src.data_extraction.extract_websites import extract_websites

# from src.data_extraction.extract_tripadvisor import extract_tripadvisor
from src.data_extraction.extract_michelin import extract_michelin
from src.data_processing.processing import processing_data


warnings.filterwarnings("ignore")

# Catégories
COSTS = {1: "affordable", 2: "mid-range", 3: "premium", 4: "luxury"}
SPORTIVITY_LEVELS = {1: "low", 2: "moderate", 3: "high", 4: "extreme"}
LANGUAGES = {1: "en", 2: "fr", 3: "de", 4: "es", 5: "it", 6: "pt"}


def validate_city(city_name, country_name):
    geolocator = Nominatim(user_agent="city_validation_test")
    try:
        query = f"{city_name}, {country_name}"
        location = geolocator.geocode(
            query, addressdetails=True, exactly_one=True, language="en", timeout=5
        )

        if location:
            address = location.raw.get("address", {})
            region = address.get(
                "state",
                address.get(
                    "region", address.get("province", address.get("country", None))
                ),
            )
            city = address.get(
                "city",
                address.get(
                    "town", address.get("village", address.get("province", None))
                ),
            )
            country = address.get("country", None)
            if city is None:
                city = region
            # print(f"City found: {city}, {region}, {country}")
            return city, region, country
        else:
            print(f"City '{city_name}' in '{country_name}' not found.")
            return None, None, None
    except GeopyError as e:
        print(f"Error querying city API: {e}")
        return None, None, None


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
            return choice
        else:
            print(
                f"Invalid choice. Choose from {', '.join(str(i) for i in options_dict.keys())}."
            )
            return get_choice(
                prompt, options_dict
            )  # Appel récursif si le choix est invalide
    except ValueError:
        print(f"Please enter a valid number.")
        return get_choice(
            prompt, options_dict
        )  # Appel récursif si l'entrée n'est pas un nombre


# Vérification si un fichier existe et correspond aux paramètres
def data_exists(directory, filename):
    filepath = os.path.join(directory, filename)
    if os.path.exists(filepath):
        print(f"Data already exists: {filepath}")
        return filepath
    return None


# Sauvegarde des données avec les paramètres associés
def save_data(directory, filename, data):
    # Vérifier si l'objet est un DataFrame
    if isinstance(data, pd.DataFrame):
        # Ajouter l'extension .csv si elle n'est pas présente
        if not filename.endswith(".csv"):
            filename += ".csv"
        filepath = os.path.join(directory, filename)
        os.makedirs(directory, exist_ok=True)
        data.to_csv(filepath, index=False)
        print(f"DataFrame saved: {filepath}")

    else:
        # Ajouter l'extension .json si elle n'est pas présente
        if not filename.endswith(".json"):
            filename += ".json"
        filepath = os.path.join(directory, filename)
        os.makedirs(directory, exist_ok=True)

        # Sauvegarder en JSON avec indentation
        with open(filepath, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print(f"JSON saved: {filepath}")


def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def load_data(filepath):
    data = load_json(filepath)
    return pd.DataFrame(data["attractions"]), pd.DataFrame(data["michelin"])


def main(city, region, country):
    city_standard = city.replace("'", "-").replace(" ", "-").lower()
    region_standard = region.replace("'", "-").replace(" ", "-").lower()
    country_standard = country.replace("'", "-").replace(" ", "-").lower()

    # Params communs
    raw_params = {"country": country_standard, "city": city_standard}
    processed_params = {"country": country_standard, "city": city_standard}
    raw_file = "df_" + "_".join(str(value) for value in raw_params.values()) + ".json"
    processed_file = (
        "df_processed_"
        + "_".join(str(value) for value in processed_params.values())
        + ".json"
    )

    # Étape 2 : Extraction des données (raw)
    raw_dir = "data/raw/"
    raw_path = data_exists(raw_dir, raw_file)
    if raw_path:
        attractions_data, michelin_data = load_data(raw_path)
    else:
        print("Extracting raw data...")
        attractions_data = extract_websites(country_standard, city_standard)
        michelin_data = extract_michelin(
            country_standard, region_standard, city_standard
        )
        # Vérification si les données sont vides
        if len(attractions_data) == 0 or len(michelin_data) == 0:
            print(
                "Erreur : nous n'avons pas trouvé de données suffisantes pour cette ville"
            )
            return
        raw_data = {
            "attractions": (
                attractions_data.to_dict(orient="records")
                if isinstance(attractions_data, pd.DataFrame)
                else attractions_data
            ),
            "michelin": (
                michelin_data.to_dict(orient="records")
                if isinstance(michelin_data, pd.DataFrame)
                else michelin_data
            ),
        }

        save_data(raw_dir, raw_file, raw_data)

    # Étape 3 : Traitement des données (processed)
    processed_dir = "data/processed/"
    processed_path = data_exists(processed_dir, processed_file)
    if processed_path:
        attractions_data_process, michelin_data_process = load_data(processed_path)
    else:
        print("Cleaning and processing data...")
        attractions_data_process, michelin_data_process = processing_data(
            attractions_data, michelin_data, country, city
        )
        processed_data = {
            "attractions": (
                attractions_data_process.to_dict(orient="records")
                if isinstance(attractions_data_process, pd.DataFrame)
                else attractions_data_process
            ),
            "michelin": (
                michelin_data_process.to_dict(orient="records")
                if isinstance(michelin_data_process, pd.DataFrame)
                else michelin_data_process
            ),
        }
        save_data(processed_dir, processed_file, processed_data)


if __name__ == "__main__":
    # Exemple de population à effectuer avant le lancement streamlit
    # Permet de gagner du temps par rapport à l'extraction depuis l'interface

    tab = [
        ["Paris", "France"],
        ["Rome", "Italie"],
        ["New York", "États-Unis"],
        ["Tokyo", "Japon"],
        ["Londres", "Royaume-Uni"],
        ["Barcelone", "Espagne"],
        ["Dubaï", "Émirats arabes unis"],
        ["Bangkok", "Thaïlande"],
        ["Istanbul", "Turquie"],
        ["Singapour", "Singapour"],
        ["Los Angeles", "États-Unis"],
        ["Berlin", "Allemagne"],
        ["Sydney", "Australie"],
        ["Rio de Janeiro", "Brésil"],
        ["Le Caire", "Égypte"],
        ["Moscou", "Russie"],
        ["Toronto", "Canada"],
        ["Pékin", "Chine"],
        ["Athènes", "Grèce"],
        ["Amsterdam", "Pays-Bas"],
        ["Venise", "Italie"],
        ["San Francisco", "États-Unis"],
        ["Hong Kong", "Chine"],
        ["Vienne", "Autriche"],
        ["Séoul", "Corée du Sud"],
        ["Lisbonne", "Portugal"],
        ["Prague", "République tchèque"],
        ["Mexico", "Mexique"],
        ["Buenos Aires", "Argentine"],
        ["Bangkok", "Thaïlande"],
        ["Budapest", "Hongrie"],
        ["Marrakech", "Maroc"],
        ["Edimbourg", "Royaume-Uni"],
        ["Florence", "Italie"],
        ["Munich", "Allemagne"],
        ["Hanoï", "Vietnam"],
        ["Delhi", "Inde"],
        ["San Diego", "États-Unis"],
        ["Kuala Lumpur", "Malaisie"],
        ["Johannesburg", "Afrique du Sud"],
    ]
    for i in range(len(tab)):
        city, region, country = validate_city(tab[i][0], tab[i][1])
        print(city, region, country)
        main(city, region, country)


    # 1er affichage console avant l'affichage streamlit
    """
    # Input parameters
    city, region, country = None, None, None
    while not all((city, region, country)):
        city, region, country = validate_city(
            input("Enter the city: "), input("Enter the country: ")
        )
    language = get_choice(
        "Enter the number corresponding to your language: ", LANGUAGES
    )

    # Demander le nombre d'activités
    num_activities = int(input("Enter the number of activities: "))

    # Demander à l'utilisateur de choisir le niveau de sportivité
    sportivity = get_choice(
        f"Enter the number corresponding to your sportivity level: ({', '.join(str(i) for i in SPORTIVITY_LEVELS.keys())}): ",
        SPORTIVITY_LEVELS,
    )

    # Demander à l'utilisateur de choisir la catégorie de prix
    price_category = get_choice(
        f"Enter the number corresponding to your price category: ({', '.join(str(i) for i in COSTS.keys())}): ",
        COSTS,
    )
    print(num_activities,sportivity,price_category)
    # Run the travel planner
    main(city, region, country, language, num_activities, sportivity, price_category)"""
