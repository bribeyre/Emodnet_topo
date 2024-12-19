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
    fichier_nouveaux = os.path.join(geodatabase_temporaire, "nouveaux_polygones")
    fichier_centroïdes = os.path.join(geodatabase_temporaire, "centroides")

    # Reprojection des données d'entrée en EPSG:2154
    sr_target = arcpy.SpatialReference(2154)  # Référence spatiale EPSG:2154 (RGF93 / Lambert-93)
    donnees_entree_proj = os.path.join(geodatabase_temporaire, "donnees_entree_proj")
    arcpy.management.Project(donnees_entree, donnees_entree_proj, sr_target)

    # Ajout d'un champ ObjectID si nécessaire
    if "OBJECTID" not in [field.name for field in arcpy.ListFields(donnees_entree_proj)]:
        arcpy.management.AddField(donnees_entree_proj, "OBJECTID", "LONG")
        with arcpy.da.UpdateCursor(donnees_entree_proj, ["OBJECTID"]) as cursor:
            object_id = 1
            for row in cursor:
                row[0] = object_id
                cursor.updateRow(row)
                object_id += 1

    # Ajout d'un champ UniqueID si nécessaire
    if "UniqueID" not in [field.name for field in arcpy.ListFields(donnees_entree_proj)]:
        arcpy.management.AddField(donnees_entree_proj, "UniqueID", "LONG")
        with arcpy.da.UpdateCursor(donnees_entree_proj, ["UniqueID"]) as cursor:
            unique_id = 1
            for row in cursor:
                row[0] = unique_id
                cursor.updateRow(row)
                unique_id += 1

    # Union de la table avec elle-même
    arcpy.analysis.Union([donnees_entree_proj], fichier_union)

    # Suppression et ajout du champ Geom_c
    if "Geom_c" in [field.name for field in arcpy.ListFields(fichier_union)]:
        arcpy.management.DeleteField(fichier_union, "Geom_c")
    arcpy.management.AddField(fichier_union, "Geom_c", "TEXT", field_length=10000)

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

    # Étape 2 : Calcul des centroïdes des polygones
    arcpy.management.FeatureToPoint(
        in_features=fichier_union,
        out_feature_class=fichier_centroïdes,
        point_location="INSIDE"
    )

    # Étape 3 : Identifier les nouveaux polygones
    # Supprimer les polygones originaux des polygones résultant de l'union
    arcpy.analysis.Erase(
        in_features=fichier_union,        # Polygones après union
        erase_features=donnees_entree_proj,   # Polygones d'origine
        out_feature_class=fichier_nouveaux
    )

    # Étape 4 : Associer chaque nouveau polygone au polygone existant le plus proche
    fichier_jointure = os.path.join(geodatabase_temporaire, "jointure_spatiale")
    arcpy.analysis.SpatialJoin(
        target_features=fichier_centroïdes,  # Centroïdes des polygones nouveaux
        join_features=donnees_entree_proj,  # Polygones d'origine
        out_feature_class=fichier_jointure,  # Fichier de sortie de la jointure
        join_type="KEEP_ALL",  # Inclure tous les centroïdes, même s'ils n'ont pas de correspondance
        match_option="CLOSEST"  # Associer au polygone le plus proche
    )

    # Étape finale : Exporter les nouvelles géométries séparément
    fichier_nouveaux_sortie = os.path.join(dossier_sortie, "nouveaux_polygones.shp")
    arcpy.conversion.FeatureClassToShapefile(
        [fichier_nouveaux],
        dossier_sortie
    )

    print(f"[{datetime.now()}] Nouveaux polygones exportés en SHP : {fichier_nouveaux_sortie}")
    return fichier_nouveaux_sortie
