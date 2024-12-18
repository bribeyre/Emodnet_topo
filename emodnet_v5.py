import arcpy
from datetime import datetime
import os
from fonction.ft_recherche_fichier import recherche_fichier

# Configuration initiale
arcpy.env.overwriteOutput = True

# Dossier racine (chemins relatifs)
# Obtenir le chemin du dossier racine
dossier_racine = os.path.dirname(os.path.abspath(__file__))
# Construire le chemin du dossier de sortie
dossier_sortie = os.path.join(dossier_racine, "output")
# Créer le dossier de sortie s'il n'existe pas
os.makedirs(dossier_sortie, exist_ok=True)

# Vérifier et créer le dossier de sortie
if not os.path.exists(dossier_sortie):
    os.makedirs(dossier_sortie)

# Créer une géodatabase temporaire
geodatabase_temporaire = os.path.join(dossier_sortie, "temp_output.gdb")
if not arcpy.Exists(geodatabase_temporaire):
    arcpy.management.CreateFileGDB(dossier_sortie, "temp_output.gdb")
print(f"Géodatabase temporaire créée : {geodatabase_temporaire}")

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
boite_englobante = os.path.join(geodatabase_temporaire, "boite_englobante")
boite_englobante_sans_donnees = os.path.join(geodatabase_temporaire, "boite_englobante_sans_donnees")
polygones_singlepart = os.path.join(geodatabase_temporaire, "polygones_simple")
points_sommets = os.path.join(geodatabase_temporaire, "points_sommets")
polygones_thiessen = os.path.join(geodatabase_temporaire, "polygones_thiessen")
polygones_thiessen_decoupes = os.path.join(geodatabase_temporaire, "polygones_thiessen_decoupes")
resultat_jointure_spatiale = os.path.join(geodatabase_temporaire, "jointure_spatiale")
fusion_donnees = os.path.join(geodatabase_temporaire, "fusion_donnees")
dissolve_avec_statistiques = os.path.join(geodatabase_temporaire, "dissolution_avec_statistiques")

# Étape 1 : Générer la boîte englobante
print(f"[{datetime.now()}] Étape 1 : Générer la boîte englobante")
arcpy.management.MinimumBoundingGeometry(
    in_features=donnees_entree,
    out_feature_class=boite_englobante,
    geometry_type="ENVELOPE",
    group_option="ALL"
)

# Étape 2 : Supprimer les zones recouvertes par les données d'entrée
print(f"[{datetime.now()}] Étape 2 : Supprimer les zones recouvertes par les données d'entrée")
arcpy.analysis.PairwiseErase(
    in_features=boite_englobante,
    erase_features=donnees_entree,
    out_feature_class=boite_englobante_sans_donnees
)

# Étape 3 : Conversion en polygones à une seule partie
print(f"[{datetime.now()}] Étape 3 : Conversion en polygones à une seule partie")
arcpy.management.MultipartToSinglepart(
    in_features=boite_englobante_sans_donnees,
    out_feature_class=polygones_singlepart
)

# Étape 4 : Calculer les surfaces et supprimer le plus grand polygone
print(f"[{datetime.now()}] Étape 4 : Supprimer le polygone englobant")
arcpy.management.AddField(
    in_table=polygones_singlepart,
    field_name="Area",
    field_type="DOUBLE"
)
arcpy.management.CalculateGeometryAttributes(
    in_features=polygones_singlepart,
    geometry_property=[["Area", "AREA_GEODESIC"]],
    area_unit="SQUARE_METERS",
    coordinate_format="SAME_AS_INPUT"
)

# Identifier et supprimer le polygone avec la plus grande superficie
print(f"[{datetime.now()}] Identification du polygone avec la plus grande superficie...")
oid_field = [f.name for f in arcpy.ListFields(polygones_singlepart) if f.type == "OID"][0]
print(f"Champ d'identifiant unique détecté : {oid_field}")

max_area = 0
max_area_oid = None
with arcpy.da.SearchCursor(polygones_singlepart, [oid_field, "Area"]) as cursor:
    for row in cursor:
        if row[1] > max_area:  # Vérifie si la superficie est plus grande
            max_area = row[1]
            max_area_oid = row[0]

if max_area_oid is not None:
    print(f"Polygone sélectionné pour suppression : {max_area_oid}, superficie : {max_area:.2f} m².")
    arcpy.management.MakeFeatureLayer(polygones_singlepart, "temp_layer")
    arcpy.management.SelectLayerByAttribute(
        in_layer_or_view="temp_layer",
        selection_type="NEW_SELECTION",
        where_clause=f"{oid_field} = {max_area_oid}"
    )
    arcpy.management.DeleteRows("temp_layer")
    print("Le polygone avec la plus grande superficie a été supprimé.")
else:
    print("Aucun polygone avec une superficie valide n'a été trouvé.")

