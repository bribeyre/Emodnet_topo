import arcpy
import os

def gestion_moz(geodatabase_temporaire, donnees_entree, dossier_sortie):
    """
    Fonction pour gérer la mosaïque des données géographiques en réalisant une union,
    en identifiant les géométries identiques et en filtrant certaines entités.

    Étapes principales :
    1. Réalise une union de la couche d'entrée avec elle-même.
    2. Ajoute des champs nécessaires pour le traitement.
    3. Identifie les géométries identiques et leur attribue un numéro séquentiel.
    4. Supprime les entités avec certains numéros spécifiques.
    5. Exporte le fichier final dans le dossier de sortie.
    """
    arcpy.env.overwriteOutput = True
    print(f"Geodatabase_temporaire (non utilisée) : {geodatabase_temporaire}")
    print(f"Données d'entrée : {donnees_entree}")
    print(f"Dossier de sortie : {dossier_sortie}")

    # Création du dossier pour la GDB locale si besoin
    dossier_gdb = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(dossier_gdb):
        os.makedirs(dossier_gdb)
        print(f"📁 Dossier 'output' créé : {dossier_gdb}")

    # Nom de la GDB
    nom_gdb = "ma_geodatabase_temp.gdb"
    chemin_gdb = os.path.join(dossier_gdb, nom_gdb)

    # Création de la GDB si elle n’existe pas
    if not arcpy.Exists(chemin_gdb):
        arcpy.management.CreateFileGDB(dossier_gdb, nom_gdb)
        print(f"✅ GDB créée : {chemin_gdb}")
    else:
        print(f"✅ GDB existante utilisée : {chemin_gdb}")

    # Fichier intermédiaire pour l’union
    fichier_union = os.path.join(chemin_gdb, "PatriNat59_trous")

    # Vérifie que les données d'entrée sont bien une seule couche
    if isinstance(donnees_entree, list):
        if len(donnees_entree) == 1:
            couche_entree = donnees_entree[0]
        else:
            raise ValueError("Plusieurs couches fournies : la fonction attend une seule couche.")
    else:
        couche_entree = donnees_entree

    # Étape 1 : Union de la couche avec elle-même
    arcpy.analysis.Union([couche_entree, couche_entree], fichier_union)

    # Étape 2 : Ajout des champs nécessaires
    champ_sequence = "Num_Sequence"
    champ_comp = "COMP"

    if not arcpy.ListFields(fichier_union, champ_sequence):
        arcpy.AddField_management(fichier_union, champ_sequence, "LONG")

    if not arcpy.ListFields(fichier_union, champ_comp):
        arcpy.AddField_management(fichier_union, champ_comp, "TEXT")

    # Étape 3 : Numérotation des géométries identiques
    geom_dict = {}
    with arcpy.da.UpdateCursor(fichier_union, ["SHAPE@", champ_sequence, champ_comp]) as cursor:
        for row in cursor:
            geom = row[0].WKT
            if geom not in geom_dict:
                geom_dict[geom] = 1
                row[2] = None
            else:
                geom_dict[geom] += 1
                row[2] = "auto"
            row[1] = geom_dict[geom]
            cursor.updateRow(row)

    print("✅ Géométries numérotées et champ COMP mis à jour.")

    # Étape 4 : Suppression de certaines entités par numéro de séquence
    with arcpy.da.UpdateCursor(fichier_union, [champ_sequence]) as cursor:
        for row in cursor:
            if row[0] in [2, 4, 6, 8]:
                cursor.deleteRow()

    print("🗑️ Entités avec Num_Sequence = 2, 4, 6, 8 supprimées.")

    # Étape 5 : Export du résultat final
    fichier_sortie = os.path.join(dossier_sortie, "patrinat15_avec_mozaique.shp")
    arcpy.management.CopyFeatures(fichier_union, fichier_sortie)
    print(f"📦 Résultat exporté : {fichier_sortie}")