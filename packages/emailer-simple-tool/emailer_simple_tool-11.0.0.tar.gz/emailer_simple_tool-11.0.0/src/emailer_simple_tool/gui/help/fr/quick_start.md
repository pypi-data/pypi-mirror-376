# 🚀 Guide de Démarrage Rapide (5 minutes)

Commencez avec Emailer Simple Tool en seulement 5 minutes !

## Étape 1 : Choisissez Votre Interface

Emailer Simple Tool offre deux interfaces :
- **🎨 Interface Graphique (GUI)** - Parfaite pour les débutants, pointer-cliquer
- **⌨️ Interface en Ligne de Commande (CLI)** - Pour les utilisateurs avancés et l'automatisation

Puisque vous lisez ceci, vous utilisez déjà l'interface graphique !

## Étape 2 : Créez Votre Première Campagne

### Ce Dont Vous Avez Besoin
- **Liste d'emails** - Un fichier CSV avec les informations des destinataires
- **Message email** - Ce que vous voulez envoyer
- **Paramètres SMTP** - Configuration de votre serveur email

### Structure du Dossier de Campagne
```
Ma Campagne/
├── recipients.csv          # Requis : Votre liste d'emails
├── subject.txt            # Requis : Objet de l'email
├── msg.txt ou msg.docx    # Requis : Message email
├── attachments/           # Optionnel : Fichiers à joindre
└── picture-generator/     # Optionnel : Images personnalisées
```

## Étape 3 : Configurez Votre Campagne

### 📁 Onglet Campagne
1. Cliquez sur **"Parcourir"** pour sélectionner ou créer un dossier de campagne
2. L'assistant vous guidera pour créer les fichiers requis
3. Modifiez votre liste de destinataires, objet et message

### Exemple de Fichier Destinataires (recipients.csv)
```csv
id,email,name,company
001,john@example.com,John Doe,ACME Corp
002,jane@example.com,Jane Smith,Tech Solutions
```

### Exemple de Message (msg.txt)
```
Cher {{name}},

Bienvenue dans notre service ! Nous sommes ravis d'avoir {{company}} comme partenaire.

Cordialement,
L'Équipe
```

## Étape 4 : Configurez les Paramètres Email

### 📧 Onglet SMTP
1. Entrez les paramètres de votre serveur email
2. **Pour les utilisateurs Gmail :**
   - Serveur : smtp.gmail.com
   - Port : 587
   - Utilisez un Mot de Passe d'Application (pas votre mot de passe habituel)
3. **Testez la Connexion** pour vérifier les paramètres

### Obtenir un Mot de Passe d'Application Gmail
1. Activez l'authentification à 2 facteurs
2. Allez dans Compte Google → Sécurité → Mots de passe d'application
3. Générez un mot de passe pour "Mail"
4. Utilisez ce mot de passe dans les paramètres SMTP

## Étape 5 : Testez Avant d'Envoyer

### 🚀 Onglet Envoi
1. Cliquez sur **"Test à Blanc"** pour tester votre campagne
2. Examinez les fichiers email générés
3. Vérifiez que la personnalisation fonctionne correctement
4. Vérifiez les pièces jointes et le formatage

**Testez toujours d'abord !** Les tests à blanc vous montrent exactement ce qui sera envoyé.

## Étape 6 : Envoyez Votre Campagne

### Envoi Final
1. Après un test à blanc réussi, cliquez sur **"Envoyer Campagne"**
2. Confirmez que vous voulez envoyer
3. Surveillez le progrès
4. Examinez le rapport d'envoi

## 🎨 Optionnel : Ajoutez des Images Personnalisées

### 🖼️ Onglet Images
1. Créez un projet d'image
2. Ajoutez des éléments de texte avec les données des destinataires
3. Générez des images personnalisées
4. Les images se joignent automatiquement aux emails

## 💡 Conseils de Pro

### Sécurité d'Abord
- **Toujours tester d'abord** - Voyez exactement ce qui sera envoyé
- **Commencez petit** - Testez avec quelques destinataires initialement
- **Vérifiez les dossiers spam** - Les destinataires doivent vérifier spam/indésirable

### Performance
- **Gardez les listes sous 100** destinataires pour de meilleures performances
- **Utilisez des images simples** pour une génération plus rapide
- **Testez les paramètres SMTP** avant les grandes campagnes

### Dépannage
- **Problèmes de connexion ?** Vérifiez les paramètres SMTP et le pare-feu
- **Personnalisation manquante ?** Vérifiez que les noms de colonnes CSV correspondent aux {{variables}}
- **Images ne fonctionnent pas ?** Vérifiez les paramètres du projet d'image

## 🆘 Besoin de Plus d'Aide ?

- **📁 Configuration de Campagne** - Guide détaillé de création de campagne
- **📧 Configuration Email** - Instructions complètes de configuration SMTP
- **🖼️ Générateur d'Images** - Personnalisation d'images avancée
- **❓ FAQ** - Questions courantes et solutions

## 🎉 Vous Êtes Prêt !

C'est tout ! Vous connaissez maintenant les bases de la création et de l'envoi de campagnes email personnalisées avec Emailer Simple Tool.

**Rappelez-vous :** Testez toujours avec des tests à blanc avant d'envoyer pour vous assurer que tout fonctionne parfaitement.

---

*Bon emailing ! 📧*
