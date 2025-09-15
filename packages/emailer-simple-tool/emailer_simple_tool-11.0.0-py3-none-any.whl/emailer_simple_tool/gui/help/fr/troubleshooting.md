# 🔧 Guide de Dépannage

Guide de dépannage complet pour les problèmes courants et leurs solutions.

## Diagnostic Rapide

### L'Application Ne Démarre Pas

#### Symptômes
- L'application ne se lance pas quand on clique
- Messages d'erreur sur des modules manquants
- Erreurs "commande non trouvée"

#### Solutions

**Vérifiez l'Installation Python**
```bash
python3 --version
# Devrait afficher Python 3.8 ou supérieur
```

**Réinstallez Emailer Simple Tool**
```bash
pip uninstall emailer-simple-tool
pip install emailer-simple-tool[gui]
```

**Vérifiez l'Installation**
```bash
emailer-simple-tool --version
# Devrait afficher le numéro de version actuel
```

**Corrections Courantes**
- **Windows** : Assurez-vous que Python est dans PATH pendant l'installation
- **macOS** : Utilisez `python3` au lieu de `python`
- **Linux** : Installez `python3-pip` si manquant

### L'Interface Graphique Ne S'Ouvre Pas

#### Symptômes
- CLI fonctionne mais l'interface graphique ne se lance pas
- Erreur sur PySide6 ou Qt
- Erreurs liées à l'affichage

#### Solutions

**Installez les Dépendances GUI**
```bash
pip install emailer-simple-tool[gui]
```

**Vérifiez l'Affichage (Linux)**
```bash
echo $DISPLAY
# Devrait afficher quelque chose comme :0 ou :1
```

**Essayez un Lancement Alternatif**
```bash
python3 -m emailer_simple_tool.gui
```

**Problèmes Courants**
- **Package GUI manquant** : Installez avec l'option `[gui]`
- **Linux sans affichage** : Utilisez CLI à la place ou activez le transfert X11
- **Permissions macOS** : Autorisez l'application dans les préférences Sécurité

## Problèmes de Campagne

### La Campagne Ne Se Charge Pas

#### Symptômes
- Erreurs "Campagne non trouvée"
- Les fichiers semblent exister mais ne sont pas reconnus
- La validation affiche toujours un statut rouge

#### Étapes de Diagnostic

**Vérifiez les Noms de Fichiers**
Les fichiers requis doivent être nommés exactement :
- `recipients.csv` (pas Recipients.csv ou recipients.CSV)
- `subject.txt` (pas subject.TXT)
- `msg.txt` ou `msg.docx` (pas message.txt)

**Vérifiez les Permissions de Fichiers**
```bash
ls -la dossier-campagne/
# Tous les fichiers devraient être lisibles (r-- dans les permissions)
```

**Vérifiez le Contenu des Fichiers**
- **recipients.csv** : Ouvrez dans un éditeur de texte, vérifiez le format CSV correct
- **subject.txt** : Devrait contenir le texte de la ligne d'objet
- **msg.txt** : Devrait contenir le message email

#### Solutions Courantes

**Problèmes de Nommage de Fichiers**
1. Renommez les fichiers aux noms exacts requis
2. Vérifiez les extensions de fichiers cachées (Windows)
3. Assurez-vous qu'il n'y a pas d'espaces supplémentaires dans les noms de fichiers

**Problèmes de Permissions**
1. **Windows** : Clic droit → Propriétés → Sécurité → Contrôle total
2. **macOS/Linux** : `chmod 644 dossier-campagne/*`
3. Déplacez la campagne vers le répertoire home de l'utilisateur

**Problèmes de Format de Fichier**
1. **CSV sauvegardé comme Excel** : Re-sauvegardez au format CSV
2. **Encodage de texte** : Sauvegardez les fichiers en encodage UTF-8
3. **Fins de ligne** : Utilisez les fins de ligne appropriées pour votre OS

### Problèmes de Fichier CSV

#### Format CSV Invalide

**Symptômes**
- Erreur "Format CSV invalide"
- La personnalisation ne fonctionne pas
- Données de destinataires manquantes

**Problèmes CSV Courants**

**En-têtes Manquants**
```csv
# Incorrect - pas de ligne d'en-tête
john@example.com,John Doe,ACME Corp

# Correct - ligne d'en-tête présente
email,name,company
john@example.com,John Doe,ACME Corp
```

