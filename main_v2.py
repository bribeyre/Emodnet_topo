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
    exporter_resultat
)
from fonction.ft_gestion_ar import (detecter_superpositions,
                                    gestion_ar)
from fonction.ft_recherche_fichier import recherche_fichier
def main():
    """
    Programme principal exécutant toutes les étapes du traitement spatial.
    """
    # Étape 0 : Initialisation
    dossier_racine, dossier_sortie, geodatabase_temporaire = initialiser_env()

    # Entrée utilisateur pour le fichier shapefile
    # Entrée utilisateur pour le nom du fichier
    nom_fichier = input("Entrez le nom du fichier (avec extension, ex: 'exemple.shp') : ")

    # Démarrer la recherche
    chemin_fichier = recherche_fichier(nom_fichier)

    if not chemin_fichier.lower().endswith(".shp"):
        raise ValueError("Le fichier d'entrée doit avoir l'extension '.shp'.")
    if chemin_fichier:
        print(f"Fichier trouvé : {chemin_fichier}")
    else:
        print(f"Le fichier '{nom_fichier}' n'a pas été trouvé sur l'ordinateur.")

    # Chemins d'accès aux données dans la géodatabase
    donnees_entree = rf"{chemin_fichier}"
    print(donnees_entree)

    # Étape 0 : Détection des superpositions
    # resultat = detecter_superpositions(donnees_entree, geodatabase_temporaire)
    # if resultat:
        # print("Des auto-recouvrements ont été détectés.")
    #    gestion_ar(donnees_entree, geodatabase_temporaire)
    # else:
        # print("Aucun auto-recouvrement détecté.")
    # Etape 1 : Gestions des auto-recouvrement
    gestion_ar(donnees_entree, geodatabase_temporaire)

if __name__ == "__main__":
    main()
