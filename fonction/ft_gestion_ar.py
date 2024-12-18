import arcpy
import os
from datetime import datetime


def detecter_superpositions(donnees_entree, geodatabase_temporaire):
    """
    Détecte les superpositions dans les données d'entrée après avoir filtré
    les entités avec la valeur "1.0" dans la colonne COMP.
    Si aucun auto-recouvrement n'est détecté, retourne un message approprié.
    """
    # Définir les chemins de sortie
    donnees_filtrees = os.path.join(geodatabase_temporaire, "donnees_filtrees")
    superpositions_detectees = os.path.join(geodatabase_temporaire, "superpositions_detectees")

    print(f"[{datetime.now()}] Étape 0 : Filtrage des entités avec COMP = 1.0")

    # Appliquer un filtre sur la colonne COMP pour sélectionner uniquement les valeurs égales à 1.0
    expression_filtre = "COMP = '1.0'"
    arcpy.analysis.Select(
        in_features=donnees_entree,
        out_feature_class=donnees_filtrees,
        where_clause=expression_filtre
    )

    print(f"[{datetime.now()}] Étape 1 : Détection des superpositions dans les données filtrées")

    # Détecter les superpositions dans les données filtrées
    arcpy.analysis.CountOverlappingFeatures(
        in_features=donnees_filtrees,
        out_feature_class=superpositions_detectees,
        min_overlap_count=2,
        out_overlap_table=None
    )

    # Vérifier si le résultat est vide
    if int(arcpy.management.GetCount(superpositions_detectees)[0]) == 0:
        print(f"[{datetime.now()}] Aucune superposition détectée.")
        return False  # Pas d'auto-recouvrements détectés
    else:
        print(f"[{datetime.now()}] Superpositions détectées.")
        return True  # Auto-recouvrements détectés


def gestion_ar(donnees_entree, geodatabase_temporaire):
    """
    Permet de gérer les auto-recouvrements en amont du processus,
    en réattribuant les auto-recouvrements dans l'un ou l'autre des premiers polygones concernés.
    Enregistre également le résultat final en format SHP.
    """
    dossier_sortie = r"C:\Users\Windows 11\Documents\EMONDET"
    fichier_union = os.path.join(geodatabase_temporaire, "donnee_union_ar")
    fichier_ar = os.path.join(geodatabase_temporaire, "donnee_sortie_ar")

    # Union de la table avec elle-même
    arcpy.analysis.Union([donnees_entree], fichier_union)

    # Suppression et ajout du champ Geom_c
    if "Geom_c" in [field.name for field in arcpy.ListFields(fichier_union)]:
        arcpy.management.DeleteField(fichier_union, "Geom_c")
    arcpy.management.AddField(fichier_union, "Geom_c", "TEXT")

    # Mise à jour du champ Geom_c
    with arcpy.da.UpdateCursor(fichier_union, ["SHAPE@WKT", "Geom_c"]) as cursor:
        for ligne in cursor:
            ligne[1] = ligne[0]
            cursor.updateRow(ligne)

    # Fusion des données avec elle-même
    arcpy.analysis.PairwiseDissolve(
        in_features=fichier_union,
        out_feature_class=fichier_ar,
        dissolve_field="Geom_c",
        statistics_fields="",
    )

    # Attribution du nouveau polygone au plus proche polygone
    with arcpy.da.UpdateCursor(fichier_ar, ["SHAPE@", "Geom_c"]) as update_cursor:
        for new_polygon in update_cursor:
            min_distance = float("inf")
            closest_polygon = None
            new_geom = new_polygon[0]

            with arcpy.da.SearchCursor(fichier_ar, ["SHAPE@", "Geom_c"]) as search_cursor:
                for existing_polygon in search_cursor:
                    if new_geom.equals(existing_polygon[0]):
                        continue  # Skip the same polygon
                    distance = new_geom.distanceTo(existing_polygon[0])
                    if distance < min_distance or (
                            distance == min_distance and existing_polygon[0].area < new_geom.area):
                        min_distance = distance
                        closest_polygon = existing_polygon

            if closest_polygon:
                new_polygon[1] = closest_polygon[1]  # Update with closest polygon's Geom_c value
                update_cursor.updateRow(new_polygon)

    arcpy.management.DeleteField(fichier_ar, ["Geom_c"])

    # Enregistrement du résultat en SHP
    fichier_shp_sortie = os.path.join(dossier_sortie, "donnee_sortie_ar.shp")
    arcpy.conversion.FeatureClassToShapefile(
        [fichier_ar],
        dossier_sortie
    )

    print(f"[{datetime.now()}] Résultat exporté en SHP : {fichier_shp_sortie}")

    # return fichier_shp_sortie
