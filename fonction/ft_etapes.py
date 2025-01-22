import arcpy
import os
from datetime import datetime


def generer_boite_englobante(donnee_entre_v2, geodatabase_temporaire):
    """
    Génère une boîte englobante autour des données d'entrée.
    """
    boite_englobante = os.path.join(geodatabase_temporaire, "boite_englobante")
    print(f"[{datetime.now()}] Étape 1 : Générer la boîte englobante")

    # Vérification des entrées
    if not arcpy.Exists(donnee_entre_v2):
        raise FileNotFoundError(f"Le fichier ou la classe d'entités '{donnee_entre_v2}' est introuvable.")

    if not arcpy.Exists(geodatabase_temporaire):
        raise FileNotFoundError(f"La géodatabase temporaire '{geodatabase_temporaire}' est introuvable.")

    if int(arcpy.management.GetCount(donnee_entre_v2)[0]) == 0:
        raise ValueError(f"La couche '{donnee_entre_v2}' ne contient aucune entité.")

    if arcpy.Exists(boite_englobante):
        arcpy.management.Delete(boite_englobante)

    try:
        arcpy.management.MinimumBoundingGeometry(
            in_features=donnee_entre_v2,
            out_feature_class=boite_englobante,
            geometry_type="ENVELOPE",
            group_option="ALL",
            group_field=None,
        )
        print(f"[{datetime.now()}] Boîte englobante créée avec succès : {boite_englobante}")
    except arcpy.ExecuteError as e:
        print(f"Erreur lors de la création de la boîte englobante : {e}")
        raise
    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")
        raise

    return boite_englobante


def supprimer_zones_recouvertes(boite_englobante, donnee_entre_v2, geodatabase_temporaire):
    """
    Supprime les zones recouvertes par les données d'entrée.
    """

    boite_englobante_sans_donnees = os.path.join(geodatabase_temporaire, "boite_englobante_sans_donnees")
    print(f"[{datetime.now()}] Étape 2 : Supprimer les zones recouvertes par les données d'entrée")
    arcpy.analysis.PairwiseErase(
        in_features=boite_englobante,
        erase_features=donnee_entre_v2,
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


def supprimer_plus_grand_polygone(polygones_simple, seuil_superficie=0.5):
    """
    Supprime tous les polygones dont la superficie dépasse un seuil spécifié (en kilomètres carrés par défaut).

    :param polygones_simple: Classe d'entités contenant les polygones.
    :param seuil_superficie: Seuil de superficie (en kilomètres carrés) au-dessus duquel les polygones seront supprimés.
    """
    print(f"[{datetime.now()}] Étape 4 : Supprimer les polygones dépassant le seuil de {seuil_superficie} km²")

    # Ajouter un champ pour stocker la superficie
    arcpy.management.AddField(polygones_simple, "Area", "DOUBLE")

    # Calculer la superficie géodésique en kilomètres carrés
    arcpy.management.CalculateGeometryAttributes(
        in_features=polygones_simple,
        geometry_property=[["Area", "AREA_GEODESIC"]],
        area_unit="SQUARE_KILOMETERS"
    )

    # Identifier le champ d'OID
    oid_field = [f.name for f in arcpy.ListFields(polygones_simple) if f.type == "OID"][0]

    # Construire une clause WHERE pour sélectionner les polygones à supprimer
    where_clause = f"Area > {seuil_superficie}"

    # Supprimer les polygones dépassant le seuil
    arcpy.management.MakeFeatureLayer(polygones_simple, "temp_layer")
    arcpy.management.SelectLayerByAttribute(
        in_layer_or_view="temp_layer",
        selection_type="NEW_SELECTION",
        where_clause=where_clause
    )

    # Supprimer les polygones sélectionnés
    rows_deleted = arcpy.management.DeleteRows("temp_layer")
    print(f"Nombre de polygones supprimés : {rows_deleted}")

    # Supprimer le champ Area pour nettoyer les données
    if "Area" in [f.name for f in arcpy.ListFields(polygones_simple)]:
        arcpy.management.DeleteField(polygones_simple, ["Area"])


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


def merge_donnees(resultat_jointure_spatiale, donnees_entree, geodatabase_temporaire):
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


def dissoudre_avec_statistiques(fusion_donnees, geodatabase_temporaire, nom_sans_extension):
    """
    Effectue une dissolution avec des statistiques sur les données fusionnées.
    """
    dissolve_avec_statistiques = os.path.join(geodatabase_temporaire, f"resultat_finale_{nom_sans_extension}_v5")
    print(f"[{datetime.now()}] Étape 10 : Dissolution avec statistiques")
    champ_dissolution = "OID_ORIG"
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
    # Suppression du préfixe "FIRST_" des noms de champs
    fields = arcpy.ListFields(dissolve_avec_statistiques)
    for field in fields:
        if field.name.startswith("FIRST_"):
            nouveau_nom = field.name.replace("FIRST_", "")
            print(f"Renommage du champ : {field.name} -> {nouveau_nom}")
            try:
                arcpy.management.AlterField(
                    in_table=dissolve_avec_statistiques,
                    field=field.name,
                    new_field_name=nouveau_nom,
                    new_field_alias=nouveau_nom
                )
            except Exception as e:
                print(f"Erreur lors du renommage du champ {field.name} : {e}")

    return dissolve_avec_statistiques

def exporter_resultat(dissolve_avec_statistiques, dossier_sortie):
    """
    Exporte le résultat final en tant que fichier shapefile.
    """
    fichier_final = os.path.join(dossier_sortie, "resultat_final_v5.shp")
    print(f"[{datetime.now()}] Étape 11 : Exporter le résultat final")
    arcpy.conversion.FeatureClassToShapefile([dissolve_avec_statistiques], dossier_sortie)
    return fichier_final

def supprimer_donnees_s_id(donnee_entre_v2):
    """
    Supprime les entités dans une classe d'entités en fonction de la valeur d'une colonne spécifique,
    puis supprime la colonne S_ID.
    """
    try:
        arcpy.env.overwriteOutput = True

        # Vérifier si la colonne existe
        fields = [f.name for f in arcpy.ListFields(donnee_entre_v2)]
        if "S_ID" not in fields:
            raise ValueError(f"La colonne 'S_ID' n'existe pas dans la classe d'entités '{donnee_entre_v2}'.")

        # Construire la clause WHERE
        where_clause = "S_ID = 'NOUVEAU'"
        print(f"Suppression des entités où S_ID = 'NOUVEAU'")

        # Utiliser l'outil Delete Features pour supprimer les entités correspondantes
        with arcpy.da.UpdateCursor(donnee_entre_v2, ["OID@"], where_clause) as cursor:
            for row in cursor:
                cursor.deleteRow()
                print(f"Entité avec OID {row[0]} supprimée.")

        print("Suppression des entités terminée.")

        # Supprimer la colonne S_ID
        arcpy.management.DeleteField(donnee_entre_v2, "S_ID")
        print("Colonne S_ID supprimée.")

    except arcpy.ExecuteError as e:
        print(f"Erreur ArcPy : {e}")
    except Exception as e:
        print(f"Erreur : {e}")

    return donnee_entre_v2