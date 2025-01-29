from haversine import haversine, Unit
import pandas as pd
from googletrans import Translator
import json  
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
model = SentenceTransformer('all-MiniLM-L6-v2')


translator = Translator()

COSTS = {1: "affordable", 2: "mid-range", 3: "premium", 4: "luxury"}
SPORTIVITY_LEVELS = {1: "low", 2: "moderate", 3: "high", 4: "extreme"}


def filter_by_proximity(df, radius_km):

    filtered_rows = []
    to_drop = set()
    for i, row in df.iterrows():
        if i in to_drop:
            continue

        filtered_rows.append(row)

        for j in range(i + 1, len(df)):
            if j not in to_drop:
                row2 = df.iloc[j]
                distance = haversine(
                    (row["latitude"], row["longitude"]),
                    (row2["latitude"], row2["longitude"]),
                )
                if distance < radius_km:
                    to_drop.add(j)

    return pd.DataFrame(filtered_rows)


def filter_by_cost(df, cost_level):
    for i in range(4):
        for level in [cost_level - i, cost_level + i]:
            if 1 <= level <= 4:
                target_cost = COSTS[level]
                filtered_df = df[df["cost"].str.lower() == target_cost.lower()]
                if not filtered_df.empty:
                    return filtered_df.reset_index(drop=True)
        return df


def clustering(df_attraction, df_michelin, radius_km, num_activities):
    clusters = []  # Liste pour stocker les clusters sous la nouvelle forme demandée

    # Pour chaque restaurant Michelin, vérifier sa proximité avec chaque attraction
    for _, restaurant in df_michelin.iterrows():
        lat_restaurant = restaurant["latitude"]
        lon_restaurant = restaurant["longitude"]

        # Liste des attractions associées à ce restaurant
        attractions_nearby = []

        for _, attraction in df_attraction.iterrows():
            lat_attraction = attraction["latitude"]
            lon_attraction = attraction["longitude"]

            # Calcul de la distance entre le restaurant et l'attraction
            distance = haversine(
                (lat_restaurant, lon_restaurant), (lat_attraction, lon_attraction)
            )

            # Si la distance est inférieure au rayon défini, on l'ajoute
            if distance <= radius_km:
                attractions_nearby.append(attraction.to_dict())

        # Ajouter le cluster si des attractions ont été trouvées
        if attractions_nearby:
            cluster = [restaurant.to_dict()] + attractions_nearby
            clusters.append(cluster)

    # Filtrer les clusters qui ont au moins n_activites
    clusters = [
        cluster[: num_activities + 1]
        for cluster in clusters
        if len(cluster) > num_activities
    ]

    # Si aucun cluster ne respecte la contrainte, renvoyer le plus long si sa taille est > 3
    if not clusters:
        max_length = max((len(cluster) for cluster in clusters), default=0)
        longest_clusters = [
            cluster for cluster in clusters if len(cluster) == max_length
        ]
        return longest_clusters if max_length > 3 else None
    return clusters


def sportivity_to_dist(sportivity_lv):
    return 2 ** (sportivity_lv - 1)


def translate(text, lang="en"):
    try:
        detected_lang = translator.detect(text).lang
        if detected_lang == lang:
            return text
        translated = translator.translate(text, dest=lang).text
        return translated
    except Exception:
        return text
def find_most_similar_cluster(clusters, query):
    # Encoder la requête
    query_en = translate(query)
    query_embedding = model.encode(query_en, convert_to_tensor=False)
    
    # Extraire les embeddings des clusters (uniquement les embeddings des restaurants)
    descr_embs = [cluster[0]['descr_emb'] for cluster in clusters]
    
    # Calculer les scores de similarité cosinus pour chaque élément dans la liste
    cos_scores = []
    for descr_emb in descr_embs:
        score = cosine_similarity([query_embedding], [descr_emb])[0][0]  # Calcul de la similarité cosinus
        cos_scores.append(score)
    
    # Trouver l'indice du plus similaire
    most_similar_index = cos_scores.index(max(cos_scores))  # Trouver le maximum dans la liste des scores
    
    # Récupérer le cluster correspondant
    best_cluster = clusters[most_similar_index]
    
    return best_cluster

def create_clusters(
    df_attraction,
    df_michelin,
    num_activities=None,
    sportivity_lv = 4,
    price_category_lv=None,
    language='en',
    sentence=None
):
    if not num_activities:
        if sentence: 
            num_activities=5
        else: 
            num_activities = 20

    clusters = None
    dist = 0
    if price_category_lv:
        df_michelin_filter = filter_by_cost(df_michelin, price_category_lv)
    else:
        df_michelin_filter = df_michelin
    
    while not clusters and sportivity_lv < 5:
        dist = sportivity_to_dist(sportivity_lv)
        clusters = clustering(df_attraction, df_michelin_filter, dist, num_activities)
        sportivity_lv += 1

    if clusters:
        print('filtre cluster')
        if sentence:
            cluster = find_most_similar_cluster(clusters,sentence)
        else:
            cluster = clusters[0]

        print("translation...")

        structured_json = []
        for i, event in enumerate(cluster):
            if i == 0:
                event["cuisine"] = translate(event["cuisine"], language)
                event.pop("descr_emb", None)
            else:
                event["Title"] = translate(event["Title"], language)
            if "description" in event:
                event["description"] = translate(event["description"], language)
        structured_json = {
            "michelin": cluster[0],  # Le restaurant
            "attractions": cluster[1:],  # Les attractions
        }
        
        return structured_json
    else:
        print("No cluster for this city")
        return None