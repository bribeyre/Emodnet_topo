# **Script correction topographique Emodnet**

## **Description**
Ce script automatise une série de traitements spatiaux à l'aide d'ArcPy pour analyser, manipuler et fusionner des données géographiques. Le workflow inclut la création d'une boîte englobante, l'identification et la suppression de polygones spécifiques, la création de polygones de Thiessen, et une dissolution finale avec des statistiques.

---

## **Étapes principales**

### **1. Configuration initiale**
- **Géodatabase temporaire** : Une géodatabase temporaire (`temp_output.gdb`) est créée dans le dossier de sortie pour stocker les résultats intermédiaires.
- **Entrée** : Le script utilise un shapefile comme données d'entrée (`exemple.shp`).

---

### **2. Workflow des traitements**

1. **Génération de la boîte englobante** :
   - Crée un polygone rectangulaire minimal (type `ENVELOPE`) autour de l'ensemble des géométries d'entrée.

2. **Suppression des zones couvertes par les données d'entrée** :
   - Utilise l'outil `PairwiseErase` pour supprimer de la boîte englobante les zones déjà couvertes par les polygones d'entrée.

3. **Conversion en polygones à une seule partie** :
   - Divise les polygones multiparties résultants en polygones individuels.

4. **Calcul des superficies et suppression du polygone englobant** :
   - Ajoute un champ `Area` et calcule la superficie de chaque polygone.
   - Identifie et supprime le polygone avec la plus grande superficie.

5. **Extraction des sommets des polygones** :
   - Convertit les sommets des polygones en points.

6. **Création de polygones de Thiessen** :
   - Génère des polygones de Thiessen basés sur les points extraits.

7. **Découpe des polygones de Thiessen** :
   - Découpe les polygones de Thiessen en fonction des polygones restants (après suppression).

8. **Jointure spatiale** :
   - Associe des attributs des données d'entrée aux polygones découpés via une jointure spatiale (`SpatialJoin`).

9. **Combine les résultats** :
   - Combine les résultats de la jointure spatiale avec les données d'entrée initiales.

10. **Fusions des données** :
    - Effectue une fusion basée sur un champ clé (`id_geom`) et conserve sur les champs restants (par exemple, `FIRST` pour les valeurs principales). 
    - Puis, les champs sont renommés pour supprimer le préfixe `FIRST_` ajouté automatiquement lors de la fusion.

---

## **Structure des fichiers**

### **Entrée**
- `donnees_entree` : Chemin du shapefile d'entrée (`exemple.shp`).

### **Sorties intermédiaires**
Les résultats intermédiaires sont stockés dans une géodatabase temporaire (`temp_output.gdb`) et incluent :
- **`boite_englobante`** : Polygone rectangulaire minimal.
- **`boite_englobante_sans_donnees`** : Boîte englobante après suppression des zones couvertes.
- **`polygones_simple`** : Polygones à une seule partie.
- **`points_sommets`** : Sommets des polygones convertis en points.
- **`polygones_thiessen`** : Polygones de Thiessen.
- **`polygones_thiessen_decoupes`** : Polygones de Thiessen après découpe.
- **`jointure_spatiale`** : Résultat de la jointure spatiale.
- **`fusion_donnees`** : Données fusionnées avant la dissolution.

### **Sortie finale**
- **`resultat_final.shp`** : Résultat final après dissolution et renommage des champs.

---

## **Pré-requis**

1. **Logiciels nécessaires** :
   - ArcGIS Pro avec une licence autorisant l'utilisation d'ArcPy. Pour utiliser arcgis Pro comme librairie il faut suivre les instructions suivantes : 
   - #### **Étapes principales**
   
     - ##### **1. Ouvrir les paramètres de PyCharm**
       - Dans PyCharm, cliquez sur **Fichier > Paramètres** (ou **File > Settings** sous Windows).

     - ##### **2. Accéder à la section "Interpréteur Python"**
       - Dans la fenêtre **Paramètres**, développez le menu **Projects : <nom_du_projet>**.
       - Sélectionnez **Python Interpreter**.

     - ##### **3. Modifier ou ajouter un interpréteur**
       - Cliquez sur l'icône **⚙ (engrenage)** située à droite de la liste des interpréteurs.
       - Sélectionnez **Add Interpreter** dans le menu déroulant.

      - ##### **4. Ajouter un environnement Conda existant**
        1. Dans la fenêtre **Ajouter un interpréteur Python**, sélectionnez **Conda Environment**.
        2. Choisissez l'option **Existing environment** (environnement existant).
        3. Cliquez sur l'icône **...** pour parcourir votre système de fichiers.

     - ##### **5. Sélectionner le chemin de l'interpréteur Conda**
       - Naviguez vers le chemin suivant :
         - **`C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\conda.exe`** (pour l'environnement Python par défaut d'ArcGIS Pro).
         - Ou sélectionnez le chemin de votre **environnement cloné** si vous en avez configuré un.

     - ##### **6. Option facultative : rendre l'interpréteur global**
       - Si vous souhaitez utiliser cet interpréteur pour plusieurs projets, cochez la case **Make available to all projects**.

     - ##### **7. Valider la configuration**
       - Cliquez sur **OK** pour confirmer l'ajout de l'interpréteur.
       - Cliquez sur **OK** dans la fenêtre **Paramètres** pour appliquer les changements.


2. **Données d'entrée** :
   - Un shapefile contenant les erreur topologique à traiter. rentrer le nom de la couche au debut du script 
   - il faut aussi renseigner le fichier de sortie des couches
---

## **Utilisation**

1. **Configurer le script** :
   - Modifiez le chemin `donnees_entree` pour pointer vers votre shapefile d'entrée.

2. **Exécuter le script** :
   - Lancez le script dans un environnement Python compatible avec ArcPy.

3. **Vérifiez les résultats** :
   - Les résultats intermédiaires seront stockés dans `temp_output.gdb`.
   - Le résultat final est dans la dossier `output` crée au debut du script sous le nom `resultat_final.shp`
---