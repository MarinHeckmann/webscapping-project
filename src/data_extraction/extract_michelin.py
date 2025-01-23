import requests
from bs4 import BeautifulSoup
import re
import pandas as pd


def fetch_restaurant_data(url):
    """
    Récupère les données de restaurants depuis une URL donnée.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        restaurants = soup.find_all('div', {'class': "card__menu-content"})
        return restaurants if restaurants else None
    except requests.RequestException as e:
        print(f"Erreur lors de la requête : {e}")
        return None
    
def scrap_restaurant(restaurants):
    COSTS = ['Affordable', 'Mid-Range', 'Premium', 'Luxury']
    data = []
    for resto in restaurants:
        resto_a = resto.find('a')
        name = resto_a.text.strip()
        link = "https://guide.michelin.com" + resto_a.get('href')
        nb_stars = 0
        bib_gourmand = False #bib-gourmand: nos meilleurs rapports qualité-prix
        gastronomie_durable = False
        gastronomie_durable = False
        for span in resto.find_all('span', {'class':'distinction-icon'}):
            for distinction in span.find_all('img'):
                src = distinction.get('src')
                if "star" in src:
                    nb_stars += 1
                elif "bib-gourmand" in src:
                    bib_gourmand = True
                elif "gastronomie-durable" in src:
                    gastronomie_durable = True

        resto_div = resto.find_all('div', {'class': "card__menu-footer--score"})
        tmp = re.sub(r'\s+', ' ', resto_div[1].text).strip() # to get "<$/€> · <cuisine>"
        price, cuisine = tmp.split(" · ")
        cost = COSTS[len(price)-1]
        address, latitude, longitude, description = scrap_resto_link(link)
        data.append({
            "name": name,
            "link": link,
            "stars": nb_stars,
            "bib-gourmand": bib_gourmand,
            "cuisine": cuisine,
            "cost": cost,
            "address": address,
            "latitude":latitude,
            "longitude": longitude,
            "gastonomie_durable": gastronomie_durable,
            "description": description
        })
    if len(data)==0:
        return None
    return pd.DataFrame(data)


def scrap_resto_link(url):
    resto_req = requests.get(url)
    resto_soup = BeautifulSoup(resto_req.text, 'html.parser')
    
    # Extraction de l'adresse
    address = ""
    for div in resto_soup.find_all('div', {'class':'data-sheet__block--text'}):
        text = div.text.strip()
        if not '\n' in text:
            address = text
            break
    
    # Extraction des coordonnées (latitude et longitude)
    latitude, longitude = None, None
    for iframe in resto_soup.find_all('iframe'):
        i_src = iframe.get('src')
        if i_src is None:
            continue
        if "maps" in i_src:
            search = re.search(r'q=([-+]?[0-9]*\.?[0-9]+),([-+]?[0-9]*\.?[0-9]+)', i_src)
            if search:
                latitude = float(search.group(1))
                longitude = float(search.group(2))
    
    # Extraction de la description (s'il y en a)
    description = None
    description_div = resto_soup.find('div', {'class': 'data-sheet__description'})
    if description_div:
        description = description_div.get_text(strip=True)
    
    return address, latitude, longitude, description

def extract_michelin(country, region, city, n_pages=3, link = 'data/utils/links_michelin_norm.csv'):
    """
    Fonction principale pour récupérer les informations des restaurants d'une ville.
    Retourne un DataFrame consolidé avec toutes les pages scrappées.
    """
    df = pd.read_csv(link)
    assert n_pages > 0, "n_pages doit être supérieur à 0 !"

    # Initialisation d'un DataFrame vide avec les bonnes colonnes
    df_restaurants = pd.DataFrame(columns=["name", "link", "stars", "bib-gourmand", 
                                           "cuisine", "cost", "address", "latitude", 
                                           "longitude", "gastonomie_durable"])

    page = 1

    while page <= n_pages:
        if city in df['city'].values and country in df['country'].values:
            base_url = df.loc[(df['city'] == city) & (df['country'] == country), 'url'].values[0]
            url = base_url + f"/page/{page}?sort=distance" if page > 1 else base_url + "?sort=distance"
        else:
            url = f"https://guide.michelin.com/fr/fr/restaurants?showMap=false&q={city}+{region if region else ''}+{country}"
        restaurants = fetch_restaurant_data(url)

        if not restaurants:
            break  # Stopper si aucun restaurant trouvé

        new_data = scrap_restaurant(restaurants)
        
        if new_data is not None and not new_data.empty and not new_data.isna().all().all():
            df_restaurants = pd.concat([df_restaurants, new_data], ignore_index=True)
        page += 1
        
        if len(restaurants) < 20:
            break  # Arrêter si moins de 20 restaurants trouvés (fin de la liste)

    return df_restaurants