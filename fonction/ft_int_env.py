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
    if not arcpy.Exists(geodatabase_temporaire):
        arcpy.management.CreateFileGDB(dossier_sortie, "temp_output.gdb")
    print(f"Géodatabase temporaire créée : {geodatabase_temporaire}")

    return dossier_racine, dossier_sortie, geodatabase_temporaire
