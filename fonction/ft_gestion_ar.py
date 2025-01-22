import arcpy
import os
from datetime import datetime
import hashlib



def detecter_superpositions(donnees_entree, geodatabase_temporaire):
    """
    Détecte les superpositions dans les données d'entrée et génère un fichier de sortie.
    """
    superpositions_detectees = os.path.join(geodatabase_temporaire, "superpositions_detectees")
    donnees_filtrees = os.path.join(geodatabase_temporaire, "donnees_filtrees")

    # Vérifier si le champ COMP existe
    fields = [f.name for f in arcpy.ListFields(donnees_entree)]
    if "COMP" in fields:
        print(f"[{datetime.now()}] Étape 0 : Filtrage des données avec COMP = '1,0'")
        arcpy.conversion.FeatureClassToFeatureClass(
            in_features=donnees_entree,
            out_path=geodatabase_temporaire,
            out_name="donnees_filtrees",
            where_clause="COMP = '1,0'"
        )
    else:
        print(f"[{datetime.now()}] Avertissement : Le champ 'COMP' est absent. Aucune donnée n'as étais filtrés pour enlever les doublons logique.")
        donnees_filtrees = donnees_entree  # Utiliser les données originales si le champ COMP est absent

    # Détection des superpositions
    print(f"[{datetime.now()}] Étape 1 : Détection des superpositions dans les données filtrées")
    arcpy.analysis.CountOverlappingFeatures(
        in_features=donnees_filtrees,
        out_feature_class=superpositions_detectees,
        min_overlap_count=2,
        out_overlap_table=None
    )

    return superpositions_detectees

def gestion_ar(donnee, geodatabase_temporaire):
    """
    Permet de gérer les auto-recouvrements en amont du processus,
    tout en conservant un maximum de champs lors du PairwiseDissolve
    (grâce à un statistics_fields dynamique).
    On retire ici les étapes 7 et 8 (Spatial Join et NearTable).
    """
    # 1) Préparation : Champ OID_ORIG pour tracer l'ObjectID initial
    if "OID_ORIG" not in [f.name for f in arcpy.ListFields(donnee)]:
        arcpy.management.AddField(donnee, "OID_ORIG", "LONG")
        with arcpy.da.UpdateCursor(donnee, ["OID@", "OID_ORIG"]) as cur:
            for row in cur:
                row[1] = row[0]
                cur.updateRow(row)

    # 2) Union
    fichier_union = os.path.join(geodatabase_temporaire, "donnee_union_ar")
    fichier_ar = os.path.join(geodatabase_temporaire, "donnee_sortie_ar")

    arcpy.analysis.Union([donnee], fichier_union)

    if "G_hash" not in [f.name for f in arcpy.ListFields(fichier_union)]:
        arcpy.management.AddField(fichier_union, "G_hash", "TEXT", field_length=255)

    # Calculer un hachage basé sur le WKT
    with arcpy.da.UpdateCursor(fichier_union, ["SHAPE@WKT", "G_hash"]) as cur:
        for row in cur:
            if row[0]:
                row[1] = hashlib.md5(row[0].encode('utf-8')).hexdigest()
            else:
                row[1] = None
            cur.updateRow(row)

        # 4) PairwiseDissolve avec CONCATENATE pour OID_ORIG
    champs_statistiques = []
    for field in arcpy.ListFields(fichier_union):
        if field.name not in ["G_hash", "Shape"]:  # Exclure le champ de dissolution et la géométrie
            if field.name == "OID_ORIG":
                champs_statistiques.append((field.name, "CONCATENATE"))
            elif field.type not in ["Geometry", "OID"]:
                champs_statistiques.append((field.name, "FIRST"))

    arcpy.analysis.PairwiseDissolve(
        in_features=fichier_union,
        out_feature_class=fichier_ar,
        dissolve_field="G_hash",
        statistics_fields=champs_statistiques
    )

    # -- DEBUG : Afficher les champs après le PairwiseDissolve
    dissolve_fields = [f.name for f in arcpy.ListFields(fichier_ar)]
    print("\n[DEBUG] Champs de 'fichier_ar' (après PairwiseDissolve) :")
    for field_name in dissolve_fields:
        print("  -", field_name)

    # 5) Renommer le champ CONCAT_OID_ORIG en OID_ORIG
    try:
        arcpy.management.AlterField(
            in_table=fichier_ar,
            field="CONCATENATE_OID_ORIG",  # Nom du champ créé par "CONCATENATE"
                new_field_name="OID_ORIG",
            new_field_alias="OID_ORIG"
        )
        print("Le champ 'CONCAT_OID_ORIG' a été renommé en 'OID_ORIG'.")
    except arcpy.ExecuteError:
        pass

    # 6) Ajuster S_ID selon la présence de ";"
    if "S_ID" not in [f.name for f in arcpy.ListFields(fichier_ar)]:
        arcpy.management.AddField(fichier_ar, "S_ID", "TEXT", field_length=50)

    with arcpy.da.UpdateCursor(fichier_ar, ["OID_ORIG", "S_ID"]) as cur:
        for row in cur:
            if row[0] and ";" in row[0]:
                row[1] = "NOUVEAU"
            else:
                row[1] = "EXISTANT"
            cur.updateRow(row)

    # 7) Nettoyage du champ G_copy
    if "G_hash" in [fld.name for fld in arcpy.ListFields(fichier_ar)]:
        arcpy.management.DeleteField(fichier_ar, ["G_copy"])

    # 8) Supprimer le préfixe "FIRST_" des noms de colonnes
    fields_to_rename = [
        f for f in arcpy.ListFields(fichier_ar)
        if f.name.startswith("FIRST_")
    ]
    for field in fields_to_rename:
        new_name = field.name.replace("FIRST_", "")
        try:
            arcpy.management.AlterField(
                in_table=fichier_ar,
                field=field.name,
                new_field_name=new_name,
                new_field_alias=new_name
            )
            print(f"Le champ '{field.name}' a été renommé en '{new_name}'.")
        except arcpy.ExecuteError:
            print(f"Erreur lors du renommage du champ '{field.name}'.")
    # 8) Export final
    dossier_sortie_shp = r"C:\Users\bribeyre\OneDrive - MNHN\Documents"
    shp_path = os.path.join(dossier_sortie_shp, "resultat_gestion_auto.shp")

    if arcpy.Exists(shp_path):
        arcpy.management.Delete(shp_path)
    arcpy.management.CopyFeatures(fichier_ar, shp_path)

    return shp_path