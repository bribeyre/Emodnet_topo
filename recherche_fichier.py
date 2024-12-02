import os

# Fonction pour rechercher un fichier sur tout l'ordinateur
def recherche_fichier(nom_fichier, repertoire_base="C:\\"):
    """
    Recherche récursive d'un fichier sur tout l'ordinateur (ou un répertoire de base donné).
    """
    print(f"Recherche du fichier '{nom_fichier}' dans {repertoire_base}...")
    for racine, dossiers, fichiers in os.walk(repertoire_base):
        if nom_fichier in fichiers:
            return os.path.join(racine, nom_fichier)
    return None