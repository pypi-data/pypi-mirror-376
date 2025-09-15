# ❓ Foire Aux Questions (FAQ)

## Questions Générales

### Q: Qu'est-ce qu'Emailer Simple Tool ?
**R:** C'est une application conviviale qui vous aide à envoyer des emails personnalisés à plusieurs personnes à la fois. Au lieu de taper manuellement le nom et les détails de chaque personne, le programme le fait automatiquement en utilisant les données d'un fichier CSV.

### Q: Dois-je être technique pour utiliser ceci ?
**R:** Non ! C'est conçu pour les utilisateurs d'ordinateur ordinaires. Si vous pouvez utiliser Excel et l'email, vous pouvez utiliser cet outil. L'interface graphique rend tout simple avec des clics.

### Q: Est-ce sûr à utiliser ?
**R:** Oui. Vos mots de passe email sont chiffrés et stockés uniquement sur votre ordinateur. Aucune information n'est envoyée vers des serveurs externes sauf pour envoyer vos emails via votre fournisseur d'email.

### Q: Combien d'emails puis-je envoyer ?
**R:** L'outil est conçu pour jusqu'à 100 destinataires par campagne pour des performances optimales. Pour des listes plus importantes, considérez les diviser en groupes plus petits.

## Questions de Configuration

### Q: Quels fournisseurs d'email fonctionnent avec ceci ?
**R:** La plupart des fournisseurs d'email fonctionnent, incluant :
- Gmail (le plus courant)
- Outlook/Hotmail
- Yahoo Mail
- Systèmes d'email d'entreprise
- La plupart des autres services email compatibles SMTP

### Q: Pourquoi ne puis-je pas utiliser mon mot de passe email habituel ?
**R:** Beaucoup de fournisseurs d'email (comme Gmail) exigent des "Mots de Passe d'Application" pour la sécurité. C'est un mot de passe spécial juste pour les applications comme celle-ci, séparé de votre mot de passe de connexion habituel.

### Q: Comment obtenir un Mot de Passe d'Application pour Gmail ?
**R:** 
1. Allez dans les paramètres de votre Compte Google
2. Activez d'abord l'authentification à 2 facteurs (requis)
3. Allez dans Sécurité → Mots de passe d'application
4. Générez un nouveau mot de passe d'application pour "Mail"
5. Utilisez ce mot de passe au lieu de votre mot de passe habituel

### Q: Et si je ne connais pas mes paramètres SMTP ?
**R:** Paramètres courants :
- **Gmail** : smtp.gmail.com, port 587
- **Outlook** : smtp-mail.outlook.com, port 587
- **Yahoo** : smtp.mail.yahoo.com, port 587
- Pour d'autres, recherchez en ligne "[votre fournisseur d'email] paramètres SMTP"

## Questions sur les Fichiers

### Q: Qu'est-ce qu'un fichier CSV ?
**R:** C'est un fichier texte simple qui stocke des données en colonnes, comme une feuille de calcul Excel basique. Vous pouvez le créer en sauvegardant un fichier Excel au format "CSV".

### Q: Puis-je utiliser Excel au lieu de CSV ?
**R:** Vous devez sauvegarder votre fichier Excel au format CSV. Les fichiers Excel (.xlsx) ne fonctionneront pas directement, mais la conversion est simple : Fichier → Enregistrer sous → format CSV.

### Q: Quelles colonnes dois-je avoir dans mon fichier CSV ?
**R:** Vous devez avoir une colonne "email". Les autres colonnes dépendent de votre modèle de message. Si votre message utilise `{{name}}`, vous avez besoin d'une colonne "name". S'il utilise `{{company}}`, vous avez besoin d'une colonne "company".

### Q: Puis-je utiliser du texte formaté dans mes emails ?
**R:** Oui ! Vous pouvez utiliser :
- **Texte brut** (fichiers .txt) pour des messages simples
- **Texte enrichi** (fichiers .docx) pour des messages formatés avec polices, couleurs et styles

## Questions d'Envoi

### Q: Qu'est-ce qu'un "test à blanc" ?
**R:** Un test à blanc crée des fichiers d'email d'exemple sans les envoyer réellement. Il vous permet de prévisualiser exactement ce qui sera envoyé à chaque destinataire avant de vous engager à envoyer de vrais emails.

### Q: Dois-je toujours faire un test à blanc d'abord ?
**R:** **Absolument !** Testez toujours avec un test à blanc pour vous assurer que :
- La personnalisation fonctionne correctement
- Les pièces jointes sont incluses
- Le formatage semble correct
- Il n'y a pas d'erreurs dans vos données

### Q: Et si mes emails vont dans les spams ?
**R:** Cela peut arriver avec tout email en masse. Conseils pour éviter les spams :
- Utilisez un fournisseur d'email réputé
- N'utilisez pas de mots déclencheurs de spam dans les lignes d'objet
- Gardez votre liste de destinataires propre et pertinente
- Demandez aux destinataires de vérifier leurs dossiers spam initialement

