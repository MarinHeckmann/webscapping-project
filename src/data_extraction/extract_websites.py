import requests
from bs4 import BeautifulSoup
import pandas as pd
from googletrans import Translator
import unicodedata
import pycountry
import pycountry_convert as pc
from difflib import get_close_matches


def fetch_and_parse_page(url):
    """
    Récupère et parse le contenu HTML d'une page web.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        # Récupérer la page
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lève une exception pour les erreurs HTTP
        
        # Parser le contenu avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération de l'URL {url}: {e}")
        return None


def extract_text_by_class(soup, balise,class_name):
    """
    Récupère tous les textes des balises <span> ayant une classe spécifique.
    """
    # Chercher toutes les balises <span> avec la classe donnée
    spans = soup.find_all(balise, class_=class_name)
    
    # Extraire et retourner le texte
    return [span.get_text(strip=True) for span in spans]


# Lonely planet extract
def LonelyPlanet_attractions(soup):
    
    texts = extract_text_by_class(soup,"span", "heading-05 font-semibold")
    df_LonelyPlanet=pd.DataFrame({'Title': texts})
    df_LonelyPlanet.insert(0, 'site', 'LonelyPlanet')
    df_LonelyPlanet['rank'] = range(len(df_LonelyPlanet))
    return df_LonelyPlanet


# Bucket List extract
def BucketList_attractions(soup):

    df_BucketList=pd.DataFrame()
    # Trouver toutes les balises <article>
    articles = soup.find_all('article', class_='listing-card bg-white shadow-listing')
    # Initialiser une liste pour stocker les résultats

    for article in articles:
        # Extraire le titre de la balise <h2> (nom de l'attraction)
        title_tag = article.find('h2', class_='text-2xl md:text-3xl font-bold')
        title = title_tag.get_text(strip=True) if title_tag else 'Titre non trouvé'

        # Initialiser un dictionnaire pour stocker les informations de l'attraction
        attraction_info = {'Title': title}

        # Trouver toutes les balises <p> avec les informations sur la durée, l'âge, etc.
        p_tags = article.find_all('p', class_='flex items-center space-x-1 text-lg')

        for p in p_tags:
            # Extraire le nom de la catégorie (par exemple "Duration", "Good for age", etc.)
            label_tag = p.find_all('span')[1]
            if label_tag:
                label_value = label_tag.get_text(strip=True).split(':')
                if len(label_value)==2:
                    label=label_value[0]
                    value=label_value[1]
                    attraction_info[label] = value

        # Ajouter l'attraction à la liste des résultats
        df_BucketList = pd.concat([df_BucketList, pd.DataFrame([attraction_info])], ignore_index=True)
    df_BucketList.insert(0, 'site', 'BucketList')
    df_BucketList['rank'] = range(len(df_BucketList))
    return df_BucketList


# WorldTravelGuide extract
def WorldTravelGuide_attractions(soup):

    df_WorldTravelGuide=pd.DataFrame()
    articles = soup.find_all('div', class_='high')
    articles.extend(soup.find_all('div', class_='medium'))

    for article in articles:
        # Extraire le titre de la balise <h2> (nom de l'attraction)
        title_tag = article.find('h3')
        title = title_tag.get_text(strip=True) if title_tag else 'Titre non trouvé'

        # Initialisation du dictionnaire pour stocker les informations extraites
        attraction_info = {'Title': title}

        # Extraire la description
        description_tag = article.find('p')
        if description_tag:
            attraction_info['description'] = description_tag.get_text(strip=True)


        # Extraire les horaires d'ouverture
        opening_times_tag = article.find('b', string="Opening times: ")
        if opening_times_tag:
            opening_times = opening_times_tag.find_next('p')
            if opening_times:
                attraction_info['Opening times'] = opening_times.get_text(strip=True)

        # Extraire le site Web
        website_tag = article.find('b', string="Website: ")
        if website_tag:
            website = website_tag.find_next('a')
            if website and website.get('href'):
                attraction_info['Website'] = website.get('href')

        # Extraire les frais d'admission
        admission_fees_tag = article.find('b', string="Admission Fees: ")
        if admission_fees_tag:
            admission_fees = admission_fees_tag.find_next('p')
            if admission_fees:
                attraction_info['Admission Fees'] = admission_fees.get_text(strip=True)

        # Extraire l'accès handicapé
        disabled_access_tag = article.find('b', string="Disabled Access: ")
        if disabled_access_tag:
            #comment récupérer le texte juste après disabled_access_tag
            disabled_access_text = disabled_access_tag.next_sibling.strip() if disabled_access_tag.next_sibling else 'Non spécifié'
            attraction_info['Disabled Access'] = disabled_access_text
        df_WorldTravelGuide = pd.concat([df_WorldTravelGuide, pd.DataFrame([attraction_info])], ignore_index=True)

    df_WorldTravelGuide.insert(0, 'site', 'WorldTravelGuide')
    df_WorldTravelGuide['rank'] = range(len(df_WorldTravelGuide))
    return df_WorldTravelGuide


def CNTraveler_attractions(soup):
    df_CNTraveler=pd.DataFrame()
    articles = soup.find_all('div', class_='GallerySlideFigCaption-dOeyTg gWbVWR')
    for article in articles:
        # Extraire le titre de l'attraction
        title_tag = article.find('span',class_='GallerySlideCaptionHedText-iqjOmM jwPuvZ')
        title = title_tag.get_text(strip=True) if title_tag else 'Titre non trouvé'
        attraction_info = {'Title': title}
        description_tag = article.find('p')
        if description_tag:
            attraction_info['description'] = description_tag.get_text(strip=True)
        df_CNTraveler = pd.concat([df_CNTraveler, pd.DataFrame([attraction_info])], ignore_index=True)
    df_CNTraveler.insert(0, 'site', 'CNTraveler')
    df_CNTraveler['rank'] = range(len(df_CNTraveler))
    return df_CNTraveler


def Routard_attractions(soup):
    df_Routard=pd.DataFrame()
    articles = soup.find_all('div', class_='bg-rtd-grey-100 flex h-96 w-60 flex-col rounded-xl p-4')
    for article in articles:
        # Extraire le titre de l'attraction
        title_tag = article.find('h2',class_='group-hover:text-rtd-green my-2 font-semibold')
        title = title_tag.get_text(strip=True) if title_tag else 'Titre non trouvé'
        attraction_info = {'Title': title}
        description_tag = article.find('div', class_='rtd-wysiwyg line-clamp-3')
        if description_tag:
            attraction_info['description'] = description_tag.get_text(strip=True)
        df_Routard = pd.concat([df_Routard, pd.DataFrame([attraction_info])], ignore_index=True)
    df_Routard.insert(0, 'site', 'Routard')
    df_Routard['rank'] = range(len(df_Routard))
    return df_Routard


def translate_location(name, src_lang="en", dest_lang="fr"):
    translator = Translator()
    try:
        translation = translator.translate(name, src=src_lang, dest=dest_lang).text
        translation= translation.replace("'","-").replace(" ","-").lower()
        #suppression des accents
        translation = unicodedata.normalize('NFD', translation)
        text = ''.join(char for char in translation if unicodedata.category(char) != 'Mn')
    
        return text
    except Exception as e:
        print(f"Error during translation: {e}")
        return name

def country_to_continent(country_name):
    country_names = [country.name for country in pycountry.countries]
    country = get_close_matches(country_name, country_names,n=1)
    if len(country) == 1:
        country_alpha2 = pc.country_name_to_country_alpha2(country[0])
        country_continent_code = pc.country_alpha2_to_continent_code(country_alpha2)
        country_continent_name = pc.convert_continent_code_to_continent_name(country_continent_code)
        return country_continent_name.lower()
    else: return None

def routard_city_to_region(city):

    cities_to_regions = {
        "strasbourg": "alsace",
        "bordeaux": "aquitaine-bordelais-landes",
        "rennes": "bretagne",
        "nice": "cote-d-azur",
        "paris": "ile-de-france",
        "montpellier": "languedoc-roussillon",
        "toulouse": "midi-toulousain-occitanie",
        "lille": "nord-pas-de-calais",
        "nantes": "pays-de-la-loire",
        "marseille": "provence"
    }
    if city not in cities_to_regions.values():
        return None
    else:
        return cities_to_regions[city]

def routard_continent(continent):
    routard_continent_fr = {
        "europe":"europe",
        "africa":"afrique",
        "north america":"ameriques",
        "south america":"ameriques",
        "asia":"asie",
        "oceania":"oceanie"
    }
    return routard_continent_fr[continent]

def extract_websites(country='france',city='paris',websites_to_call=['Routard','WorldTravelGuide','BucketList','LonelyPlanet','CNTraveler']):
    continent = country_to_continent(country)
    continent_fr = routard_continent(continent)
    country_fr = translate_location(country)
    city_fr = translate_location(city)

    URL_dict={
        'LonelyPlanet':f'https://www.lonelyplanet.com/{country}/{city}/attractions',
        'BucketList':f'https://www.bucketlisttravels.com/destination/{city}/best-things-to-see-and-do',
        'WorldTravelGuide':f'https://www.worldtravelguide.net/guides/{continent}/{country}/{city}/things-to-see/',
        'CNTraveler':f'https://www.cntraveler.com/gallery/best-things-to-do-in-{city}',
        'Routard':f'https://www.routard.com/fr/guide/top/{continent_fr}/{country_fr}/{city_fr}'
    }
    if country=='france':
        region = routard_city_to_region (city_fr)

        URL_dict['Routard']=f'https://www.routard.com/fr/guide/top/{country}/{region}/{city_fr}'

    URL_extractor={
        'LonelyPlanet_attractions': LonelyPlanet_attractions,
        'BucketList_attractions':BucketList_attractions,
        'WorldTravelGuide_attractions':WorldTravelGuide_attractions,
        'CNTraveler_attractions':CNTraveler_attractions,
        'Routard_attractions':Routard_attractions
    }
    df=pd.DataFrame()
    for website in websites_to_call:
        soup=fetch_and_parse_page(URL_dict[website])
        if soup:
            df=pd.concat([df,URL_extractor[f'{website}_attractions'](soup)],ignore_index=True)

    return df
        

