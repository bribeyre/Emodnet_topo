import os
import arcpy


def initialiser_env():
    """
    Initialise l'environnement ArcPy, crée les dossiers nécessaires et retourne leurs chemins.

    Retourne :
        tuple : Le chemin du dossier racine, du dossier de sortie et de la géodatabase temporaire.
    """
    arcpy.env.overwriteOutput = True
    dossier_racine = os.path.dirname(os.path.abspath(__file__))
    dossier_sortie = os.path.join(dossier_racine, "output")
    os.makedirs(dossier_sortie, exist_ok=True)

    geodatabase_temporaire = os.path.join(dossier_sortie, "temp_output.gdb")

    # Si la géodatabase existe, vider son contenu
    if arcpy.Exists(geodatabase_temporaire):
        print(f"Nettoyage de la géodatabase temporaire : {geodatabase_temporaire}")

        # Supprimer les datasets si existants
        datasets = arcpy.ListDatasets("*", "Feature")
        if datasets:
            for dataset in datasets:
                arcpy.management.Delete(dataset)

        # Supprimer les tables si existantes
        tables = arcpy.ListTables()
        if tables:
            for table in tables:
                arcpy.management.Delete(table)
    else:
        arcpy.management.CreateFileGDB(dossier_sortie, "temp_output.gdb")
        print(f"Géodatabase temporaire créée : {geodatabase_temporaire}")

    return dossier_racine, dossier_sortie, geodatabase_temporaire