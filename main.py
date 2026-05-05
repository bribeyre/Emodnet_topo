import os
import re
import unicodedata
import arcpy

# Importation des fonctions personnalisées
from fonction.ft_int_env import initialiser_env
from fonction.ft_etapes import (
    generer_boite_englobante,
    supprimer_zones_recouvertes,
    convertir_en_polygones_simple,
    supprimer_plus_grand_polygone,
    extraire_sommets,
    creer_polygones_thiessen,
    decouper_polygones_thiessen,
    effectuer_jointure_spatiale,
    merge_donnees,
    dissoudre_avec_statistiques,
    exporter_resultat,
)

def nettoyer_nom(nom):
    """
    Nettoie un nom de fichier pour qu'il soit compatible avec ArcGIS :
    - Supprime les accents
    - Remplace les caractères spéciaux ou espaces par des underscores
    - Supprime les underscores superflus en début/fin
    """
    nom = unicodedata.normalize('NFKD', nom).encode('ASCII', 'ignore').decode('ASCII')
    nom = re.sub(r'\W+', '_', nom)
    nom = nom.strip('_')
    return nom

def main():
    """
    Programme principal exécutant toutes les étapes du traitement spatial.
    """
    # Étape 0 : Initialisation de l'environnement (dossiers, géodatabase temporaire, etc.)
    dossier_racine, dossier_sortie, geodatabase_temporaire = initialiser_env()

    # Étape 0 : Récupération des données d'entrée
    donnees_entree = input("Entrez le chemin des données d'entrée (Shapefile) : ")
    if not arcpy.Exists(donnees_entree):
        raise FileNotFoundError(f"Le fichier '{donnees_entree}' est introuvable.")

    # Extraire le nom du fichier sans le chemin
    nom_fichier = os.path.basename(donnees_entree)
    print(f"Nom du fichier extrait : {nom_fichier}")

    # Extraire le nom sans extension et le nettoyer pour un usage sûr dans ArcGIS
    nom_sans_extension = os.path.splitext(nom_fichier)[0]
    nom_sans_extension = nettoyer_nom(nom_sans_extension)
    print(f"Nom nettoyé : {nom_sans_extension}")

    # Étape 0 : Ajout d'un champ OID_ORIG si absent (utile pour retracer les entités)
    if "OID_ORIG" not in [f.name for f in arcpy.ListFields(donnees_entree)]:
        arcpy.management.AddField(donnees_entree, "OID_ORIG", "LONG")
        with arcpy.da.UpdateCursor(donnees_entree, ["OID@", "OID_ORIG"]) as cur:
            for row in cur:
                row[1] = row[0]
                cur.updateRow(row)

    # Étape 1 : Génération de la boîte englobante à partir des données d’entrée
    boite_englobante = generer_boite_englobante(donnees_entree, geodatabase_temporaire)

    # Étape 2 : Suppression des zones couvertes par les données existantes
    boite_englobante_sans_donnees = supprimer_zones_recouvertes(
        boite_englobante, donnees_entree, geodatabase_temporaire
    )

    # Étape 3 : Conversion des zones restantes en polygones simples
    polygones_simple = convertir_en_polygones_simple(boite_englobante_sans_donnees, geodatabase_temporaire)

    # Étape 4 : Suppression du plus grand polygone (souvent en périphérie)
    supprimer_plus_grand_polygone(polygones_simple)

    # Étape 5 : Extraction des sommets des polygones restants
    points_sommet = extraire_sommets(polygones_simple, geodatabase_temporaire)

    # Étape 6 : Génération des polygones de Thiessen à partir des sommets
    polygones_thiessen = creer_polygones_thiessen(points_sommet, geodatabase_temporaire)

    # Étape 7 : Découpage des polygones de Thiessen par les polygones simples
    polygones_thiessen_decoupes = decouper_polygones_thiessen(
        polygones_thiessen, polygones_simple, geodatabase_temporaire
    )

    # Étape 8 : Jointure spatiale entre les polygones découpés et les données d’entrée
    resultat_jointure_spatiale = effectuer_jointure_spatiale(
        polygones_thiessen_decoupes, donnees_entree, geodatabase_temporaire
    )

    # Étape 9 : Fusion des données originales avec les résultats de la jointure
    fusion_donnees = merge_donnees(resultat_jointure_spatiale, donnees_entree, geodatabase_temporaire)

    # Étape 10 : Dissolution des polygones fusionnés avec calcul de statistiques
    dissolve_avec_statistiques = dissoudre_avec_statistiques(
        fusion_donnees, geodatabase_temporaire, nom_sans_extension
    )

    # Étape 11 : Export du résultat final vers le dossier de sortie
    exporter_resultat(dissolve_avec_statistiques, dossier_sortie)

if __name__ == "__main__":
    main()
