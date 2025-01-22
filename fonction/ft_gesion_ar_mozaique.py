import arcpy
import os

def gestion_moz(geodatabase_temporaire, donnees_entree, nom_fichier, dossier_sortie):
    """
    Fonction pour gérer la mosaïque des données géographiques en réalisant une union,
    en identifiant les géométries identiques et en filtrant certaines entités.

    Étapes principales :
    1. Réalise une union de la couche d'entrée avec elle-même.
    2. Ajoute des champs nécessaires pour le traitement.
    3. Identifie les géométries identiques et leur attribue un numéro séquentiel.
    4. Supprime les entités avec certains numéros spécifiques.
    5. Exporte le fichier final dans le dossier de sortie.
    """
    # Chemins des données
    temp_gdb = geodatabase_temporaire

    # Fichiers intermédiaires et finaux
    fichier_union = os.path.join(temp_gdb, f"{nom_fichier}_union_ar")

    # Étape 1 : Union de la couche avec elle-même
    arcpy.analysis.Union([donnees_entree, donnees_entree], fichier_union)

    # Étape 2 : Ajouter les champs nécessaires
    champ_sequence = "Num_Sequence"
    champ_comp = "COMP"

    if not arcpy.ListFields(fichier_union, champ_sequence):
        arcpy.AddField_management(fichier_union, champ_sequence, "LONG")

    # Étape 3 : Identifier les géométries identiques et attribuer un numéro
    geom_dict = {}

    with arcpy.da.UpdateCursor(fichier_union, ["SHAPE@", champ_sequence, champ_comp]) as cursor:
        for row in cursor:
            geom = row[0].WKT  # Représentation WKT pour identifier les géométries
            if geom not in geom_dict:
                geom_dict[geom] = 1  # Nouvelle géométrie
                row[2] = None  # Pas de recouvrement pour une nouvelle géométrie
            else:
                geom_dict[geom] += 1  # Géométrie existante, incrémenter le compteur
                row[2] = "unknown"  # Marquer comme auto-recouvrée ou identique

            row[1] = geom_dict[geom]  # Mettre à jour Num_Sequence
            cursor.updateRow(row)

    print("Numérotation des géométries identiques et mise à jour du champ COMP terminée.")

    # Étape 4 : Supprimer les polygones avec Num_Sequence = 2 ou 4
    with arcpy.da.UpdateCursor(fichier_union, [champ_sequence]) as cursor:
        for row in cursor:
            if row[0] in [2, 4, 6, 8]:  # Vérifier si la valeur est 2, 4, 6 ou 8
                cursor.deleteRow()  # Supprimer la ligne

    print("Suppression des numéros 2, 4, 6 et 8 terminée.")

    # Étape 5 : Exporter le résultat final
    fichier_sortie = os.path.join(dossier_sortie, f"{nom_fichier}_avec_mozaique.shp")
    arcpy.management.CopyFeatures(fichier_union, fichier_sortie)
    print(f"Fichier exporté : {fichier_sortie}")
