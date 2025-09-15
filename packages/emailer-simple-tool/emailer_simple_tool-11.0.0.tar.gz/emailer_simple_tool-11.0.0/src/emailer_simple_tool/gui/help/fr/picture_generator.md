# 🖼️ Guide du Générateur d'Images

Guide complet pour créer des images personnalisées pour vos campagnes email.

## Qu'est-ce que le Générateur d'Images ?

Le Générateur d'Images crée des images personnalisées pour chaque destinataire de votre campagne. Vous pouvez ajouter des éléments de texte qui utilisent automatiquement les données de votre fichier CSV destinataires pour créer des images uniques pour chaque personne.

**Exemples :**
- Badges nominatifs avec le nom et l'entreprise de chaque personne
- Certificats avec les noms et détails des destinataires
- Invitations d'événements avec des informations personnalisées
- Matériel marketing avec du texte personnalisé par destinataire

## Commencer

### 1. Accéder au Générateur d'Images

1. Allez dans l'onglet **🖼️ Images** dans Emailer Simple Tool
2. Assurez-vous d'avoir d'abord chargé une campagne
3. Le Générateur d'Images sera disponible pour votre campagne

### 2. Comprendre les Projets

#### Qu'est-ce qu'un Projet d'Image ?
Un projet définit :
- **Taille du canevas** (dimensions de l'image)
- **Arrière-plan** (couleur ou image)
- **Éléments de texte** avec personnalisation
- **Style** (polices, couleurs, positionnement)

#### Structure du Projet
```
dossier-campagne/
└── picture-generator/
    └── nom-de-votre-projet/
        ├── project.json          # Paramètres du projet
        ├── background.png        # Image d'arrière-plan (optionnel)
        └── generated/           # Images de sortie (créées automatiquement)
```

## Créer Votre Premier Projet

### Étape 1 : Créer un Nouveau Projet

1. Cliquez sur le bouton **"Créer Nouveau Projet"**
2. Entrez un nom de projet descriptif (ex: "Badges Nominatifs", "Certificats")
3. Choisissez les dimensions du canevas :
   - **Petit** : 400x300 pixels (adapté aux emails)
   - **Moyen** : 800x600 pixels (standard)
   - **Grand** : 1200x900 pixels (haute qualité)
   - **Personnalisé** : Entrez vos propres dimensions

### Étape 2 : Définir l'Arrière-plan

#### Arrière-plan Couleur Unie
1. Choisissez **"Couleur Unie"**
2. Cliquez sur le sélecteur de couleur pour choisir la couleur d'arrière-plan
3. Choix populaires : Blanc (#FFFFFF), Bleu Clair (#E3F2FD), Gris Clair (#F5F5F5)

#### Arrière-plan Image
1. Choisissez **"Image d'Arrière-plan"**
2. Cliquez sur **"Parcourir"** pour sélectionner un fichier image
3. Formats supportés : PNG, JPG, GIF
4. L'image sera redimensionnée pour s'adapter au canevas

#### Conseils pour l'Arrière-plan
- **Gardez-le simple** - les arrière-plans chargés rendent le texte difficile à lire
- **Utilisez des couleurs claires** pour du texte sombre, des couleurs sombres pour du texte clair
- **Considérez l'affichage email** - certains clients email peuvent ne pas afficher les images
- **Testez différentes tailles** pour assurer la lisibilité

### Étape 3 : Ajouter des Éléments de Texte

#### Créer des Éléments de Texte
1. Cliquez sur le bouton **"Ajouter Élément de Texte"**
2. Configurez les propriétés du texte :
   - **Contenu du Texte** : Quoi afficher
   - **Source de Données** : Quelle colonne CSV utiliser
   - **Position** : Où sur l'image
   - **Style** : Police, taille, couleur, etc.

#### Options de Contenu de Texte

**Texte Statique**
- Texte fixe qui apparaît sur toutes les images
- Exemple : "Bienvenue à notre événement"
- Utilisez pour les titres, étiquettes, informations communes

**Texte Dynamique (Personnalisé)**
- Utilise les données de votre CSV destinataires
- Format : `{{nom_colonne}}`
- Exemple : `{{name}}`, `{{company}}`, `{{position}}`
- Chaque image obtient un contenu différent basé sur les données du destinataire

**Texte Mixte**
- Combine texte statique et dynamique
- Exemple : "Bonjour {{name}}, bienvenue à l'événement de {{company}} !"
- Très flexible pour les messages personnalisés

### Étape 4 : Positionner et Styliser le Texte

#### Positionnement
- **Position X** : Placement horizontal (0 = bord gauche)
- **Position Y** : Placement vertical (0 = bord supérieur)
- **Alignement** : Gauche, Centre, Droite
- **Rotation** : Angle en degrés (0-360)

#### Style de Police
- **Famille de Police** : Choisissez parmi les polices système disponibles
- **Taille de Police** : Taille en pixels (12-200 gamme typique)
- **Poids de Police** : Normal, Gras
- **Style de Police** : Normal, Italique
- **Couleur** : Couleur du texte (cliquez pour choisir)

#### Style Avancé
- **Contour** : Ajouter une bordure autour du texte
- **Ombre** : Ajouter un effet d'ombre portée
- **Transparence** : Rendre le texte semi-transparent

## Travailler avec les Données

### Intégration CSV

#### Données Disponibles
Le Générateur d'Images peut utiliser n'importe quelle colonne de votre fichier recipients.csv :
- `{{name}}` - Nom du destinataire
- `{{email}}` - Adresse email
- `{{company}}` - Nom de l'entreprise
- `{{position}}` - Titre du poste
- `{{champ_personnalise}}` - N'importe quelle colonne personnalisée que vous créez

#### Validation des Données
- **Données manquantes** - Affiche un texte de substitution si le champ CSV est vide
- **Texte long** - Gère automatiquement le texte qui pourrait être trop long
- **Caractères spéciaux** - Gère correctement les accents, symboles, etc.

### Conseils de Formatage de Texte

#### Texte Lisible
- **Taille de police** : Minimum 16px pour la lisibilité email
- **Contraste** : Texte sombre sur arrière-plan clair (ou vice versa)
- **Choix de police** : Utilisez des polices claires et lisibles (Arial, Helvetica, etc.)
- **Espacement** : Laissez assez d'espace autour des éléments de texte

#### Apparence Professionnelle
- **Alignement cohérent** - Alignez les éléments liés
- **Dimensionnement approprié** - Texte important plus grand, détails plus petits
- **Schéma de couleurs** - Utilisez 2-3 couleurs maximum
- **Espace blanc** - Ne surchargez pas l'image

## Fonctionnalités Avancées

### Éléments de Texte Multiples

#### Superposition
- Ajoutez plusieurs éléments de texte à une image
- Les éléments sont superposés dans l'ordre de création
- Les éléments ultérieurs apparaissent au-dessus des précédents

#### Exemple de Mise en Page
```
┌─────────────────────────────┐
│        NOM ÉVÉNEMENT        │  ← Texte statique, grande police
│                             │
│    Bonjour {{name}} !       │  ← Salutation personnalisée
│                             │
│   Entreprise : {{company}}  │  ← Info entreprise
│   Poste : {{position}}      │  ← Titre du poste
│                             │
│    15 décembre 2025         │  ← Info date statique
└─────────────────────────────┘
```

### Rotation de Texte

#### Quand Utiliser la Rotation
- **Éléments décoratifs** - Titres inclinés ou filigranes
- **Optimisation d'espace** - Adapter plus de texte dans des espaces restreints
- **Variété de design** - Créer des mises en page plus intéressantes

#### Conseils de Rotation
- **Petits angles** (5-15 degrés) semblent souvent plus naturels
- **Angles de 45 degrés** fonctionnent bien pour les éléments diagonaux
- **Rotation de 90 degrés** pour du texte vertical
- **Testez la lisibilité** - le texte pivoté peut être plus difficile à lire

### Couleur et Style

#### Schémas de Couleurs
- **Monochrome** : Différentes nuances d'une couleur
- **Complémentaire** : Couleurs opposées sur le cercle chromatique
- **Entreprise** : Utilisez les couleurs de marque de votre entreprise
- **Contraste élevé** : Assurez-vous que le texte est toujours lisible

#### Style Professionnel
- **Polices cohérentes** - Utilisez 1-2 familles de polices maximum
- **Hiérarchie** - Texte important plus grand/gras
- **Alignement** - Gardez les éléments visuellement organisés
- **Équilibre** - Distribuez les éléments uniformément

## Test et Aperçu

### Système d'Aperçu

#### Aperçu en Temps Réel
- Voyez les changements immédiatement pendant l'édition
- L'aperçu montre les données réelles des destinataires
- Basculez entre différents destinataires pour tester les variations

#### Contrôles d'Aperçu
- **Sélecteur de destinataire** - Choisissez quel destinataire prévisualiser
- **Contrôles de zoom** - Zoomez pour le travail de détail
- **Actualiser** - Mettez à jour l'aperçu après les changements

### Processus de Test

#### Avant la Génération
1. **Vérifiez que tous les éléments de texte** s'affichent correctement
2. **Testez avec différents destinataires** pour voir les variations de données
3. **Vérifiez le positionnement** et l'alignement
4. **Vérifiez la lisibilité** à la taille réelle
5. **Testez avec les noms les plus longs/courts** pour vérifier l'ajustement

#### Test de Génération
1. **Générez quelques images de test** d'abord
2. **Vérifiez la qualité de sortie** et les tailles de fichiers
3. **Vérifiez que tous les destinataires** obtiennent des images uniques
4. **Testez dans un client email** pour voir comment les images s'affichent

## Génération d'Images

### Processus de Génération

#### Comment Ça Fonctionne
1. **Charger les paramètres du projet** et les données des destinataires
2. **Créer l'image de base** avec l'arrière-plan
3. **Ajouter les éléments de texte** pour chaque destinataire
4. **Appliquer le style** et le positionnement
5. **Sauvegarder les images individuelles** pour chaque destinataire

#### Détails de Sortie
- **Format** : PNG (meilleure qualité pour le texte)
- **Nommage** : Utilise l'ID destinataire ou email pour des noms de fichiers uniques
- **Emplacement** : `campagne/picture-generator/nom-projet/generated/`
- **Pièce jointe automatique** : Les images se joignent automatiquement aux emails

### Options de Génération

#### Génération par Lots
- **Générer tout** - Créer des images pour tous les destinataires à la fois
- **Générer sélectionnés** - Créer des images pour des destinataires spécifiques
- **Régénérer** - Recréer les images après les changements

#### Paramètres de Qualité
- **Qualité standard** - Bon pour l'email, tailles de fichiers plus petites
- **Haute qualité** - Meilleur pour l'impression, tailles de fichiers plus grandes
- **DPI personnalisé** - Spécifier la résolution pour des besoins spéciaux

## Performance et Optimisation

### Conseils de Performance

#### Génération Rapide
- **Tailles de canevas plus petites** génèrent plus rapidement
- **Moins d'éléments de texte** se traitent plus rapidement
- **Arrière-plans simples** (couleurs unies) sont les plus rapides
- **Polices standard** se rendent plus rapidement que les polices personnalisées

#### Optimisation de Taille de Fichier
- **Dimensions appropriées** - Ne rendez pas les images plus grandes que nécessaire
- **Designs simples** créent des fichiers plus petits
- **Limitez les couleurs** - Moins de couleurs = fichiers PNG plus petits
- **Considérez JPEG** pour les arrière-plans photo (fichiers plus petits)

### Spécifications Recommandées

#### Images Adaptées aux Emails
- **Dimensions** : 400x300 à 800x600 pixels
- **Taille de fichier** : Sous 100KB par image
- **Format** : PNG pour le texte, JPEG pour les photos
- **Campagne totale** : Gardez sous 10MB de taille totale de pièces jointes

#### Images Qualité Impression
- **Dimensions** : 1200x900 pixels ou plus
- **Résolution** : 300 DPI pour l'impression
- **Format** : PNG pour la meilleure qualité
- **Taille de fichier** : Fichiers plus grands acceptables pour l'usage impression

## Dépannage

### Problèmes Courants

#### Le Texte N'Apparaît Pas
- **Vérifiez la source de données** - La colonne CSV existe-t-elle ?
- **Vérifiez l'orthographe** - Les noms de colonnes sont sensibles à la casse
- **Vérifiez le positionnement** - Le texte est-il en dehors de la zone du canevas ?
- **Problèmes de police** - La police sélectionnée est-elle disponible sur le système ?

#### Qualité d'Image Médiocre
- **Augmentez la taille du canevas** pour une meilleure résolution
- **Utilisez des polices appropriées** - Certaines polices se rendent mieux que d'autres
- **Vérifiez le contraste des couleurs** - Assurez-vous que le texte est visible contre l'arrière-plan
- **Évitez le texte très petit** - Minimum 12px pour la lisibilité

#### Erreurs de Génération
- **Vérifiez les données CSV** - Assurez-vous qu'il n'y a pas de données corrompues ou manquantes
- **Vérifiez les paramètres du projet** - Tous les champs requis configurés ?
- **Disponibilité des polices** - Les polices sélectionnées sont-elles installées ?
- **Espace disque** - Assez d'espace pour les images générées ?

#### Problèmes de Performance
- **Réduisez la taille du canevas** si la génération est lente
- **Simplifiez le design** - Moins d'éléments génèrent plus rapidement
- **Fermez d'autres applications** pour libérer de la mémoire
- **Générez en plus petits lots** pour de grandes listes de destinataires

### Messages d'Erreur

#### "Police non trouvée"
- **Solution** : Choisissez une police différente installée sur votre système
- **Polices courantes** : Arial, Helvetica, Times New Roman sont généralement disponibles

#### "Colonne CSV non trouvée"
- **Solution** : Vérifiez que `{{nom_colonne}}` correspond exactement à l'en-tête CSV
- **Sensible à la casse** : `{{Name}}` ≠ `{{name}}`

#### "Génération d'image échouée"
- **Solution** : Vérifiez les paramètres du projet, essayez un design plus simple d'abord
- **Vérifiez les journaux** : Regardez les détails d'erreur spécifiques dans les journaux d'application

## Meilleures Pratiques

### Directives de Design

#### Résultats Professionnels
- **Gardez-le simple** - Les designs propres et non encombrés fonctionnent le mieux
- **Marque cohérente** - Utilisez les couleurs et polices de votre organisation
- **Texte lisible** - Assurez-vous d'un bon contraste et d'un dimensionnement approprié
- **Testez minutieusement** - Prévisualisez avec diverses données de destinataires

#### Compatibilité Email
- **Tailles de fichiers raisonnables** - Gardez les images sous 100KB chacune
- **Dimensions standard** - Évitez les images extrêmement larges ou hautes
- **Considération du texte alternatif** - Les images peuvent ne pas s'afficher dans tous les clients email
- **Plan de secours** - Assurez-vous que le contenu email fonctionne sans images

### Efficacité du Flux de Travail

#### Organisation du Projet
- **Noms descriptifs** - Utilisez des noms de projets clairs
- **Projets modèles** - Sauvegardez les designs réussis comme modèles
- **Contrôle de version** - Gardez des sauvegardes des projets fonctionnels
- **Documentation** - Notez les décisions de design pour référence future

#### Traitement par Lots
- **Testez petit d'abord** - Générez 5-10 images pour tester avant le lot complet
- **Surveillez le progrès** - Surveillez les erreurs pendant la génération
- **Vérification qualité** - Examinez les sorties d'échantillon avant d'envoyer la campagne
- **Sauvegardez les originaux** - Gardez les fichiers de projet en sécurité pour usage futur

---

## Prochaines Étapes

Une fois vos images générées :

1. **🚀 Testez avec Test à Blanc** - Vérifiez que les images se joignent correctement aux emails
2. **📧 Envoyez la Campagne** - Les images se joindront automatiquement aux emails personnalisés
3. **📊 Surveillez les Résultats** - Vérifiez que les destinataires reçoivent les images correctement

**Rappelez-vous** : Testez toujours la génération d'images et la livraison d'emails avec un petit groupe avant d'envoyer à votre liste complète de destinataires !

---

*Besoin de plus d'aide ? Vérifiez la section FAQ ou recherchez des sujets spécifiques de génération d'images.*
