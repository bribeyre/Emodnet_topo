import arcpy
import os
from datetime import datetime



def detecter_superpositions(donnees_entree, geodatabase_temporaire):
    """
    Détecte les superpositions dans les données d'entrée et génère un fichier de sortie.
    """
    superpositions_detectees = os.path.join(geodatabase_temporaire, "superpositions_detectees")
    print(f"[{datetime.now()}] Étape 0 : Détection des superpositions dans les données d'entrée")
    arcpy.analysis.CountOverlappingFeatures(
        in_features=donnees_entree,
        out_feature_class=superpositions_detectees,
        min_overlap_count=2,
        out_overlap_table=None
    )
    return superpositions_detectees

def gestion_ar(donnee,geodatabase_temporaire,):

    """
    Permet de gerer les auto-recouvrement en amont du processus,
    il permet de réatribuer l'auto-recouvrement dans l'un ou l'autre des premier polygone conserner
    """

    fichier_union = os.path.join(geodatabase_temporaire, f"donnee_union_ar")
    fichier_ar = os.path.join(geodatabase_temporaire, f"donnee_sortie_ar")

    # Union de la table avec elle-même
    arcpy.analysis.Union([donnee], fichier_union)

    # Suppression et ajout du champ Geom_Copy
    if "Geom_Copy" in [field.name for field in arcpy.ListFields(fichier_union)]:
        arcpy.management.DeleteField(fichier_union, "Geom_Copy")
    arcpy.management.AddField(fichier_union, "Geom_Copy", "TEXT")

    # Mise à jour du champ Geom_Copy
    with arcpy.da.UpdateCursor(fichier_union, ["SHAPE@WKT", "Geom_Copy"]) as cursor:
        for ligne in cursor:
            ligne[1] = ligne[0]
            cursor.updateRow(ligne)

    # Fusion des données avec elle-même
    arcpy.analysis.PairwiseDissolve(
        in_features=fichier_union,
        out_feature_class=fichier_ar,
        dissolve_field="Geom_Copy",
        statistics_fields="",
    )

    # Attribution du nouveau polygone au plus proche polygone
    with arcpy.da.UpdateCursor(fichier_ar, ["SHAPE@", "Geom_Copy"]) as update_cursor:
        for new_polygon in update_cursor:
            min_distance = float("inf")
            closest_polygon = None
            new_geom = new_polygon[0]

            with arcpy.da.SearchCursor(fichier_ar, ["SHAPE@", "Geom_Copy"]) as search_cursor:
                for existing_polygon in search_cursor:
                    if new_geom.equals(existing_polygon[0]):
                        continue  # Skip the same polygon
                    distance = new_geom.distanceTo(existing_polygon[0])
                    if distance < min_distance or (
                            distance == min_distance and existing_polygon[0].area < new_geom.area):
                        min_distance = distance
                        closest_polygon = existing_polygon

            if closest_polygon:
                new_polygon[1] = closest_polygon[1]  # Update with closest polygon's Geom_Copy value
                update_cursor.updateRow(new_polygon)

    arcpy.management.DeleteField(fichier_ar, ["Geom_Copy"])

    return fichier_ar