**Séparateurs Incorrects**
```csv
# Incorrect - séparé par point-virgule
email;name;company
john@example.com;John Doe;ACME Corp

# Correct - séparé par virgule
email,name,company
john@example.com,John Doe,ACME Corp
```

**Guillemets ou Virgules Supplémentaires**
```csv
# Incorrect - guillemets supplémentaires
"email","name","company"
"john@example.com","John Doe","ACME Corp"

# Correct - pas de guillemets supplémentaires nécessaires
email,name,company
john@example.com,John Doe,ACME Corp
```

**Lignes Vides**
```csv
# Incorrect - lignes vides

email,name,company
john@example.com,John Doe,ACME Corp

# Correct - pas de lignes vides
email,name,company
john@example.com,John Doe,ACME Corp
```

#### Corriger les Problèmes CSV

**Utilisez un Éditeur de Texte**
1. Ouvrez le CSV dans un éditeur de texte brut (Bloc-notes, TextEdit)
2. Vérifiez le format visuellement
3. Corrigez tout problème évident
4. Sauvegardez comme texte brut

**Recréez depuis Excel**
1. Ouvrez les données dans Excel
2. Fichier → Enregistrer sous → CSV (délimité par des virgules)
3. Choisissez l'encodage UTF-8 si disponible
4. N'utilisez pas le format Excel (.xlsx)

**Validez le CSV en Ligne**
- Utilisez des validateurs CSV en ligne pour vérifier le format
- Copiez/collez de petits échantillons pour tester
- Corrigez les problèmes avant d'utiliser dans la campagne

### La Personnalisation Ne Fonctionne Pas

#### Symptômes
- Les variables comme `{{name}}` apparaissent littéralement dans les emails
- Certains destinataires obtiennent des champs vides
- Résultats de personnalisation incohérents

#### Diagnostic

**Vérifiez les Noms de Variables**
```
Modèle : Bonjour {{name}}, bienvenue chez {{company}} !
En-têtes CSV : email,name,company
Résultat : ✅ Les variables correspondent aux en-têtes

Modèle : Bonjour {{Name}}, bienvenue chez {{Company}} !
En-têtes CSV : email,name,company  
Résultat : ❌ Différence de casse (Name vs name)
```

**Vérifiez les Données CSV**
```csv
email,name,company
john@example.com,John Doe,ACME Corp     ✅ Données complètes
jane@example.com,,Tech Solutions        ❌ Nom manquant
bob@example.com,Bob Wilson,             ❌ Entreprise manquante
```

#### Solutions

**Corrigez la Casse des Variables**
- Faites correspondre exactement les variables de modèle aux en-têtes CSV
- Utilisez des minuscules dans les deux : `{{name}}` et en-tête CSV `name`
- Vérifiez les fautes de frappe dans les noms de variables

**Nettoyez les Données CSV**
- Remplissez les données manquantes où possible
- Utilisez du texte de substitution pour les champs manquants
- Supprimez les destinataires avec des données critiques manquantes

**Testez avec un Exemple Simple**
1. Créez un CSV minimal avec juste email et name
2. Utilisez un modèle simple : `Bonjour {{name}}`
3. Testez un test à blanc pour vérifier que la personnalisation fonctionne
4. Ajoutez graduellement de la complexité

## Problèmes SMTP et Email

### Problèmes de Connexion

#### Erreurs "Connexion Échouée"

**Vérifiez les Paramètres de Base**
- **Serveur** : Adresse correcte du serveur SMTP
- **Port** : Généralement 587 (TLS) ou 465 (SSL)
- **Sécurité** : TLS pour le port 587, SSL pour le port 465

**Testez la Connexion Réseau**
```bash
# Testez si le serveur est accessible
ping smtp.gmail.com

# Testez si le port est ouvert (Linux/macOS)
telnet smtp.gmail.com 587
```

**Paramètres de Serveur Courants**
```
Gmail :
- Serveur : smtp.gmail.com
- Port : 587
- Sécurité : TLS

Outlook :
- Serveur : smtp-mail.outlook.com  
- Port : 587
- Sécurité : TLS

Yahoo :
- Serveur : smtp.mail.yahoo.com
- Port : 587 ou 465
- Sécurité : TLS ou SSL
```

#### Authentification Échouée

