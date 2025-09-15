# 🚀 Guide d'Envoi d'Emails

Guide complet pour tester et envoyer vos campagnes email de manière sûre et efficace.

## Aperçu

L'onglet Envoi est votre centre de contrôle pour les campagnes email. Il fournit des outils complets pour tester, valider et envoyer des emails personnalisés avec des fonctionnalités de sécurité intégrées pour prévenir les erreurs.

## Approche Sécurité d'Abord

### Pourquoi la Sécurité Importe

Les campagnes email ne peuvent pas être "annulées" une fois envoyées. L'onglet Envoi implémente plusieurs couches de sécurité :
- **Validation obligatoire** - Tous les problèmes doivent être résolus avant l'envoi
- **Tests à blanc requis** - Doit tester avant d'envoyer de vrais emails
- **Dialogues de confirmation** - Confirmations multiples préviennent les accidents
- **Surveillance du progrès** - Suivez le progrès d'envoi et détectez les problèmes tôt

### Fonctionnalités de Sécurité Intégrées

#### Validation de Campagne
- ✅ Tous les fichiers requis existent et sont valides
- ✅ Les données CSV sont correctement formatées
- ✅ Les adresses email sont valides
- ✅ La configuration SMTP fonctionne
- ✅ Pas de destinataires dupliqués

