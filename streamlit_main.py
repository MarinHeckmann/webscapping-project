import streamlit as st
import warnings
import json
from geopy.geocoders import Nominatim
import os
import folium
import pandas as pd
from streamlit_folium import folium_static
from src.data_extraction.extract_websites import extract_websites
from src.data_extraction.extract_michelin import extract_michelin
from src.data_processing.processing import processing_data
from src.data_clustering.clustering import create_clusters
from src.visualization.folium_map import create_map

# Catégories
COSTS_ = {"affordable": 1, "mid-range": 2, "premium": 3, "luxury": 4}
SPORTIVITY_LEVELS_ = {"low": 1, "moderate": 2, "high": 3, "extreme": 4}

COSTS = {1: "affordable", 2: "mid-range", 3: "premium", 4: "luxury"}
SPORTIVITY_LEVELS = {1: "low", 2: "moderate", 3: "high", 4: "extreme"}
LANGUAGES = {1: "en", 2: "fr", 3: "de", 4: "es", 5: "it", 6: "pt"}


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


def run_main(
    city,
    region,
    country,
    language,
    num_activities,
    sportivity,
    price_category,
    raw,
    process,
    description,
):
    city_standard = city.replace("'", "-").replace(" ", "-").lower()
    region_standard = region.replace("'", "-").replace(" ", "-").lower()
    country_standard = country.replace("'", "-").replace(" ", "-").lower()
    if price_category == "No category":
        price_category_lv = None
    else:
        price_category_lv = COSTS_[price_category]
    sportivity_lv = SPORTIVITY_LEVELS_[sportivity]
    raw_params = {"country": country_standard, "city": city_standard}
    processed_params = {"country": country_standard, "city": city_standard}

    raw_file = "df_" + "_".join(str(value) for value in raw_params.values()) + ".json"
    processed_file = (
        "df_processed_"
        + "_".join(str(value) for value in processed_params.values())
        + ".json"
    )
    if not raw:
        with st.spinner("Extracting raw data..."):

            raw_dir = "data/raw/"
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

    if not process:
        if raw:
            raw_dir = "data/raw/"
            raw_path = os.path.join(raw_dir, raw_file)
            attractions_data, michelin_data = load_data(raw_path)
        with st.spinner("Processing data..."):
            processed_dir = "data/processed/"
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

    else:
        processed_dir = "data/processed/"
        processed_path = os.path.join(processed_dir, processed_file)
        attractions_data_process, michelin_data_process = load_data(processed_path)
    with st.spinner("Clustering and translating data..."):
        clusters_data = create_clusters(
            attractions_data_process,
            michelin_data_process,
            num_activities,
            sportivity_lv,
            price_category_lv,
            language,
            description,
        )
        m = create_map(clusters_data, sportivity_lv)
        folium_static(m)


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


# Titre de l'application
st.title("Travel Planner")

# Initialisation des variables dans st.session_state si elles n'existent pas encore
if "city" not in st.session_state:
    st.session_state.city = ""
if "country" not in st.session_state:
    st.session_state.country = ""
if "region" not in st.session_state:
    st.session_state.region = ""
if "validated" not in st.session_state:
    st.session_state.validated = False
if "num_activities" not in st.session_state:
    st.session_state.num_activities = 3
if "sportivity_lv" not in st.session_state:
    st.session_state.sportivity_lv = None
if "price_category_lv" not in st.session_state:
    st.session_state.price_category_lv = None
if "language" not in st.session_state:
    st.session_state.language = None
if "raw" not in st.session_state:
    st.session_state.raw = False
if "process" not in st.session_state:
    st.session_state.process = False
if "description" not in st.session_state:
    st.session_state.description = ""