**Problèmes Gmail**
- **Utilisez un Mot de Passe d'Application** : Pas votre mot de passe Gmail habituel
- **Activez 2FA** : Requis avant de créer un Mot de Passe d'Application
- **Générez Nouveau** : Créez un Mot de Passe d'Application frais si l'ancien échoue

**Problèmes de Mot de Passe**
- **Copier/Coller** : Évitez de taper les mots de passe manuellement
- **Pas d'Espaces** : Supprimez tout espace supplémentaire avant/après le mot de passe
- **Caractères Spéciaux** : Certains mots de passe peuvent nécessiter un échappement

**Problèmes de Nom d'Utilisateur**
- **Email Complet** : Utilisez l'adresse email complète comme nom d'utilisateur
- **Sensibilité à la Casse** : Certains serveurs sont sensibles à la casse
- **Domaine** : Incluez le domaine complet (utilisateur@domaine.com)

### Problèmes de Livraison d'Email

#### Les Emails N'Arrivent Pas

**Vérifiez les Dossiers Spam**
- Les destinataires devraient vérifier les dossiers spam/indésirable
- Marquez comme "Pas Spam" pour améliorer la livraison future
- Ajoutez l'expéditeur au carnet d'adresses du destinataire

**Vérifiez les Adresses Email**
- Vérifiez les fautes de frappe dans les adresses destinataires
- Supprimez les adresses évidemment invalides
- Testez avec des adresses connues bonnes d'abord

**Vérifiez les Rapports d'Envoi**
- Examinez le rapport d'envoi pour les échecs de livraison
- Cherchez les messages de rebond ou codes d'erreur
- Supprimez les adresses qui échouent constamment

#### Les Emails Vont dans les Spams

**Améliorez la Réputation de l'Expéditeur**
- Utilisez une adresse email d'entreprise établie
- Évitez les services email gratuits pour l'envoi d'affaires
- Envoyez depuis une adresse d'expéditeur cohérente

**Améliorations du Contenu**
- Évitez les mots déclencheurs de spam (GRATUIT, URGENT, CLIQUEZ MAINTENANT)
- Incluez un lien de désabonnement pour les emails marketing
- Utilisez du contenu professionnel et pertinent
- Évitez les majuscules excessives ou points d'exclamation

**Améliorations Techniques**
- Utilisez un fournisseur SMTP réputé
- Authentifiez-vous correctement avec les bons identifiants
- Gardez les listes de destinataires propres et engagées
- Surveillez les taux de rebond et supprimez les mauvaises adresses

## Problèmes du Générateur d'Images

### Les Images Ne Se Génèrent Pas

#### Causes Courantes

**Problèmes de Police**
- Police sélectionnée non disponible sur le système
- Nom de police mal orthographié
- Problèmes de cache de polices système

**Problèmes de Données**
- Colonne CSV référencée dans l'image n'existe pas
- Champs de données vides causant des erreurs de génération
- Caractères spéciaux dans les données causant des problèmes

**Configuration du Projet**
- Dimensions de canevas invalides
- Texte positionné en dehors de la zone du canevas
- Paramètres de projet corrompus

#### Solutions

**Corrigez les Problèmes de Police**
1. Utilisez des polices système courantes (Arial, Helvetica, Times New Roman)
2. Vérifiez les polices disponibles dans le système
3. Évitez les polices personnalisées ou décoratives
4. Testez avec une police simple d'abord

**Vérifiez les Données**
1. Vérifiez que le CSV a toutes les colonnes référencées dans l'image
2. Remplissez les données manquantes ou utilisez des substituts
3. Supprimez les caractères spéciaux qui pourraient causer des problèmes
4. Testez avec des données simples d'abord

**Réinitialisez le Projet**
1. Créez un nouveau projet simple pour tester
2. Utilisez des paramètres de base (arrière-plan uni, texte simple)
3. Ajoutez graduellement de la complexité
4. Sauvegardez les configurations fonctionnelles comme modèles

### Qualité d'Image Médiocre

#### Images Floues ou Pixelisées

**Augmentez la Résolution**
- Utilisez des dimensions de canevas plus grandes
- Minimum 400x300 pour usage email
- 800x600 ou plus pour une meilleure qualité
- Considérez le cas d'usage final (email vs impression)