### Q: Puis-je envoyer des emails avec des pièces jointes ?
**R:** Oui ! Mettez les fichiers dans le dossier "attachments" de votre campagne, et ils seront joints automatiquement à tous les emails.

## Questions sur le Générateur d'Images

### Q: Qu'est-ce que le Générateur d'Images ?
**R:** Il crée des images personnalisées pour chaque destinataire en utilisant leurs données. Par exemple, vous pourriez créer des badges nominatifs, des certificats, ou des invitations avec le nom et les détails de chaque personne.

### Q: Dois-je utiliser des images ?
**R:** Non, les images sont complètement optionnelles. Vous pouvez envoyer des emails texte uniquement sans aucune image.

### Q: Quels formats d'image sont supportés ?
**R:** L'outil génère des images PNG, qui fonctionnent bien pour les pièces jointes d'email et s'affichent correctement dans la plupart des clients email.

## Dépannage

### Q: J'obtiens "Connexion échouée" lors du test SMTP
**R:** Vérifiez :
- L'adresse du serveur SMTP et le port sont corrects
- Le nom d'utilisateur et le mot de passe sont corrects (utilisez un Mot de Passe d'Application pour Gmail)
- Votre connexion internet fonctionne
- Votre pare-feu ne bloque pas la connexion
- Essayez le port 587 avec chiffrement TLS

### Q: Ma personnalisation ne fonctionne pas
**R:** Vérifiez :
- Les noms de colonnes CSV correspondent exactement à vos `{{variables}}` (sensible à la casse)
- Pas d'espaces supplémentaires dans les noms de colonnes
- Le fichier CSV est correctement formaté
- Les variables dans votre modèle de message utilisent l'orthographe correcte

### Q: L'application ne démarre pas
**R:** Assurez-vous que :
- Python 3.8 ou supérieur est installé
- Vous avez installé avec le support GUI : `pip install emailer-simple-tool[gui]`
- Essayez de réinstaller : `pip uninstall emailer-simple-tool` puis `pip install emailer-simple-tool[gui]`

### Q: Les images ne se génèrent pas correctement
**R:** Vérifiez :
- Les paramètres du projet d'image sont configurés correctement
- Les éléments de texte ont des sources de données valides
- Les dimensions d'image sont raisonnables (pas trop grandes)
- Les polices sont disponibles sur votre système

## Questions de Performance

### Q: À quelle vitesse envoie-t-il les emails ?
**R:** L'outil peut traiter environ 478 emails par seconde, mais la vitesse d'envoi réelle dépend des limites de votre fournisseur d'email et de votre connexion internet.

### Q: À quelle vitesse génère-t-il les images ?
**R:** Environ 180 images par seconde sur du matériel typique. Les images complexes avec beaucoup d'éléments peuvent prendre plus de temps.

### Q: Ma campagne fonctionne lentement
**R:** Essayez :
- Réduire le nombre de destinataires (garder sous 100)
- Simplifier les projets d'images (moins d'éléments de texte)
- Utiliser des dimensions d'image plus petites
- Vérifier la vitesse de votre connexion internet

## Messages d'Erreur

### Q: "Authentification SMTP échouée"
**R:** Vos identifiants email sont incorrects. Vérifiez doublement :
- Nom d'utilisateur (généralement votre adresse email complète)
- Mot de passe (utilisez un Mot de Passe d'Application pour Gmail, pas votre mot de passe habituel)
- Les paramètres du serveur sont corrects pour votre fournisseur

### Q: Erreurs "Fichier non trouvé"
**R:** Assurez-vous que :
- Tous les fichiers requis existent (recipients.csv, subject.txt, msg.txt)
- Les noms de fichiers sont orthographiés correctement
- Les fichiers sont dans le bon dossier de campagne
- Vous avez la permission de lire les fichiers

### Q: "Format CSV invalide"
**R:** Votre fichier CSV a des problèmes de formatage :
- Assurez-vous qu'il est sauvegardé au format CSV (pas Excel)
- Vérifiez les virgules manquantes ou les guillemets supplémentaires
- Assurez-vous que la première ligne contient les en-têtes de colonnes
- Vérifiez qu'il n'y a pas de lignes vides au début

## Obtenir Plus d'Aide

### Q: Où puis-je trouver une aide plus détaillée ?
**R:** Utilisez les autres sections de ce système d'aide :
- **📁 Configuration de Campagne** - Création détaillée de campagne
- **📧 Configuration Email** - Configuration SMTP complète
- **🖼️ Générateur d'Images** - Fonctionnalités d'images avancées
- **🚀 Guide de Démarrage Rapide** - Guide de configuration en 5 minutes

### Q: L'aide ne répond pas à ma question
**R:** Essayez :
- Rechercher dans le système d'aide (utilisez la boîte de recherche)
- Vérifier la section dépannage
- Regarder les fichiers de documentation complets
- Tester avec une campagne simple d'abord pour isoler le problème

---

**Besoin encore d'aide ?** La plupart des problèmes peuvent être résolus en commençant par une campagne de test simple et en ajoutant graduellement de la complexité une fois que les bases fonctionnent.

*Bon emailing !* 📧
