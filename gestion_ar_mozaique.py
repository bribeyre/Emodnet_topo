import os
import arcpy
from sqlalchemy import text


def gestion_auto_recouvrement(conn, ajout_ar, temp_gdb, nom_table, table_part, nom_table_c):
    """
    Effectue un auto-recouvrement sur une couche SIG et enregistre les correspondances dans une base PostgreSQL.

    Étapes du traitement :
    1. Union de la couche avec elle-même
    2. Ajout d'un champ identifiant géométrique temporaire
    3. Dissolution selon la géométrie (pour regrouper les entités identiques)
    4. Création d'identifiants uniques
    5. Insertion des correspondances anciennes/nouvelles dans la table de correspondance

    Paramètres
    ----------
    conn : SQLAlchemy.Connection
        Connexion active à PostgreSQL via SQLAlchemy.
    ajout_ar : str
        Chemin de la classe d'entités à traiter (Feature Class).
    temp_gdb : str
        Chemin vers la géodatabase temporaire (où seront stockés les fichiers intermédiaires).
    nom_table : str
        Nom de base utilisé pour générer les fichiers temporaires.
    table_part : str
        Suffixe utilisé pour nommer les champs spécifiques à la table.
    nom_table_c : str
        Nom de la table de correspondance dans la base PostgreSQL.

    Retourne
    -------
    str
        Chemin de la couche finale après traitement.
    """

    fichier_union = os.path.join(temp_gdb, f"{nom_table}_union_ar")
    fichier_ar = os.path.join(temp_gdb, f"{nom_table}_sortie_ar")

    # Étape 1 : Union avec elle-même
    arcpy.analysis.Union([ajout_ar], fichier_union)

    # Nettoyage éventuel et ajout du champ temporaire
    if "Geom_Copy" in [field.name for field in arcpy.ListFields(fichier_union)]:
        arcpy.management.DeleteField(fichier_union, "Geom_Copy")
    arcpy.management.AddField(fichier_union, "Geom_Copy", "TEXT")

    with arcpy.da.UpdateCursor(fichier_union, ["SHAPE@WKT", "Geom_Copy"]) as cursor:
        for ligne in cursor:
            ligne[1] = ligne[0]
            cursor.updateRow(ligne)

    # Étape 2 : Dissolution pairwise sur la géométrie
    arcpy.analysis.PairwiseDissolve(
        in_features=fichier_union,
        out_feature_class=fichier_ar,
        dissolve_field="Geom_Copy",
        statistics_fields=f"cd_sig_{table_part} CONCATENATE",
        concatenation_separator=" ; "
    )

    # Étape 3 : Ajout champ identifiant final
    champ_cd_sig = f"cd_sig_{table_part}"
    if champ_cd_sig in [field.name for field in arcpy.ListFields(fichier_ar)]:
        arcpy.management.DeleteField(fichier_ar, champ_cd_sig)

    arcpy.management.AddField(fichier_ar, champ_cd_sig, "TEXT")

    with arcpy.da.UpdateCursor(fichier_ar, ["SHAPE@WKT", "Geom_Copy", champ_cd_sig]) as cursor:
        unique_id = 1
        for ligne in cursor:
            ligne[1] = ligne[0]  # Mise à jour Geom_Copy
            ligne[2] = f"{nom_table}_{unique_id}"  # Création identifiant unique
            cursor.updateRow(ligne)
            unique_id += 1

    # Étape 4 : Création des correspondances
    correspondance_data = []
    with arcpy.da.SearchCursor(fichier_ar, [champ_cd_sig, f"CONCATENATE_cd_sig_{table_part}"]) as cursor:
        for ligne in cursor:
            valeurs_concat = ligne[1].split(" ; ")
            for val in valeurs_concat:
                correspondance_data.append([val, ligne[0]])

    # Étape 5 : Insertion dans la table de correspondance (PostgreSQL)
    requete_insertion = text(
        f"""
        INSERT INTO sig_union.{nom_table_c} (cd_sig, cd_sig_equiv)
        VALUES (:cd_sig, :cd_sig_equiv)
        """
    )
    for ligne in correspondance_data:
        conn.execute(requete_insertion, {"cd_sig": ligne[0], "cd_sig_equiv": ligne[1]})

    # Nettoyage final
    arcpy.management.DeleteField(fichier_ar, [f"CONCATENATE_cd_sig_{table_part}", "Geom_Copy"])

    return fichier_ar
