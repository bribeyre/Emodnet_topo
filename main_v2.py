import arcpy
from fonction.ft_int_env import initialiser_env
from fonction.ft_etapes import (
    detecter_superpositions,
    generer_boite_englobante,
    supprimer_zones_recouvertes,
    convertir_en_polygones_simple,
    supprimer_plus_grand_polygone,
    extraire_sommets,
    creer_polygones_thiessen,
    decouper_polygones_thiessen,
    effectuer_jointure_spatiale,
    fusionner_donnees,
    dissoudre_avec_statistiques,
    exporter_resultat
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

    # Étape 0 : Détection des superpositions
    detecter_superpositions(donnees_entree, geodatabase_temporaire)

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

    # Étape 5 : Extraction des sommets
    points_sommets = extraire_sommets(polygones_simple, geodatabase_temporaire)

    # Étape 6 : Création de polygones de Thiessen
    polygones_thiessen = creer_polygones_thiessen(points_sommets, geodatabase_temporaire)

    # Étape 7 : Découpage des polygones de Thiessen
    polygones_thiessen_decoupes = decouper_polygones_thiessen(polygones_thiessen, polygones_simple, geodatabase_temporaire)

    # Étape 8 : Jointure spatiale
    resultat_jointure_spatiale = effectuer_jointure_spatiale(polygones_thiessen_decoupes, donnees_entree, geodatabase_temporaire)

    # Étape 9 : Fusion des données
    fusion_donnees = fusionner_donnees(resultat_jointure_spatiale, donnees_entree, geodatabase_temporaire)

    # Étape 10 : Dissolution avec statistiques
    dissolve_avec_statistiques = dissoudre_avec_statistiques(fusion_donnees, geodatabase_temporaire)

    # Étape 11 : Exportation du résultat final
    exporter_resultat(dissolve_avec_statistiques, dossier_sortie)

if __name__ == "__main__":
    main()
