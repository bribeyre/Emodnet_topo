import os
import arcpy
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

def main():
    """
    Programme principal exécutant toutes les étapes du traitement spatial.
    """
    # Étape 0 : Initialisation
    dossier_racine, dossier_sortie, geodatabase_temporaire = initialiser_env()

    # Étape 0 : Obtenir les données d'entrée
    donnees_entree = input("Entrez le chemin des données d'entrée (Shapefile) : ")
    if not arcpy.Exists(donnees_entree):
        raise FileNotFoundError(f"Le fichier '{donnees_entree}' est introuvable.")

    # Extraire le nom du fichier sans le chemin
    nom_fichier = os.path.basename(donnees_entree)
    print(f"Nom du fichier extrait : {nom_fichier}")

    # Exemple d'utilisation du nom de fichier plus tard
    nom_sans_extension = os.path.splitext(nom_fichier)[0]
    print(f"Nom du fichier sans extension : {nom_sans_extension}")

    # Étape 0 : Détection des superpositions
    # detecter_superpositions(donnees_entree, geodatabase_temporaire)

    # Etape 1 : Gestions des auto-recouvrement
    # polygone_avec = gestion_ar(donnees_entree, geodatabase_temporaire)

    #Supperssions des polygones auto-recouvert
    # donnee_entre_v2 = supprimer_donnees_s_id(polygone_avec)

    if "OID_ORIG" not in [f.name for f in arcpy.ListFields(donnees_entree)]:
        arcpy.management.AddField(donnees_entree, "OID_ORIG", "LONG")
        with arcpy.da.UpdateCursor(donnees_entree, ["OID@", "OID_ORIG"]) as cur:
            for row in cur:
                row[1] = row[0]
                cur.updateRow(row)

    # Étape 1 : Génération de la boîte englobante
    boite_englobante = generer_boite_englobante(donnees_entree, geodatabase_temporaire)

    # Étape 2 : Suppression des zones recouvertes
    boite_englobante_sans_donnees = supprimer_zones_recouvertes(
        boite_englobante, donnees_entree, geodatabase_temporaire
    )

    # Étape 3 : Conversion en polygones simples
    polygones_simple = convertir_en_polygones_simple(boite_englobante_sans_donnees, geodatabase_temporaire)

    # Étape 4 : Suppression du plus grand polygone
    supprimer_plus_grand_polygone(polygones_simple)

    # Etape 5 :
    points_sommet = extraire_sommets(polygones_simple, geodatabase_temporaire)

    # Etape 6 :
    polygones_thiessen = creer_polygones_thiessen(points_sommet, geodatabase_temporaire)

    # Etape 7 :
    polygones_thiessen_decoupes = decouper_polygones_thiessen(polygones_thiessen, polygones_simple, geodatabase_temporaire)

    # Etape 8
    resultat_jointure_spatiale = effectuer_jointure_spatiale(polygones_thiessen_decoupes,donnees_entree, geodatabase_temporaire)

    # Etape 9 :
    fusion_donnees = merge_donnees(resultat_jointure_spatiale,donnees_entree,geodatabase_temporaire)

    # Etape 10 :
    dissolve_avec_statistiques = dissoudre_avec_statistiques(fusion_donnees, geodatabase_temporaire, nom_sans_extension)

    # Etape 11 : Export des données
    exporter_resultat(dissolve_avec_statistiques, dossier_sortie)

if __name__ == "__main__":
    main()