**Problèmes de Taille de Police**
- Utilisez des tailles de police plus grandes (minimum 16px)
- Évitez le texte très petit qui devient illisible
- Testez à la taille d'affichage réelle
- Considérez la distance de visualisation

**Problèmes d'Arrière-plan**
- Utilisez des images d'arrière-plan haute résolution
- Évitez d'étirer de petites images
- Considérez les couleurs unies pour du texte net
- Testez le contraste arrière-plan/texte

#### Problèmes de Positionnement de Texte

**Texte Coupé**
- Vérifiez que la position du texte est dans les limites du canevas
- Tenez compte de la hauteur et largeur du texte
- Laissez des marges autour des éléments de texte
- Testez avec le texte le plus long attendu

**Éléments qui Se Chevauchent**
- Planifiez la mise en page du texte avant de créer
- Utilisez un espacement cohérent entre les éléments
- Considérez les variations de longueur de texte
- Testez avec différentes données de destinataires

**Problèmes de Rotation**
- Les petits angles de rotation (5-15°) fonctionnent souvent mieux
- Tenez compte que le texte pivoté prend plus d'espace
- Testez la lisibilité du texte pivoté
- Considérez si la rotation est nécessaire

## Problèmes de Performance

### Fonctionnement Lent

#### Application Fonctionne Lentement

**Ressources Système**
- Fermez d'autres applications pour libérer la mémoire
- Vérifiez l'espace disque disponible
- Surveillez l'usage CPU pendant les opérations
- Redémarrez l'application si l'usage mémoire est élevé

**Grandes Campagnes**
- Divisez les grandes listes de destinataires en lots plus petits
- Traitez moins de 100 destinataires à la fois
- Utilisez des modèles email plus simples pour les gros envois
- Générez les images en lots plus petits

**Problèmes Réseau**
- Vérifiez la vitesse de connexion internet
- Utilisez une connexion filaire au lieu du WiFi si possible
- Évitez les heures de pointe d'usage pour l'envoi d'emails
- Considérez les limites de débit du fournisseur email

#### Envoi d'Email Lent

**Limites du Fournisseur SMTP**
- Gmail : ~100 emails/jour pour les comptes gratuits
- Outlook : ~300 emails/jour pour les comptes gratuits
- Vérifiez les limites spécifiques de votre fournisseur
- Considérez passer à un compte d'entreprise pour des limites plus élevées

**Taille des Pièces Jointes**
- Réduisez la taille totale des pièces jointes par email
- Compressez les gros fichiers avant de les joindre
- Utilisez des dimensions d'image plus petites
- Supprimez les pièces jointes inutiles

**Optimisation Réseau**
- Utilisez une connexion internet stable
- Évitez d'envoyer pendant les heures de pointe
- Considérez l'envoi par lots sur plusieurs sessions
- Surveillez les interruptions de connexion

### Problèmes de Mémoire

#### Erreurs de Mémoire Insuffisante

**Réduisez l'Usage Mémoire**
- Traitez des lots plus petits de destinataires
- Fermez d'autres applications
- Utilisez des dimensions d'image plus petites
- Redémarrez l'application entre les grandes opérations

**Configuration Système Requise**
- Assurez-vous d'avoir minimum 512MB RAM disponible
- Vérifiez l'usage mémoire système
- Considérez augmenter la mémoire système
- Utilisez Python 64-bit si disponible

## Messages d'Erreur

### Messages d'Erreur Courants et Solutions

#### "Fichier non trouvé"
- **Cause** : Fichiers de campagne requis manquants
- **Solution** : Assurez-vous que recipients.csv, subject.txt, et msg.txt existent
- **Vérifiez** : Noms de fichiers orthographiés exactement correctement

#### "Permission refusée"
- **Cause** : Pas d'accès pour lire/écrire les fichiers de campagne
- **Solution** : Vérifiez les permissions de fichiers, déplacez vers un emplacement accessible
- **Windows** : Exécutez comme administrateur si nécessaire

#### "Adresse email invalide"
- **Cause** : Adresses email mal formées dans le CSV
- **Solution** : Vérifiez le format email, corrigez les fautes de frappe, supprimez les entrées invalides
- **Format** : Doit être nom@domaine.com

#### "Authentification SMTP échouée"
- **Cause** : Identifiants email incorrects
- **Solution** : Vérifiez nom d'utilisateur/mot de passe, utilisez Mot de Passe d'Application pour Gmail
- **Vérifiez** : Les paramètres serveur correspondent aux exigences du fournisseur

