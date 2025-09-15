# 📁 Guide de Configuration de Campagne

Guide complet pour créer et gérer des campagnes email avec Emailer Simple Tool.

## Qu'est-ce qu'une Campagne ?

Une campagne est un dossier contenant tous les fichiers nécessaires pour envoyer des emails personnalisés :
- **Liste de destinataires** (fichier CSV avec adresses email et données)
- **Objet d'email** (modèle avec personnalisation)
- **Message d'email** (texte brut ou document formaté)
- **Pièces jointes** (fichiers optionnels à inclure)
- **Images** (images personnalisées optionnelles)

## Structure du Dossier de Campagne

```
Ma Campagne/
├── recipients.csv          # Requis : Liste d'emails avec données
├── subject.txt            # Requis : Modèle d'objet d'email
├── msg.txt ou msg.docx    # Requis : Message d'email
├── attachments/           # Optionnel : Fichiers à joindre à tous les emails
├── picture-generator/     # Optionnel : Projets d'images personnalisées
├── dryrun/               # Créé : Sorties d'emails de test
├── logs/                 # Créé : Journaux d'application
└── .emailer-config.json  # Créé : Paramètres de campagne
```

## Étape 1 : Créer le Dossier de Campagne

### Utilisation de l'Interface Graphique
1. Allez dans l'onglet **📁 Campagne**
2. Cliquez sur le bouton **"Parcourir"**
3. Choisissez **"Créer Nouvelle Campagne"** ou sélectionnez un dossier existant
4. Suivez l'assistant de création de campagne

### Création Manuelle
1. Créez un nouveau dossier pour votre campagne
2. Donnez-lui un nom descriptif (ex: "Invitations Fête de Noël")
3. L'assistant aidera à créer les fichiers requis

## Étape 2 : Configurer la Liste de Destinataires

### Création de recipients.csv

Le fichier destinataires contient votre liste d'emails et les données de personnalisation.

#### Colonne Requise
- **email** - L'adresse email du destinataire (doit être le nom exact de colonne)

#### Colonnes Optionnelles
Ajoutez toutes les colonnes que vous voulez utiliser pour la personnalisation :
- **name** - Nom du destinataire
- **company** - Nom de l'entreprise
- **position** - Titre du poste
- **city** - Localisation
- **champ_personnalise** - Toute donnée personnalisée

#### Exemple recipients.csv
```csv
id,email,name,company,position,city
001,john.doe@example.com,John Doe,ACME Corporation,Manager,New York
002,jane.smith@company.com,Jane Smith,Tech Solutions,Directrice,San Francisco
003,bob.wilson@firm.com,Bob Wilson,Wilson & Associés,Partenaire,Chicago
```

### Conseils pour le Fichier CSV

#### Règles de Formatage
- **La première ligne doit être les en-têtes de colonnes**
- **Utilisez des virgules pour séparer les colonnes**
- **Pas de lignes vides au début**
- **Sauvegardez au format CSV** (pas Excel .xlsx)

#### Création dans Excel
1. Ouvrez Excel et créez votre tableau de données
2. Première ligne = en-têtes de colonnes (email, name, company, etc.)
3. Lignes suivantes = données des destinataires
4. **Fichier → Enregistrer sous → CSV (délimité par des virgules)**
5. Choisissez le dossier de campagne comme emplacement de sauvegarde
6. Nommez-le exactement : **recipients.csv**

#### Conseils de Qualité des Données
- **Vérifiez les adresses email** sont correctes
- **Supprimez les doublons** pour éviter d'envoyer deux fois
- **Vérifiez l'orthographe** dans les noms et entreprises
- **Utilisez un formatage cohérent** (ex: tous les noms en format "Prénom Nom")

## Étape 3 : Créer l'Objet d'Email

### Fichier subject.txt

Créez un fichier nommé **subject.txt** avec votre ligne d'objet d'email.

#### Exemples
```
Bienvenue à notre événement, {{name}} !
```

```
Votre invitation {{company}} est prête
```

```
{{name}}, ne manquez pas notre offre spéciale
```

#### Conseils pour la Ligne d'Objet
- **Gardez-la sous 50 caractères** pour un meilleur affichage dans les clients email
- **Évitez les mots spam** comme "GRATUIT", "URGENT", "CLIQUEZ MAINTENANT"
- **Personnalisez quand possible** en utilisant les données des destinataires
- **Soyez clair et spécifique** sur le contenu de l'email

