import arcpy
import os

from fonction.ft_int_env import initialiser_env
from fonction.ft_gesion_ar_mozaique import gestion_moz

def main():
    """
    Fonction principale pour gérer les auto-recouvrements et la gestion des mosaïques qui en résultent.

    Étapes :
    1. Initialiser l'environnement de travail.
    2. Obtenir le chemin du fichier d'entrée.
    3. Vérifier l'existence du fichier d'entrée.
    4. Extraire le nom du fichier d'entrée et son extension.
    5. Déterminer le dossier de sortie.
    6. Appeler la fonction de gestion de la mosaïque.
    """
    # Étape 0 : Initialisation de l'environnement
    # Si initialiser_env retourne un Result, on extrait le chemin
    geodatabase_temporaire = initialiser_env()
    if hasattr(geodatabase_temporaire, "getOutput"):
        geodatabase_temporaire = geodatabase_temporaire.getOutput(0)
    else:
        geodatabase_temporaire = str(geodatabase_temporaire)

    # Étape 1 : Obtenir les données d'entrée
    donnees_entree = input(
        "Entrez le chemin d'un ou plusieurs shapefiles (séparés par des points-virgules) : "
    )
    liste_donnees_entree = [chemin.strip() for chemin in donnees_entree.split(";")]

    # Étape 2 : Vérifier l'existence de tous les fichiers d'entrée
    for chemin in liste_donnees_entree:
        if not arcpy.Exists(chemin):
            raise FileNotFoundError(f"Le fichier '{chemin}' est introuvable.")

    # Étape 3 : Extraire le nom du premier fichier
    nom_fichier = os.path.basename(liste_donnees_entree[0])
    nom_sans_extension = os.path.splitext(nom_fichier)[0]
    print(f"Nom du fichier extrait : {nom_fichier}")
    print(f"Nom du fichier sans extension : {nom_sans_extension}")

    # Étape 4 : Déterminer le dossier de sortie
    dossier_sortie = os.path.dirname(liste_donnees_entree[0])
    print(f"Dossier de sortie : {dossier_sortie}")

    # Étape 5 : Lancer le traitement
    gestion_moz(geodatabase_temporaire, liste_donnees_entree, dossier_sortie)

# Point d'entrée du script
if __name__ == "__main__":
    main()