# Étape 5 : Extraire les sommets des polygones
print(f"[{datetime.now()}] Étape 5 : Extraire les sommets des polygones")
arcpy.management.FeatureVerticesToPoints(
    in_features=polygones_singlepart,
    out_feature_class=points_sommets,
    point_location="ALL"
)

# Étape 6 : Créer des polygones de Thiessen
print(f"[{datetime.now()}] Étape 6 : Créer des polygones de Thiessen")
arcpy.analysis.CreateThiessenPolygons(
    in_features=points_sommets,
    out_feature_class=polygones_thiessen
)

# Étape 7 : Découper les polygones de Thiessen
print(f"[{datetime.now()}] Étape 7 : Découper les polygones de Thiessen")
arcpy.analysis.Clip(
    in_features=polygones_thiessen,
    clip_features=polygones_singlepart,
    out_feature_class=polygones_thiessen_decoupes
)

# Étape 8 : Effectuer une jointure spatiale
print(f"[{datetime.now()}] Étape 8 : Effectuer une jointure spatiale")
arcpy.analysis.SpatialJoin(
    target_features=polygones_thiessen_decoupes,
    join_features=donnees_entree,
    out_feature_class=resultat_jointure_spatiale,
    join_operation="JOIN_ONE_TO_ONE",
    join_type="KEEP_ALL",
    match_option="INTERSECT"
)

# Étape 9 : Fusionner les données
print(f"[{datetime.now()}] Étape 10 : Fusionner les données")

# Initialiser l'objet FieldMappings
mappage_champs = arcpy.FieldMappings()

# Ajouter les couches d'entrée au FieldMappings
entrees = [resultat_jointure_spatiale, donnees_entree]
for couche in entrees:
    mappage_champs.addTable(couche)

# Identifier les champs ayant le même nom et les fusionner
noms_champs_uniques = set([champ.name for champ in arcpy.ListFields(resultat_jointure_spatiale)] +
                          [champ.name for champ in arcpy.ListFields(donnees_entree)])

for nom_champ in noms_champs_uniques:
    # Créer un FieldMap pour le champ
    mappage_champ = arcpy.FieldMap()

    # Ajouter le champ depuis chaque jeu de données s'il existe
    for couche in entrees:
        try:
            mappage_champ.addInputField(couche, nom_champ)
        except Exception:
            pass  # Ignore si le champ n'existe pas dans cette couche

    # Définir les propriétés du champ combiné
    champ_sortie = mappage_champ.outputField
    champ_sortie.name = nom_champ  # Conserver le nom d'origine
    champ_sortie.aliasName = f"{nom_champ}"  # Alias descriptif
    mappage_champ.outputField = champ_sortie

    # Ajouter ce FieldMap au FieldMappings
    mappage_champs.addFieldMap(mappage_champ)

# Exécuter la fusion avec les FieldMappings personnalisés
arcpy.management.Merge(inputs=entrees, output=fusion_donnees, field_mappings=mappage_champs)

# Étape 10 : Dissolution avec statistiques après fusion
print(f"[{datetime.now()}] Étape 11 : Dissolution avec statistiques après fusion")
champ_dissolution = "id_geom"
champs_statistiques = [
    (field.name, "FIRST") for field in arcpy.ListFields(fusion_donnees)
    if field.name != champ_dissolution and field.type not in ["Geometry", "OID"]
]
arcpy.management.Dissolve(
    in_features=fusion_donnees,
    out_feature_class=dissolve_avec_statistiques,
    dissolve_field=champ_dissolution,
    statistics_fields=champs_statistiques,
    multi_part="MULTI_PART"
)

# Renommer les champs pour supprimer "FIRST_"
print(f"[{datetime.now()}] Renommage des champs pour supprimer 'FIRST_'")
output_fields = arcpy.ListFields(dissolve_avec_statistiques)

# Liste des noms de champs existants
existing_field_names = [field.name for field in output_fields]

for field in output_fields:
    if field.name.startswith("FIRST_"):
        new_name = field.name.replace("FIRST_", "")
        # Vérifier si le nouveau nom existe déjà
        if new_name in existing_field_names:
            print(f"Nom déjà existant, ignoré : {field.name} -> {new_name}")
            continue
        try:
            # Renommer le champ
            arcpy.management.AlterField(
                in_table=dissolve_avec_statistiques,
                field=field.name,
                new_field_name=new_name
            )
            print(f"Renommé : {field.name} -> {new_name}")
            # Ajouter le nouveau nom à la liste des champs existants
            existing_field_names.append(new_name)
        except Exception as e:
            print(f"Erreur lors du renommage : {field.name} -> {new_name}. {e}")

print(f"[{datetime.now()}] Processus terminé. Résultat final dans {dissolve_avec_statistiques}")

# Exporter le résultat final dans le dossier de sortie
fichier_final = os.path.join(dossier_sortie, "resultat_final.shp")
arcpy.conversion.FeatureClassToShapefile(
    [dissolve_avec_statistiques],  # Dissolution finale
    dossier_sortie
)
print(f"Fichier final exporté dans : {fichier_final}")