# Formulaire de validation de la ville et du pays
with st.form(key="city_country_form"):
    st.subheader("Enter your destination")
    city_input = st.text_input("City", value=st.session_state.city)
    country_input = st.text_input("Country", value=st.session_state.country)
    validate_btn = st.form_submit_button("Validate City")

    # Si l'utilisateur appuie sur le bouton "Validate City"
    if validate_btn:
        validated_city, region, validated_country = validate_city(
            city_input, country_input
        )
        if validated_city:
            # Mettre à jour les variables de session et valider
            st.session_state.city = validated_city
            st.session_state.region = region
            st.session_state.country = validated_country
            st.session_state.validated = True
            st.success(f"City {validated_city} in {validated_country} validated!")
        else:
            # Réinitialiser les champs si la validation échoue
            st.session_state.validated = False
            st.session_state.city = (
                ""  # Effacer les champs pour que l'utilisateur puisse réessayer
            )
            st.session_state.country = ""
            st.error("Invalid city or country. Please try again.")

# Ajouter un bouton pour réinitialiser la validation en dehors du formulaire
if st.session_state.validated:
    reset_btn = st.button("Revalidate or Change City")
    if reset_btn:
        # Réinitialiser la validation et laisser l'utilisateur changer la ville et le pays
        st.session_state.validated = False
        st.session_state.city = ""
        st.session_state.country = ""
        st.session_state.num_activities = (
            3  # Réinitialiser les autres paramètres si nécessaire
        )
        st.session_state.sportivity_lv = None
        st.session_state.price_category_lv = None
        st.warning("City and country reset. Please re-enter your destination.")

# Vérification de la validation avant d'afficher le second formulaire
if st.session_state.validated:
    city_standard = st.session_state.city.replace("'", "-").replace(" ", "-").lower()
    country_standard = (
        st.session_state.country.replace("'", "-").replace(" ", "-").lower()
    )
    # Vérification de l'existence des fichiers
    raw_file = f"data/raw/df_{country_standard}_{city_standard}.json"
    processed_file = (
        f"data/processed/df_processed_{country_standard}_{city_standard}.json"
    )

    if os.path.exists(raw_file):
        st.info("Raw data file exists.")
        st.session_state.raw = True
    else:
        st.warning("Raw data file does not exist. It will be generated.")
        st.session_state.raw = False
    if os.path.exists(processed_file):
        st.info("Processed data file exists.")
        st.session_state.process = True
    else:
        st.warning("Processed data file does not exist. It will be generated.")
        st.session_state.process = False
    
    # Formulaire pour les paramètres utilisateur
    with st.form(key="user_preferences_form"):
        st.subheader("Customize your trip")

        st.session_state.num_activities = st.number_input(
            "Number of activities",
            min_value=2,
            max_value=20,
            value=st.session_state.num_activities,
        )
        st.session_state.sportivity_lv = st.selectbox(
            "Sportivity Level",
            ["low", "moderate", "high", "extreme"],
            index=(
                3
                if not st.session_state.sportivity_lv
                else ["low", "moderate", "high", "extreme"].index(
                    st.session_state.sportivity_lv
                )
            ),
        )
        st.session_state.price_category_lv = st.selectbox(
            "Price Category",
            ["No category", "affordable", "mid-range", "premium", "luxury"],
            index=(
                0
                if not st.session_state.price_category_lv
                else [
                    "No category",
                    "affordable",
                    "mid-range",
                    "premium",
                    "luxury",
                ].index(st.session_state.price_category_lv)
            ),
        )

        st.session_state.language = st.selectbox(
            "Language Category",
            ["en", "fr", "de", "es", "it", "pt"],
            index=(
                0
                if not st.session_state.language
                else ["en", "fr", "de", "es", "it", "pt"].index(
                    st.session_state.language
                )
            ),
        )

        st.session_state.description = st.text_area(
            "Describe your ideal restaurant setting",
            value=st.session_state.description,
            height=100,
        )


        submit_preferences = st.form_submit_button("Generate Itinerary")

        if submit_preferences:
            # Appel à la fonction `run_main` avec la description incluse
            run_main(
                st.session_state.city,
                st.session_state.region,
                st.session_state.country,
                st.session_state.language,
                st.session_state.num_activities,
                st.session_state.sportivity_lv,
                st.session_state.price_category_lv,
                st.session_state.raw,
                st.session_state.process,
                st.session_state.description,  
            )
