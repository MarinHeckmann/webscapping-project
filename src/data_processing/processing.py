import pandas as pd
import re
from googletrans import Translator
from unidecode import unidecode
from nltk.corpus import stopwords
from rapidfuzz import fuzz
import nltk
from geopy.geocoders.nominatim import Nominatim
from sentence_transformers import SentenceTransformer


try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

translator = Translator()
stop_words = set(stopwords.words("french") + stopwords.words("english"))
geolocator = Nominatim(user_agent="webscrappingproject")
model = SentenceTransformer('all-MiniLM-L6-v2')


def group_df(df, threshold=80):

    def combined_token_sort_ratio(s1, s2):
        return 0.4 * fuzz.token_sort_ratio(
            s1, s2
        ) + 0.6 * fuzz.partial_token_sort_ratio(s1, s2)

    # Trouver la meilleure correspondance dans un sous-ensemble du DataFrame
    def find_best_match(query, grouped_df):
        best_match, best_score = None, 0
        for idx in grouped_df.index:
            choice = grouped_df.loc[idx, "Title_english"]
            score = combined_token_sort_ratio(query, choice)
            if score > best_score:
                best_match, best_score = idx, score
        return (best_match, best_score) if best_match is not None else None

    # Groupement des titres similaires
    df["group"] = None
    last_group = 0

    for index in df.index:
        sub_df = df[(df["group"].notnull()) & (df["site"] != df.loc[index, "site"])]
        match = find_best_match(df.loc[index, "Title_english"], sub_df)

        if match and match[1] >= threshold:
            df.loc[index, "group"] = df.loc[match[0], "group"]
        else:
            df.loc[index, "group"] = last_group
            last_group += 1
    return df


def merge_groups(df):
    merged_df = pd.DataFrame()

    for group in df["group"].unique():
        group_df = df[df["group"] == group]
        # Initialiser une ligne vide pour la fusion
        merged_row = {}

        filtered_group_df = group_df[group_df["VO"] == True]
        if not filtered_group_df.empty and filtered_group_df["Title"].notnull().any():
            merged_row["Title"] = filtered_group_df.loc[
                filtered_group_df["Title"].str.len().idxmin()
            ]["Title"]
        else:
            merged_row["Title"] = group_df.loc[group_df["Title"].str.len().idxmin()][
                "Title"
            ]

        # Fusionner la colonne 'site' en concaténant les valeurs, en évitant les doublons
        sites = group_df["site"].dropna().unique()
        merged_row["site"] = ", ".join(sites) if len(sites) > 0 else None

        # Calculer le 'rank' moyen pour le groupe
        merged_row["rank"] = round(group_df["rank"].mean())

        # Ajouter la 'count' pour le groupe
        merged_row["count"] = len(group_df)
        # Fusionner les colonnes avec la logique décrite
        for column in group_df.columns:

            if column not in [
                "site",
                "rank",
                "count",
                "Title",
                "group",
                "VO",
            ]:  # Ne pas fusionner ces colonnes
                # On prend la valeur avec le plus grand nombre de caractères ou None
                values = group_df[column].dropna()
                if not values.empty:
                    merged_row[column] = max(
                        values, key=len
                    )  # La valeur avec le plus grand nombre de caractères
                else:
                    merged_row[column] = None
        # Ajouter la ligne fusionnée au DataFrame final
        merged_df = pd.concat(
            [merged_df, pd.DataFrame([merged_row])], ignore_index=True
        )

    return merged_df


def extract_parentheses(title):
    match = re.search(r"\((.*?)\)", title)
    return (
        match.group(1) if match else title
    )  # Retourne le texte entre parenthèses s'il existe, sinon le titre original


def detect_and_translate(text, lang="en"):
    try:
        detected_lang = translator.detect(text).lang
        if detected_lang == lang:
            return text, False  # Pas besoin de traduction
        translated = translator.translate(text, dest=lang).text
        return translated, True
    except Exception as e:
        return f"Erreur: {e}", False


# Nettoyage des textes
def clean_text(text):
    text = unidecode(text)  # Supprime les accents
    text = re.sub(r"\W+", " ", text).lower()  # Supprime caractères spéciaux
    unique_words = []  # Liste pour stocker les mots uniques
    for word in text.split():
        if word not in stop_words and word not in unique_words:
            unique_words.append(word)
    return " ".join(unique_words)


def clean_data(df, threshold=80):

    # Appliquer la fonction à la colonne 'Title'
    df["Title"] = df["Title"].apply(extract_parentheses)

    # Détection et traduction du texte en anglais
    df[["Title_english", "VO"]] = df["Title"].apply(
        lambda x: pd.Series(detect_and_translate(x))
    )
    df["Title_english"] = df["Title_english"].apply(clean_text)

    # Fonction pour combiner les scores de similarité
    df = group_df(df, threshold)
    df.drop(columns="Title_english", inplace=True)

    df_merged = merge_groups(df).sort_values(
        by=["count", "rank"], ascending=[False, True], inplace=False
    )
    df_merged.reset_index(drop=True, inplace=True)

    return df_merged


def geocode_addresses(address, country, city):
    try:
        # Appeler l'API pour obtenir les coordonnées complètes (adresse + ville)
        location = geolocator.geocode(f"{address}, {city}, {country}")
        if location:
            return pd.Series(
                [location.latitude, location.longitude]
            )  # Retourne les valeurs sous forme de série
        else:
            print(f"Location not found: {address}")
            return pd.Series([None, None])
    except Exception as e:
        print(f"Error with address '{address}': {e}")
        return pd.Series([None, None])


def processing_data(df_attraction, df_michelin, country, city, threshold=80):

    print("merge of the attractions ...")
    df_attraction_clean = clean_data(df_attraction, threshold)

    print("geolocalisation...")
    df_attraction_clean[["latitude", "longitude"]] = df_attraction_clean["Title"].apply(
        lambda x: geocode_addresses(x, country, city)
    )
    df_attraction_clean.drop(
        df_attraction_clean[
            df_attraction_clean["latitude"].isna()
            | df_attraction_clean["longitude"].isna()
        ].index,
        inplace=True,
    )
    df_attraction_clean.reset_index(drop=True, inplace=True)

    descriptions = df_michelin['description'].tolist()
    embeddings = model.encode(descriptions, convert_to_tensor=False) 
    df_michelin['descr_emb'] = [emb.tolist() for emb in embeddings] 

    return df_attraction_clean, df_michelin
