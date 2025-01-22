import arcpy
from datetime import datetime
import os
from fonction.ft_recherche_fichier import recherche_fichier

# Configuration initiale
# ----------------------
arcpy.env.overwriteOutput = True

# Définir le dossier racine et le dossier de sortie
dossier_racine = os.path.dirname(os.path.abspath(__file__))
dossier_sortie = os.path.join(dossier_racine, "output")
os.makedirs(dossier_sortie, exist_ok=True)  # Créer le dossier de sortie s'il n'existe pas

# Créer une géodatabase temporaire pour stocker les données intermédiaires
geodatabase_temporaire = os.path.join(dossier_sortie, "temp_output.gdb")
if not arcpy.Exists(geodatabase_temporaire):
    arcpy.management.CreateFileGDB(dossier_sortie, "temp_output.gdb")
print(f"Géodatabase temporaire créée : {geodatabase_temporaire}")

# Entrée utilisateur
# ------------------
nom_fichier = input("Entrez le nom du fichier (avec extension, ex: 'exemple.shp') : ")
chemin_fichier = recherche_fichier(nom_fichier)

if not chemin_fichier.lower().endswith(".shp"):
    raise ValueError("Le fichier d'entrée doit avoir l'extension '.shp'.")
if chemin_fichier:
    print(f"Fichier trouvé : {chemin_fichier}")
else:
    print(f"Le fichier '{nom_fichier}' n'a pas été trouvé sur l'ordinateur.")
    exit()

# Définir les chemins pour les données intermédiaires
# ---------------------------------------------------
donnees_entree = rf"{chemin_fichier}"
boite_englobante = os.path.join(geodatabase_temporaire, "boite_englobante")
boite_englobante_sans_donnees = os.path.join(geodatabase_temporaire, "boite_englobante_sans_donnees")
polygones_singlepart = os.path.join(geodatabase_temporaire, "polygones_simple")
points_sommets = os.path.join(geodatabase_temporaire, "points_sommets")
polygones_thiessen = os.path.join(geodatabase_temporaire, "polygones_thiessen")
polygones_thiessen_decoupes = os.path.join(geodatabase_temporaire, "polygones_thiessen_decoupes")
resultat_jointure_spatiale = os.path.join(geodatabase_temporaire, "jointure_spatiale")
fusion_donnees = os.path.join(geodatabase_temporaire, "fusion_donnees")
dissolve_avec_statistiques = os.path.join(geodatabase_temporaire, "dissolution_avec_statistiques")
superpositions_detectees = os.path.join(geodatabase_temporaire, "superpositions_detectees")

# Étape 0 : Détection des superpositions dans les données d'entrée
# -----------------------------------------------------------------
print(f"[{datetime.now()}] Étape 0 : Détection des superpositions dans les données d'entrée")
arcpy.analysis.CountOverlappingFeatures(
    in_features=donnees_entree,
    out_feature_class=superpositions_detectees,
    min_overlap_count=2,
    out_overlap_table=None
)
print(f"Superpositions détectées dans : {superpositions_detectees}")

# Étape 1 : Génération de la boîte englobante
# --------------------------------------------
print(f"[{datetime.now()}] Étape 1 : Générer la boîte englobante")
arcpy.management.MinimumBoundingGeometry(
    in_features=donnees_entree,
    out_feature_class=boite_englobante,
    geometry_type="ENVELOPE",
    group_option="ALL"
)

# Étape 2 : Suppression des zones recouvertes par les données
# ------------------------------------------------------------
print(f"[{datetime.now()}] Étape 2 : Supprimer les zones recouvertes par les données d'entrée")
arcpy.analysis.PairwiseErase(
    in_features=boite_englobante,
    erase_features=donnees_entree,
    out_feature_class=boite_englobante_sans_donnees
)