## Étape 4 : Créer le Message d'Email

Vous pouvez créer soit un message texte brut soit un message formaté.

### Message Texte Brut (msg.txt)

Fichier texte simple avec votre contenu d'email.

#### Exemple msg.txt
```
Cher {{name}},

Nous sommes ravis de vous inviter, vous et {{company}}, à notre conférence annuelle.

Détails de l'Événement :
- Date : 15 décembre 2025
- Heure : 9h00 - 17h00
- Lieu : Centre de Congrès, {{city}}

Veuillez confirmer votre présence avant le 1er décembre.

Cordialement,
L'Équipe Événementielle
```

### Message Formaté (msg.docx)

Document texte enrichi avec polices, couleurs et formatage.

#### Création dans Microsoft Word
1. Ouvrez Microsoft Word
2. Créez votre contenu d'email avec formatage
3. Utilisez la syntaxe `{{variable}}` pour la personnalisation
4. **Fichier → Enregistrer sous → Document Word (.docx)**
5. Sauvegardez dans votre dossier de campagne comme **msg.docx**

#### Conseils de Formatage
- **Utilisez des polices lisibles** (Arial, Calibri, Times New Roman)
- **Gardez le formatage simple** pour une meilleure compatibilité email
- **Testez avec différents clients email** pour assurer la compatibilité
- **Évitez les mises en page complexes** qui pourraient se casser dans l'email

## Étape 5 : Variables de Personnalisation

### Syntaxe des Variables

Utilisez `{{nom_colonne}}` pour insérer des données de votre fichier CSV.

#### Exemples
- `{{name}}` - Insère la valeur de la colonne "name"
- `{{company}}` - Insère la valeur de la colonne "company"
- `{{email}}` - Insère l'adresse email du destinataire

### Règles des Variables

#### Sensible à la Casse
- `{{name}}` ≠ `{{Name}}` ≠ `{{NAME}}`
- Les noms de colonnes doivent correspondre exactement

#### Caractères Valides
- Lettres, chiffres, underscores : `{{prenom_nom}}`
- Pas d'espaces : `{{prenom nom}}` ❌ `{{prenom_nom}}` ✅
- Pas de caractères spéciaux : `{{nom!}}` ❌ `{{nom}}` ✅

#### Prévention d'Erreurs
- **Vérifiez l'orthographe** des noms de variables contre les colonnes CSV
- **Utilisez une nomenclature cohérente** (tout en minuscules recommandé)
- **Testez avec un test à blanc** pour vérifier que la personnalisation fonctionne

## Étape 6 : Ajouter des Pièces Jointes (Optionnel)

### Pièces Jointes Statiques

Fichiers qui seront joints à chaque email de la campagne.

#### Configuration des Pièces Jointes
1. Créez un dossier **attachments** dans votre répertoire de campagne
2. Copiez les fichiers que vous voulez joindre dans ce dossier
3. Tous les fichiers de ce dossier seront joints à chaque email

#### Types de Fichiers Supportés
- **Documents** : PDF, DOC, DOCX, TXT
- **Images** : JPG, PNG, GIF
- **Feuilles de calcul** : XLS, XLSX, CSV
- **Archives** : ZIP, RAR
- **La plupart des autres types de fichiers** sont supportés

#### Conseils pour les Pièces Jointes
- **Gardez la taille totale sous 10MB** par email pour une meilleure livraison
- **Utilisez des noms de fichiers descriptifs**
- **Compressez les gros fichiers** quand possible
- **Testez la livraison** avec des pièces jointes en utilisant un test à blanc

## Étape 7 : Validation de Campagne

### Validation Automatique

L'application vérifie automatiquement votre campagne pour les problèmes courants :

#### Validation des Fichiers
- ✅ Les fichiers requis existent (recipients.csv, subject.txt, fichier message)
- ✅ Le format du fichier CSV est valide
- ✅ Les adresses email sont correctement formatées
- ✅ Les variables dans les modèles correspondent aux colonnes CSV

#### Validation des Données
- ✅ Pas d'adresses email dupliquées
- ✅ Toutes les colonnes requises présentes
- ✅ Pas d'adresses email vides
- ✅ Nombre de destinataires raisonnable (sous 100 recommandé)