#### Exigences de Test à Blanc
- 🧪 Doit effectuer un test à blanc avant l'envoi
- 🧪 Le test à blanc doit être "frais" (reflète l'état actuel de la campagne)
- 🧪 Tout changement de campagne nécessite un nouveau test à blanc
- 🧪 Les indicateurs visuels montrent le statut du test à blanc

## Validation de Campagne

### Validation Automatique

Le système valide continuellement votre campagne et affiche des indicateurs de statut :

#### Statut Vert (Prêt)
- ✅ **Tous les fichiers présents** - recipients.csv, subject.txt, fichier message
- ✅ **Format CSV valide** - Formatage et en-têtes corrects
- ✅ **Adresses email valides** - Tous les emails correctement formatés
- ✅ **SMTP configuré** - Paramètres du serveur email testés et fonctionnels
- ✅ **Pas de doublons** - Chaque adresse email n'apparaît qu'une fois

#### Statut Rouge (Problèmes Trouvés)
- ❌ **Fichiers manquants** - Fichiers de campagne requis non trouvés
- ❌ **CSV invalide** - Erreurs de formatage ou colonnes manquantes
- ❌ **Mauvaises adresses email** - Adresses email invalides ou mal formées
- ❌ **SMTP non configuré** - Paramètres du serveur email manquants ou invalides
- ❌ **Destinataires dupliqués** - La même adresse email apparaît plusieurs fois

#### Statut Jaune (Avertissements)
- ⚠️ **Grande liste de destinataires** - Plus de 100 destinataires (avertissement de performance)
- ⚠️ **Grandes pièces jointes** - Taille totale des pièces jointes plus de 10MB
- ⚠️ **Personnalisation manquante** - Variables dans les modèles non trouvées dans le CSV

### Résoudre les Problèmes de Validation

#### Fichiers Manquants
1. **Vérifiez le dossier de campagne** - Assurez-vous que tous les fichiers requis existent
2. **Vérifiez les noms de fichiers** - Doivent être exactement : recipients.csv, subject.txt, msg.txt/msg.docx
3. **Vérifiez les permissions de fichiers** - Assurez-vous que les fichiers sont lisibles

#### Problèmes de Format CSV
1. **Ouvrez dans un éditeur de texte** - Vérifiez les problèmes de formatage
2. **Vérifiez les en-têtes** - La première ligne doit contenir les noms de colonnes
3. **Vérifiez les virgules** - Assurez-vous d'une séparation par virgules correcte
4. **Supprimez les lignes vides** - Pas de lignes vides au début ou à la fin
5. **Sauvegardez comme CSV** - Pas au format Excel

#### Adresses Email Invalides
1. **Vérifiez le format** - Doit être au format nom@domaine.com
2. **Supprimez les espaces** - Pas d'espaces avant ou après les adresses email
3. **Corrigez les fautes de frappe** - Problèmes courants : @ manquant, mauvaises extensions de domaine
4. **Supprimez les entrées invalides** - Supprimez ou corrigez les adresses problématiques

#### Configuration SMTP
1. **Allez dans l'onglet SMTP** - Configurez les paramètres du serveur email
2. **Testez la connexion** - Utilisez le bouton "Tester la Connexion"
3. **Vérifiez les identifiants** - Vérifiez le nom d'utilisateur et le mot de passe
4. **Vérifiez les paramètres** - Le serveur, port, type de sécurité doivent être corrects

## Test à Blanc

### Qu'est-ce qu'un Test à Blanc ?

Un test à blanc génère tous les emails qui seraient envoyés, mais les sauvegarde comme fichiers au lieu de les envoyer réellement. Cela vous permet de :
- **Prévisualiser le contenu exact** pour chaque destinataire
- **Vérifier que la personnalisation** fonctionne correctement
- **Vérifier que les pièces jointes** sont incluses correctement
- **Tester le formatage** et la mise en page
- **Détecter les erreurs** avant l'envoi réel

### Effectuer un Test à Blanc

#### Étape 1 : Assurez-vous que la Campagne est Valide
- Tous les indicateurs de validation doivent être verts
- La configuration SMTP doit être testée et fonctionnelle

#### Étape 2 : Démarrer le Test à Blanc
1. Cliquez sur le bouton **"Test à Blanc"** dans l'onglet Envoi
2. Choisissez les options de test à blanc :
   - **Tous les destinataires** - Générer des emails pour tout le monde
   - **10 premiers destinataires** - Test rapide avec un sous-ensemble
   - **Plage personnalisée** - Spécifiez quels destinataires tester

#### Étape 3 : Surveiller le Progrès
- La barre de progrès montre le statut de génération
- Mises à jour en temps réel sur les emails en cours de traitement
- Messages d'erreur si des problèmes surviennent

#### Étape 4 : Examiner les Résultats
- Le test à blanc crée un dossier : `campagne/dryrun/AAAA-MM-JJ_HH-MM-SS/`
- Chaque destinataire obtient un fichier .eml individuel
- Ouvrez les fichiers .eml dans un client email pour prévisualiser

### Sortie du Test à Blanc

#### Structure des Fichiers
```
campagne/
└── dryrun/
    └── 2025-08-19_14-30-15/
        ├── john.doe@example.com.eml
        ├── jane.smith@company.com.eml
        ├── bob.wilson@firm.com.eml
        └── dry_run_report.txt
```

#### Ce qu'il Faut Vérifier

**Contenu Email**
- ✅ **Personnalisation fonctionne** - Noms, entreprises remplis correctement
- ✅ **Ligne d'objet correcte** - Variables remplacées correctement
- ✅ **Formatage du message** - Texte/HTML s'affiche correctement
- ✅ **Pas de données manquantes** - Toutes les variables ont des valeurs

**Pièces Jointes**
- ✅ **Pièces jointes statiques incluses** - Fichiers du dossier attachments
- ✅ **Images générées jointes** - Images personnalisées (si utilisées)
- ✅ **Tailles de fichiers raisonnables** - Pas trop grandes pour la livraison email
- ✅ **Tous les destinataires ont des pièces jointes** - Cohérent pour tous les emails

**Détails Techniques**
- ✅ **En-têtes email corrects** - De, À, Objet correctement définis
- ✅ **Encodage correct** - Les caractères spéciaux s'affichent correctement
- ✅ **Structure MIME valide** - Le format email est conforme aux standards

### Rapports de Test à Blanc

#### Contenu du Rapport
Le rapport de test à blanc (`dry_run_report.txt`) contient :
- **Statistiques de résumé** - Total emails, comptes succès/échec
- **Temps de traitement** - Combien de temps la génération a pris
- **Tailles de fichiers** - Tailles d'emails individuelles et totales
- **Détails d'erreur** - Tout problème rencontré
- **Liste des destinataires** - Tous les destinataires traités

#### Lire le Rapport
```
Rapport de Test à Blanc - 2025-08-19 14:30:15
===============================================
Campagne : Invitations Fête de Noël
Total Destinataires : 25
Réussis : 25
Échoués : 0
Temps de Traitement Total : 2,3 secondes
Taille Moyenne Email : 145 KB
Taille Totale Campagne : 3,6 MB

Détails Destinataires :
✅ john.doe@example.com (152 KB)
✅ jane.smith@company.com (138 KB)
✅ bob.wilson@firm.com (149 KB)
...
```

## Envoyer Votre Campagne

### Liste de Vérification Pré-Envoi

Avant d'envoyer de vrais emails, vérifiez :
- ✅ **Test à blanc terminé avec succès** - Pas d'erreurs dans le test
- ✅ **Contenu examiné** - Vérifié les fichiers .eml d'échantillon
- ✅ **Liste de destinataires vérifiée** - Bonnes personnes, pas de doublons
- ✅ **SMTP testé** - Connexion fonctionne correctement
- ✅ **Timing approprié** - Envoi au bon moment pour les destinataires

### Processus d'Envoi

#### Étape 1 : Validation Finale
- Le système effectue une vérification de validation finale
- Tous les problèmes précédents doivent être résolus
- Un test à blanc frais doit exister (reflète l'état actuel de la campagne)

#### Étape 2 : Confirmation d'Envoi
Plusieurs étapes de confirmation préviennent les envois accidentels :

**Résumé de Campagne**
- Montre le nombre de destinataires, l'objet et les détails clés
- Affiche la taille totale de l'email et le temps d'envoi estimé
- Liste tout avertissement ou note importante

**Taper le Nom de Campagne**
- Doit taper le nom exact du dossier de campagne pour confirmer
- Prévient les envois accidentels de la mauvaise campagne
- La boîte de texte montre le nom de campagne comme placeholder

**Cases de Confirmation Finale**
- ☑️ "J'ai examiné les résultats du test à blanc"
- ☑️ "Je confirme que c'est la bonne campagne à envoyer"
- ☑️ "Je comprends que cette action ne peut pas être annulée"

#### Étape 3 : Progrès d'Envoi
- Barre de progrès en temps réel montre le statut d'envoi
- Mises à jour de statut de destinataires individuels
- Comptes succès/échec
- Temps restant estimé

#### Étape 4 : Achèvement d'Envoi
- Rapport final avec statistiques complètes
- Liste des envois réussis et échoués
- Rapport d'envoi sauvegardé pour référence future

### Surveillance du Progrès d'Envoi

#### Mises à Jour en Temps Réel
```
Envoi de Campagne : Invitations Fête de Noël
Progrès : [████████████████████████████████] 100%
Envoyés : 23/25 | Échoués : 2/25 | Restants : 0
Écoulé : 45 secondes | Restant estimé : 0 secondes

Actuel : Envoi à bob.wilson@firm.com...
Dernier terminé : jane.smith@company.com ✅
```

#### Indicateurs de Statut
- ✅ **Succès** - Email envoyé avec succès
- ❌ **Échoué** - Email a échoué à l'envoi (avec raison)
- ⏳ **Envoi** - Actuellement en cours d'envoi
- ⏸️ **En Pause** - Envoi en pause (peut reprendre)
- ⏹️ **Arrêté** - Envoi arrêté par l'utilisateur

### Gérer les Erreurs d'Envoi

#### Erreurs d'Envoi Courantes

**Authentification SMTP Échouée**
- **Cause** : Identifiants email incorrects ou expirés
- **Solution** : Re-testez les paramètres SMTP, mettez à jour le mot de passe si nécessaire

**Adresse Destinataire Rejetée**
- **Cause** : Adresse email invalide ou bloquée par le serveur
- **Solution** : Vérifiez l'adresse email, supprimez si définitivement invalide

**Message Trop Grand**
- **Cause** : Email dépasse les limites de taille (généralement 25MB)
- **Solution** : Réduisez les tailles de pièces jointes ou supprimez les gros fichiers

**Limite de Débit Dépassée**
- **Cause** : Envoi trop rapide pour les limites du fournisseur email
- **Solution** : Réduisez la vitesse d'envoi, attendez et réessayez

#### Récupération d'Erreur
- **Pausez l'envoi** - Arrêtez pour enquêter sur les problèmes
- **Corrigez les problèmes** - Corrigez les paramètres SMTP ou données destinataires
- **Reprenez l'envoi** - Continuez d'où ça s'est arrêté
- **Réessayez les échecs** - Tentez de renvoyer les emails échoués

## Rapports d'Envoi et Historique

### Rapports d'Envoi

#### Génération de Rapport
Après chaque envoi, un rapport détaillé est automatiquement créé :
- **Emplacement** : `campagne/sentreport/AAAA-MM-JJ_HH-MM-SS/`
- **Format** : Fichier texte avec statistiques complètes
- **Contenu** : Détails succès/échec pour chaque destinataire

#### Contenu du Rapport
```
Rapport d'Envoi de Campagne Email
=================================
Campagne : Invitations Fête de Noël
Date d'Envoi : 2025-08-19 14:45:30
Total Destinataires : 25
Envoyés avec Succès : 23
Échec d'Envoi : 2
Taux de Succès : 92%
Temps Total d'Envoi : 3 minutes 15 secondes

Envois Réussis :
✅ john.doe@example.com (14:45:32)
✅ jane.smith@company.com (14:45:35)
✅ alice.johnson@corp.com (14:45:38)
...

Envois Échoués :
❌ bad.email@invalid.domain (14:46:12) - Domaine non trouvé
❌ full.mailbox@company.com (14:46:45) - Boîte aux lettres pleine
```

### Historique d'Envoi

#### Suivi des Envois Précédents
- **Tous les envois enregistrés** - Historique complet maintenu
- **Archive de rapports** - Tous les rapports d'envoi sauvegardés
- **Versions de campagne** - Suivez les changements entre les envois
- **Métriques de performance** - Taux de succès et données de timing

#### Gestion de l'Historique d'Envoi
- **Voir les rapports passés** - Accédez à tous les rapports d'envoi précédents
- **Comparer les campagnes** - Voir les différences de performance
- **Nettoyer les anciens rapports** - Supprimez les rapports obsolètes pour économiser l'espace
- **Exporter les données** - Sauvegardez les rapports pour analyse externe

## Meilleures Pratiques

### Timing de Vos Envois

#### Heures d'Envoi Optimales
- **Mardi-Jeudi** - Généralement meilleurs taux de réponse
- **10h-14h** - Heures de pointe de lecture d'emails
- **Évitez les lundis** - Les gens rattrapent le weekend
- **Évitez les vendredis** - Les gens se préparent pour le weekend
- **Considérez les fuseaux horaires** - Envoyez quand les destinataires sont actifs

#### Considérations de Planification
- **Emails d'affaires** - Envoyez pendant les heures de bureau
- **Emails personnels** - Le soir ou weekend peut être mieux
- **Destinataires internationaux** - Considérez plusieurs fuseaux horaires
- **Conscience des vacances** - Évitez les jours fériés majeurs

### Délivrabilité des Emails

#### Améliorer les Taux de Livraison
- **Listes de destinataires propres** - Supprimez les adresses rebondies/invalides
- **Contenu pertinent** - Envoyez seulement aux destinataires intéressés
- **Expéditeur professionnel** - Utilisez une adresse email d'entreprise
- **Évitez les déclencheurs de spam** - N'utilisez pas de lignes d'objet type spam
- **Incluez désabonnement** - Pour les emails marketing

#### Surveillance de la Livraison
- **Vérifiez les taux de rebond** - Les rebonds élevés nuisent à la réputation
- **Surveillez les plaintes spam** - Supprimez les plaignants des listes
- **Suivez l'engagement** - Le faible engagement affecte la délivrabilité
- **Utilisez un SMTP réputé** - Les fournisseurs de qualité aident la livraison

### Optimisation des Performances

#### Envoi Plus Rapide
- **Listes de destinataires plus petites** - Sous 100 pour de meilleures performances
- **Réduisez les tailles de pièces jointes** - Les emails plus petits s'envoient plus rapidement
- **Contenu email simple** - Le texte brut s'envoie plus rapidement que le HTML
- **Fournisseur SMTP fiable** - Les fournisseurs de qualité gèrent mieux le volume

#### Gestion des Ressources
- **Fermez d'autres applications** - Libérez les ressources système
- **Connexion internet stable** - Évitez les interruptions pendant l'envoi
- **Espace disque suffisant** - Pour les rapports et fichiers temporaires
- **Surveillez les performances système** - Surveillez les problèmes mémoire/CPU

## Dépannage

### Problèmes Courants

#### Le Test à Blanc Échoue
- **Vérifiez la validation de campagne** - Résolvez tous les problèmes rouge/jaune
- **Vérifiez les permissions de fichiers** - Assurez-vous que les fichiers sont lisibles
- **Vérifiez l'espace disque** - Besoin d'espace pour les fichiers générés
- **Examinez les messages d'erreur** - Cherchez les raisons d'échec spécifiques

#### L'Envoi S'Arrête/Échoue
- **Connexion SMTP perdue** - Vérifiez la connexion internet
- **Authentification expirée** - Re-testez les identifiants SMTP
- **Limites de débit atteintes** - Attendez et réessayez avec une vitesse plus lente
- **Problèmes de destinataires** - Vérifiez les adresses email invalides

#### Taux de Livraison Médiocres
- **Vérifiez les dossiers spam** - Demandez aux destinataires de vérifier le spam
- **Vérifiez la réputation de l'expéditeur** - Utilisez une adresse email établie
- **Examinez le contenu** - Évitez les mots déclencheurs de spam
- **Vérifiez l'engagement des destinataires** - Supprimez les destinataires non engagés

### Obtenir de l'Aide

#### Informations de Diagnostic
Lors du signalement de problèmes, incluez :
- **Messages d'erreur** - Texte exact de tout message d'erreur
- **Rapports d'envoi** - Contenu des rapports d'envoi échoués
- **Détails de campagne** - Nombre de destinataires, tailles de pièces jointes
- **Informations système** - Système d'exploitation, type de connexion internet

#### Ressources de Support
- **📚 Système d'Aide** - Recherchez dans ce système d'aide pour des solutions
- **❓ FAQ** - Vérifiez les questions fréquemment posées
- **🔧 Dépannage** - Guides de dépannage détaillés
- **📖 Documentation** - Documentation utilisateur complète

---

## Résumé

L'onglet Envoi fournit des outils complets pour une livraison de campagne email sûre et efficace :

1. **Validez** - Assurez-vous que la campagne est correctement configurée
2. **Testez** - Effectuez toujours un test à blanc avant l'envoi
3. **Examinez** - Vérifiez soigneusement les résultats du test à blanc
4. **Envoyez** - Utilisez le processus de confirmation pour envoyer en sécurité
5. **Surveillez** - Suivez le progrès et gérez tout problème
6. **Rapportez** - Examinez les rapports d'envoi pour des insights

**Rappelez-vous** : Les fonctionnalités de sécurité sont là pour vous protéger. Utilisez toujours les tests à blanc, lisez soigneusement les dialogues de confirmation, et commencez avec de petites campagnes de test lors de l'essai de nouvelles fonctionnalités.

---

*Besoin de plus d'aide ? Utilisez la fonction de recherche pour trouver des sujets d'envoi spécifiques ou vérifiez la section dépannage pour les problèmes courants.*
