# webscraping-project

## Informations complémentaires
Des ressources supplémentaires sont disponibles dans le dossier **`document`** :
- Une vidéo de démonstration de l'interface **Streamlit**.
- Une présentation PowerPoint expliquant le projet.

## Population des données
- Vous pouvez **remplir la base de données** en exécutant directement le fichier `populate.py`.
- Alternativement, les données peuvent être extraites depuis l'interface **Streamlit**.

---

## Commandes pour rejoindre le projet

**Cloner le dépôt :**  
```bash
git clone https://github.com/MarinHeckmann/webscapping-project.git

cd webscapping-project
```

**Créer un environnement virtuel Python :**  
```bash
python -m venv .venv
```

**Activer l'environnement virtuel :**  
- **Sur Windows** :  
  ```bash
  .venv\Scripts\activate.bat
  ```
- **Sur Mac/Linux** :  
  ```bash
  source .venv/bin/activate
  ```

**Installer les dépendances :**  
```bash
pip install -r requirements.txt
```

---

## Commandes pour lancer le projet

**Lancer l'application Streamlit :**  
```bash
streamlit run streamlit_main.py
```

---

## Commandes pour participer au projet

**Créer une nouvelle branche avec votre trigramme :**  
```bash
git checkout -b <nom-de-la-branche>
```

Apportez vos modifications au projet.

**Synchroniser et envoyer vos modifications :**  
```bash
git pull origin main
git add .
git commit -m "Ajout de la fonction de scraping pour les articles de blog"
git push origin <nom-de-la-branche>
```

**Créer un Pull Request :**  
Sur GitHub, effectuez un Pull Request pour soumettre vos modifications à la branche `main`.