#### "Délai de connexion dépassé"
- **Cause** : Problèmes réseau ou serveur
- **Solution** : Vérifiez la connexion internet, essayez un serveur SMTP différent
- **Attendez** : Le serveur peut être temporairement indisponible

#### "Message trop grand"
- **Cause** : Email dépasse les limites de taille
- **Solution** : Réduisez les tailles de pièces jointes, utilisez des images plus petites
- **Limite** : La plupart des fournisseurs limitent à 25MB par email

### Obtenir des Informations d'Erreur Détaillées

#### Journaux d'Application
- **Emplacement** : `dossier-campagne/logs/`
- **Format** : Fichiers texte avec horodatage
- **Contenu** : Messages d'erreur détaillés et traces de pile

#### Rapports d'Envoi
- **Emplacement** : `dossier-campagne/sentreport/`
- **Contenu** : Détails succès/échec pour chaque destinataire
- **Usage** : Identifier les modèles dans les échecs

#### Rapports de Test à Blanc
- **Emplacement** : `dossier-campagne/dryrun/`
- **Contenu** : Détails succès/échec de génération
- **Usage** : Déboguer les problèmes avant l'envoi

## Obtenir de l'Aide

### Ressources d'Auto-Assistance

#### Aide Intégrée
- **📚 Système d'Aide** : Recherchez dans ce système d'aide pour des solutions
- **❓ FAQ** : Vérifiez les questions fréquemment posées
- **🚀 Démarrage Rapide** : Examinez les bases de configuration
- **📁 Configuration de Campagne** : Guide détaillé de création de campagne

#### Approche de Test
1. **Commencez Simple** : Créez une campagne de test minimale
2. **Ajoutez la Complexité Graduellement** : Ajoutez les fonctionnalités une à la fois
3. **Testez Chaque Étape** : Vérifiez que chaque composant fonctionne avant de continuer
4. **Documentez les Solutions** : Notez ce qui fonctionne pour référence future

### Signaler des Problèmes

#### Informations à Inclure
Lors de la recherche d'aide, fournissez :
- **Messages d'Erreur** : Texte exact de tout message d'erreur
- **Informations Système** : Système d'exploitation, version Python
- **Détails de Campagne** : Nombre de destinataires, tailles de fichiers
- **Étapes pour Reproduire** : Ce que vous avez fait avant l'erreur
- **Fichiers de Journal** : Contenu des fichiers de journal pertinents

#### Commandes de Diagnostic
```bash
# Informations système
python3 --version
emailer-simple-tool --version

# Vérifiez l'installation
pip show emailer-simple-tool

# Testez la fonctionnalité de base
emailer-simple-tool --help
```

---

## Conseils de Prévention

### Éviter les Problèmes Courants

#### Configuration de Campagne
- **Utilisez des modèles** : Commencez avec des exemples fonctionnels
- **Testez petit** : Testez toujours avec 2-3 destinataires d'abord
- **Validez tôt** : Vérifiez les fichiers avant de créer de grandes campagnes
- **Sauvegardez les configurations fonctionnelles** : Sauvegardez les configurations réussies

#### Envoi d'Email
- **Toujours test à blanc** : N'envoyez jamais sans tester d'abord
- **Vérifiez SMTP régulièrement** : Testez la connexion avant chaque campagne
- **Surveillez la livraison** : Surveillez les modèles de rebond
- **Gardez les listes propres** : Supprimez rapidement les adresses invalides

#### Maintenance Système
- **Gardez le logiciel à jour** : Mettez à jour Emailer Simple Tool régulièrement
- **Surveillez l'espace disque** : Assurez-vous d'un espace adéquat pour les opérations
- **Redémarrages réguliers** : Redémarrez l'application pour les grandes opérations
- **Nettoyez les anciens fichiers** : Supprimez périodiquement les anciens tests à blanc et rapports

---

**Rappelez-vous** : La plupart des problèmes peuvent être résolus en commençant par un cas de test simple et en ajoutant graduellement de la complexité. En cas de doute, testez avec une campagne minimale d'abord !

*Avez-vous encore des problèmes ? Utilisez la fonction de recherche pour trouver des messages d'erreur spécifiques ou vérifiez d'autres sections d'aide pour des conseils détaillés.*
