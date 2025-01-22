import arcpy
import os

from fonction.ft_int_env import initialiser_env
from fonction.ft_gesion_ar_mozaique import gestion_moz

def main():
    """
    Fonction principale pour gérer les auto-recouvrements et la gestions des mozaïque qui en resulte.

    Étapes :
    1. Initialiser l'environnement de travail.
    2. Obtenir le chemin du fichier d'entrée.
    3. Vérifier l'existence du fichier d'entrée.
    4. Extraire le nom du fichier d'entrée et son extension.
    5. Déterminer le dossier de sortie.
    6. Appeler la fonction de gestion de la mosaïque.
    """
    # Étape 0 : Initialisation de l'environnement
    geodatabase_temporaire = initialiser_env()

    # Étape 1 : Obtenir les données d'entrée
    donnees_entree = input("Entrez le chemin des données d'entrée (Shapefile) : ")

    # Étape 2 : Vérifier l'existence des données d'entrée
    if not arcpy.Exists(donnees_entree):
        raise FileNotFoundError(f"Le fichier '{donnees_entree}' est introuvable.")

    # Étape 3 : Extraire le nom du fichier
    nom_fichier = os.path.basename(donnees_entree)
    print(f"Nom du fichier extrait : {nom_fichier}")

    # Extraire le nom sans extension
    nom_sans_extension = os.path.splitext(nom_fichier)[0]
    print(f"Nom du fichier sans extension : {nom_sans_extension}")

    # Étape 4 : Déterminer le dossier de sortie
    dossier_sortie = os.path.dirname(donnees_entree)
    print(f"Dossier de sortie : {dossier_sortie}")

    # Étape 5 : Gestion des données avec mosaïque
    gestion_moz(geodatabase_temporaire, donnees_entree, nom_fichier, dossier_sortie)

# Point d'entrée du script
if __name__ == "__main__":
    main()
