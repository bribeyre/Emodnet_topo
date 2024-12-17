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


def generer_boite_englobante(donnees_entree, geodatabase_temporaire):
    """
    Génère une boîte englobante autour des données d'entrée.
    """
    boite_englobante = os.path.join(geodatabase_temporaire, "boite_englobante")
    print(f"[{datetime.now()}] Étape 1 : Générer la boîte englobante")
    arcpy.management.MinimumBoundingGeometry(
        in_features=donnees_entree,
        out_feature_class=boite_englobante,
        geometry_type="ENVELOPE",
        group_option="ALL"
    )
    return boite_englobante


def supprimer_zones_recouvertes(boite_englobante, donnees_entree, geodatabase_temporaire):
    """
    Supprime les zones recouvertes par les données d'entrée.
    """
    boite_englobante_sans_donnees = os.path.join(geodatabase_temporaire, "boite_englobante_sans_donnees")
    print(f"[{datetime.now()}] Étape 2 : Supprimer les zones recouvertes par les données d'entrée")
    arcpy.analysis.PairwiseErase(
        in_features=boite_englobante,
        erase_features=donnees_entree,
        out_feature_class=boite_englobante_sans_donnees
    )
    return boite_englobante_sans_donnees


def convertir_en_polygones_simple(boite_englobante_sans_donnees, geodatabase_temporaire):
    """
    Convertit les polygones multiparts en polygones simples.
    """
    polygones_simple = os.path.join(geodatabase_temporaire, "polygones_simple")
    print(f"[{datetime.now()}] Étape 3 : Conversion en polygones à une seule partie")
    arcpy.management.MultipartToSinglepart(
        in_features=boite_englobante_sans_donnees,
        out_feature_class=polygones_simple
    )
    return polygones_simple


def supprimer_plus_grand_polygone(polygones_simple):
    """
    Supprime le polygone avec la plus grande superficie.
    """
    print(f"[{datetime.now()}] Étape 4 : Supprimer le polygone englobant")
    arcpy.management.AddField(polygones_simple, "Area", "DOUBLE")
    arcpy.management.CalculateGeometryAttributes(
        in_features=polygones_simple,
        geometry_property=[["Area", "AREA_GEODESIC"]],
        area_unit="SQUARE_METERS"
    )
    oid_field = [f.name for f in arcpy.ListFields(polygones_simple) if f.type == "OID"][0]
    max_area = 0
    max_area_oid = None

    with arcpy.da.SearchCursor(polygones_simple, [oid_field, "Area"]) as cursor:
        for row in cursor:
            if row[1] > max_area:
                max_area = row[1]
                max_area_oid = row[0]

    if max_area_oid is not None:
        arcpy.management.MakeFeatureLayer(polygones_simple, "temp_layer")
        arcpy.management.SelectLayerByAttribute(
            in_layer_or_view="temp_layer",
            selection_type="NEW_SELECTION",
            where_clause=f"{oid_field} = {max_area_oid}"
        )
        arcpy.management.DeleteRows("temp_layer")


def extraire_sommets(polygones_simple, geodatabase_temporaire):
    """
    Extrait les sommets des polygones.
    """
    points_sommets = os.path.join(geodatabase_temporaire, "points_sommets")
    print(f"[{datetime.now()}] Étape 5 : Extraire les sommets des polygones")
    arcpy.management.FeatureVerticesToPoints(
        in_features=polygones_simple,
        out_feature_class=points_sommets,
        point_location="ALL"
    )
    return points_sommets


def creer_polygones_thiessen(points_sommets, geodatabase_temporaire):
    """
    Crée des polygones de Thiessen à partir des sommets.
    """
    polygones_thiessen = os.path.join(geodatabase_temporaire, "polygones_thiessen")
    print(f"[{datetime.now()}] Étape 6 : Créer des polygones de Thiessen")
    arcpy.analysis.CreateThiessenPolygons(
        in_features=points_sommets,
        out_feature_class=polygones_thiessen
    )
    return polygones_thiessen


def decouper_polygones_thiessen(polygones_thiessen, polygones_simple, geodatabase_temporaire):
    """
    Découpe les polygones de Thiessen avec les polygones simples.
    """
    polygones_thiessen_decoupes = os.path.join(geodatabase_temporaire, "polygones_thiessen_decoupes")
    print(f"[{datetime.now()}] Étape 7 : Découper les polygones de Thiessen")
    arcpy.analysis.Clip(
        in_features=polygones_thiessen,
        clip_features=polygones_simple,
        out_feature_class=polygones_thiessen_decoupes
    )
    return polygones_thiessen_decoupes


def effectuer_jointure_spatiale(polygones_thiessen_decoupes, donnees_entree, geodatabase_temporaire):
    """
    Effectue une jointure spatiale entre les polygones découpés et les données d'entrée.
    """
    resultat_jointure_spatiale = os.path.join(geodatabase_temporaire, "jointure_spatiale")
    print(f"[{datetime.now()}] Étape 8 : Effectuer une jointure spatiale")
    arcpy.analysis.SpatialJoin(
        target_features=polygones_thiessen_decoupes,
        join_features=donnees_entree,
        out_feature_class=resultat_jointure_spatiale,
        join_operation="JOIN_ONE_TO_ONE",
        match_option="INTERSECT"
    )
    return resultat_jointure_spatiale


def fusionner_donnees(resultat_jointure_spatiale, donnees_entree, geodatabase_temporaire):
    """
    Fusionne les données après jointure spatiale.
    """
    fusion_donnees = os.path.join(geodatabase_temporaire, "fusion_donnees")
    print(f"[{datetime.now()}] Étape 9 : Fusionner les données")
    mappage_champs = arcpy.FieldMappings()
    entrees = [resultat_jointure_spatiale, donnees_entree]
    for couche in entrees:
        mappage_champs.addTable(couche)
    arcpy.management.Merge(inputs=entrees, output=fusion_donnees, field_mappings=mappage_champs)
    return fusion_donnees


def dissoudre_avec_statistiques(fusion_donnees, geodatabase_temporaire):
    """
    Effectue une dissolution avec des statistiques sur les données fusionnées.
    """
    dissolve_avec_statistiques = os.path.join(geodatabase_temporaire, "dissolution_avec_statistiques")
    print(f"[{datetime.now()}] Étape 10 : Dissolution avec statistiques")
    champ_dissolution = "id_geom"
    champs_statistiques = [
        (field.name, "FIRST") for field in arcpy.ListFields(fusion_donnees)
        if field.name != champ_dissolution and field.type not in ["Geometry", "OID"]
    ]
    arcpy.management.Dissolve(
        in_features=fusion_donnees,
        out_feature_class=dissolve_avec_statistiques,
        dissolve_field=champ_dissolution,
        statistics_fields=champs_statistiques
    )
    return dissolve_avec_statistiques


def exporter_resultat(dissolve_avec_statistiques, dossier_sortie):
    """
    Exporte le résultat final en tant que fichier shapefile.
    """
    fichier_final = os.path.join(dossier_sortie, "resultat_final.shp")
    print(f"[{datetime.now()}] Étape 11 : Exporter le résultat final")
    arcpy.conversion.FeatureClassToShapefile([dissolve_avec_statistiques], dossier_sortie)
    return fichier_final
