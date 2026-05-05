import arcpy
import os

def initialiser_env():
    """
    Initialise l'environnement ArcPy, crée les dossiers nécessaires et retourne leurs chemins.

    Retourne :
        tuple : Le chemin du dossier racine, du dossier de sortie et de la géodatabase temporaire.
    """
    arcpy.env.overwriteOutput = True

    # Dossier du script
    dossier_racine = os.path.dirname(os.path.abspath(__file__))

    # Dossier de sortie
    dossier_sortie = os.path.join(dossier_racine, "output")
    os.makedirs(dossier_sortie, exist_ok=True)

    # Chemin vers la GDB temporaire
    nom_gdb = "temp_output.gdb"
    geodatabase_temporaire = os.path.join(dossier_sortie, nom_gdb)

    # Si la GDB n'existe pas → la créer
    if not arcpy.Exists(geodatabase_temporaire):
        arcpy.management.CreateFileGDB(dossier_sortie, nom_gdb)
        print(f"✅ Géodatabase temporaire créée : {geodatabase_temporaire}")
    else:
        print(f"♻️ Nettoyage de la géodatabase temporaire : {geodatabase_temporaire}")
        # Supprimer tous les jeux de données
        arcpy.env.workspace = geodatabase_temporaire

        # Supprimer tous les feature classes
        for fc in arcpy.ListFeatureClasses():
            arcpy.management.Delete(fc)

        # Supprimer tous les datasets
        for ds in arcpy.ListDatasets("", "Feature"):
            arcpy.management.Delete(ds)

        # Supprimer toutes les tables
        for table in arcpy.ListTables():
            arcpy.management.Delete(table)

    return dossier_racine, dossier_sortie, geodatabase_temporaire