# Étape 3 : Conversion en polygones à une seule partie
# -----------------------------------------------------
print(f"[{datetime.now()}] Étape 3 : Conversion en polygones à une seule partie")
arcpy.management.MultipartToSinglepart(
    in_features=boite_englobante_sans_donnees,
    out_feature_class=polygones_singlepart
)

# Étape 4 : Calculer les surfaces et supprimer le plus grand polygone
# --------------------------------------------------------------------
print(f"[{datetime.now()}] Étape 4 : Supprimer le polygone englobant")
arcpy.management.AddField(
    in_table=polygones_singlepart,
    field_name="Area",
    field_type="DOUBLE"
)
arcpy.management.CalculateGeometryAttributes(
    in_features=polygones_singlepart,
    geometry_property=[["Area", "AREA_GEODESIC"]],
    area_unit="SQUARE_METERS"
)

# Identifier et supprimer le plus grand polygone
oid_field = [f.name for f in arcpy.ListFields(polygones_singlepart) if f.type == "OID"][0]
max_area = 0
max_area_oid = None
with arcpy.da.SearchCursor(polygones_singlepart, [oid_field, "Area"]) as cursor:
    for row in cursor:
        if row[1] > max_area:
            max_area = row[1]
            max_area_oid = row[0]

if max_area_oid is not None:
    arcpy.management.MakeFeatureLayer(polygones_singlepart, "temp_layer")
    arcpy.management.SelectLayerByAttribute(
        in_layer_or_view="temp_layer",
        selection_type="NEW_SELECTION",
        where_clause=f"{oid_field} = {max_area_oid}"
    )
    arcpy.management.DeleteRows("temp_layer")

# Étape 5 : Extraction des sommets des polygones
# -----------------------------------------------
print(f"[{datetime.now()}] Étape 5 : Extraire les sommets des polygones")
arcpy.management.FeatureVerticesToPoints(
    in_features=polygones_singlepart,
    out_feature_class=points_sommets,
    point_location="ALL"
)

# Étape 6 : Création des polygones de Thiessen
# ---------------------------------------------
print(f"[{datetime.now()}] Étape 6 : Créer des polygones de Thiessen")
arcpy.analysis.CreateThiessenPolygons(
    in_features=points_sommets,
    out_feature_class=polygones_thiessen
)

# Étape 7 : Découpage des polygones de Thiessen
# ----------------------------------------------
print(f"[{datetime.now()}] Étape 7 : Découper les polygones de Thiessen")
arcpy.analysis.Clip(
    in_features=polygones_thiessen,
    clip_features=polygones_singlepart,
    out_feature_class=polygones_thiessen_decoupes
)

# Étape 8 : Jointure spatiale
# ----------------------------
print(f"[{datetime.now()}] Étape 8 : Effectuer une jointure spatiale")
arcpy.analysis.SpatialJoin(
    target_features=polygones_thiessen_decoupes,
    join_features=donnees_entree,
    out_feature_class=resultat_jointure_spatiale,
    join_operation="JOIN_ONE_TO_ONE",
    match_option="INTERSECT"
)

# Étape 9 : Fusion des données
# -----------------------------
print(f"[{datetime.now()}] Étape 9 : Fusionner les données")
mappage_champs = arcpy.FieldMappings()
entrees = [resultat_jointure_spatiale, donnees_entree]
for couche in entrees:
    mappage_champs.addTable(couche)
arcpy.management.Merge(inputs=entrees, output=fusion_donnees, field_mappings=mappage_champs)

# Étape 10 : Dissolution avec statistiques
# -----------------------------------------
print(f"[{datetime.now()}] Étape 10 : Dissolution avec statistiques après fusion")
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

# Étape 11 : Exporter le résultat final
# --------------------------------------
print(f"[{datetime.now()}] Exportation du fichier final")
fichier_final = os.path.join(dossier_sortie, "resultat_final.shp")
arcpy.conversion.FeatureClassToShapefile([dissolve_avec_statistiques], dossier_sortie)
print(f"Fichier final exporté dans : {fichier_final}")