### Correction des Erreurs de Validation

#### Problèmes Courants et Solutions

**"Fichier requis manquant"**
- Assurez-vous que recipients.csv, subject.txt, et msg.txt/msg.docx existent
- Vérifiez que les noms de fichiers sont orthographiés exactement correctement
- Vérifiez que les fichiers sont dans le bon dossier de campagne

**"Format CSV invalide"**
- Ouvrez le CSV dans un éditeur de texte pour vérifier le formatage
- Assurez-vous que les virgules séparent les colonnes correctement
- Supprimez toute ligne vide au début
- Sauvegardez au format CSV, pas au format Excel

**"Variable non trouvée dans le CSV"**
- Vérifiez que les noms `{{variable}}` correspondent exactement aux en-têtes de colonnes CSV
- Vérifiez l'orthographe et la sensibilité à la casse
- Supprimez tout espace supplémentaire dans les noms de colonnes

**"Adresse email invalide"**
- Vérifiez les adresses email pour les fautes de frappe
- Assurez-vous du format correct : nom@domaine.com
- Supprimez tout espace ou caractère supplémentaire

## Étape 8 : Tester Votre Campagne

### Utilisez Toujours un Test à Blanc d'Abord

Avant d'envoyer de vrais emails, testez toujours avec un test à blanc :

1. Allez dans l'onglet **🚀 Envoi**
2. Cliquez sur le bouton **"Test à Blanc"**
3. Examinez les fichiers d'email générés
4. Vérifiez que la personnalisation a fonctionné correctement
5. Vérifiez que les pièces jointes sont incluses

### Ce que le Test à Blanc Vous Montre

- **Contenu d'email exact** pour chaque destinataire
- **Résultats de personnalisation** (variables remplacées par des données réelles)
- **Vérification d'inclusion des pièces jointes**
- **Aperçu du formatage d'email**
- **Problèmes potentiels** avant l'envoi réel

## Conseils de Gestion de Campagne

### Organisation
- **Utilisez des noms de dossiers descriptifs** pour les campagnes
- **Gardez les campagnes séparées** - un dossier par campagne
- **Archivez les anciennes campagnes** quand elles ne sont plus nécessaires
- **Sauvegardez les campagnes importantes** avant les changements majeurs

### Meilleures Pratiques
- **Commencez petit** - testez avec 5-10 destinataires d'abord
- **Vérifiez la qualité des données** avant de créer de grandes campagnes
- **Gardez les listes de destinataires à jour** et supprimez les emails qui rebondissent
- **Suivez les meilleures pratiques email** pour éviter les filtres spam

### Optimisation des Performances
- **Gardez les listes de destinataires sous 100** pour de meilleures performances
- **Utilisez des pièces jointes simples** (évitez les très gros fichiers)
- **Optimisez les images** dans les projets du générateur d'images
- **Testez sur différents appareils** et clients email

## Dépannage des Problèmes de Campagne

### La Campagne Ne Se Charge Pas
- Vérifiez les permissions du dossier (vous avez besoin d'accès lecture/écriture)
- Vérifiez que les fichiers requis existent et sont nommés correctement
- Essayez de créer une nouvelle campagne simple pour tester

### La Personnalisation Ne Fonctionne Pas
- Vérifiez que les noms de colonnes CSV correspondent exactement aux variables de modèle
- Vérifiez les espaces supplémentaires ou caractères spéciaux
- Testez avec une variable simple comme `{{name}}` d'abord

### Fichiers Non Trouvés
- Assurez-vous que tous les fichiers sont dans le bon dossier de campagne
- Vérifiez les extensions de fichiers (.csv, .txt, .docx)
- Vérifiez que les noms de fichiers n'ont pas d'espaces supplémentaires ou de caractères

---

## Prochaines Étapes

Une fois votre campagne configurée :

1. **📧 Configurer SMTP** - Paramétrer vos paramètres de serveur email
2. **🖼️ Ajouter des Images** (optionnel) - Créer des images personnalisées
3. **🚀 Tester et Envoyer** - Test à blanc, puis envoyer votre campagne

**Rappelez-vous** : Testez toujours avec un test à blanc avant d'envoyer de vrais emails !

---

*Besoin de plus d'aide ? Vérifiez les autres sections d'aide ou utilisez la fonction de recherche pour trouver des informations spécifiques.*
