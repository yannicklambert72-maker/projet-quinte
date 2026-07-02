import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

# ==========================
# Configuration
# ==========================
URL_GENY = "https://www.geny.com/reunions-courses-pmu"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0 Safari/537.36"
    )
}
FICHIER_INFO = "quinte_du_jour.json"

# ==========================
# Téléchargement
# ==========================
print("Connexion à Geny.com...")
response = requests.get(URL_GENY, headers=HEADERS, timeout=20)
response.raise_for_status()
print("Page téléchargée.")

# ==========================
# Recherche du Quinté+
# ==========================
soup = BeautifulSoup(response.text, "html.parser")

url_quinte = None
nom_course = None
heure_depart = None

# Le Quinté+ est identifié par les liens ayant la classe "btnQuinte"
lien_quinte = soup.find("a", class_="btnQuinte", href=lambda h: h and "partants-pmu" in h)

if lien_quinte:
    url_quinte = "https://www.geny.com" + lien_quinte["href"]

    # Remonte pour trouver le bloc de la course (div courseParis)
    bloc_course = lien_quinte.find_parent("div", class_="yui-g")
    if bloc_course:
        # Le nom est dans le div précédent
        bloc_nom = bloc_course.find_previous_sibling("div")
        if bloc_nom:
            nom_tag = bloc_nom.find(class_="nomCourse")
            if nom_tag:
                nom_course = nom_tag.get_text(strip=True)

        # L'heure est dans le div btnArrivee
        heure_tag = bloc_course.find("div", class_="btnArrivee")
        if heure_tag:
            texte = heure_tag.get_text(strip=True)
            match = re.search(r'(\d{2}h\d{2})', texte)
            if match:
                heure_depart = match.group(1)

# ==========================
# Résultat
# ==========================
if url_quinte is None:
    raise Exception("Impossible de trouver le Quinté+ du jour.")

print("\n===================================")
print("Quinté+ trouvé !")
print("Course      :", nom_course)
print("Heure départ:", heure_depart)
print("URL         :", url_quinte)
print("===================================\n")

# ==========================
# Sauvegarde
# ==========================
info = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "nom_course": nom_course,
    "heure_depart": heure_depart,
    "url_partants": url_quinte
}

with open(FICHIER_INFO, "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=2)

print("Infos sauvegardées dans :", FICHIER_INFO)