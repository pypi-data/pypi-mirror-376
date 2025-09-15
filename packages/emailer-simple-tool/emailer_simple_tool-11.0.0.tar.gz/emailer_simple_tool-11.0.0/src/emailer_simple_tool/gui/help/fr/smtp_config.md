# 📧 Configuration Email (Configuration SMTP)

Guide complet pour configurer les paramètres de votre serveur email pour envoyer des campagnes.

## Qu'est-ce que SMTP ?

SMTP (Simple Mail Transfer Protocol) est la méthode standard pour envoyer des emails. Pour envoyer des emails via Emailer Simple Tool, vous devez le configurer avec les paramètres SMTP de votre fournisseur d'email.

## Configuration Rapide par Fournisseur

### 📧 Gmail (Le Plus Courant)

#### Paramètres
- **Serveur SMTP** : `smtp.gmail.com`
- **Port** : `587`
- **Sécurité** : TLS/STARTTLS
- **Nom d'utilisateur** : Votre adresse Gmail complète (ex: `votrenom@gmail.com`)
- **Mot de passe** : Mot de Passe d'Application (PAS votre mot de passe Gmail habituel)

#### Obtenir un Mot de Passe d'Application Gmail
1. **Activez l'Authentification à 2 Facteurs** (requis d'abord)
   - Allez dans Compte Google → Sécurité
   - Activez la Vérification en 2 étapes
2. **Générez un Mot de Passe d'Application**
   - Allez dans Sécurité → Mots de passe d'application
   - Sélectionnez "Mail" comme application
   - Copiez le mot de passe à 16 caractères
3. **Utilisez le Mot de Passe d'Application** dans Emailer Simple Tool (pas votre mot de passe habituel)

#### Problèmes Courants Gmail
- **"Authentification échouée"** → Utilisez un Mot de Passe d'Application, pas le mot de passe habituel
- **"Applications moins sécurisées"** → Utilisez un Mot de Passe d'Application à la place
- **"Connexion refusée"** → Vérifiez le port 587 et TLS activé

### 📧 Outlook/Hotmail

#### Paramètres
- **Serveur SMTP** : `smtp-mail.outlook.com`
- **Port** : `587`
- **Sécurité** : TLS/STARTTLS
- **Nom d'utilisateur** : Votre adresse Outlook complète
- **Mot de passe** : Votre mot de passe Outlook habituel

#### Conseils Outlook
- Fonctionne généralement avec le mot de passe habituel (pas besoin de mot de passe d'application)
- Si problèmes, essayez d'activer "Accès aux applications moins sécurisées" dans les paramètres du compte
- Pour les comptes Office 365 d'entreprise, vérifiez avec le département IT

### 📧 Yahoo Mail

#### Paramètres
- **Serveur SMTP** : `smtp.mail.yahoo.com`
- **Port** : `587` ou `465`
- **Sécurité** : TLS/STARTTLS (port 587) ou SSL (port 465)
- **Nom d'utilisateur** : Votre adresse Yahoo complète
- **Mot de passe** : Mot de Passe d'Application (recommandé)

#### Obtenir un Mot de Passe d'Application Yahoo
1. Allez dans Sécurité du Compte Yahoo
2. Générez un mot de passe d'application pour "Mail"
3. Utilisez le mot de passe généré dans Emailer Simple Tool

### 📧 Autres Fournisseurs

#### Modèle de Paramètres Courants
La plupart des fournisseurs d'email suivent des modèles similaires :
- **Serveur** : `smtp.votredomaine.com` ou `mail.votredomaine.com`
- **Port** : `587` (TLS) ou `465` (SSL) ou `25` (non sécurisé)
- **Sécurité** : TLS/STARTTLS préféré

#### Trouver Vos Paramètres
1. **Recherchez en ligne** : "[votre fournisseur] paramètres SMTP"
2. **Vérifiez la documentation du fournisseur**
3. **Contactez votre fournisseur d'email** ou département IT
4. **Essayez les modèles courants** avec votre domaine

## Configuration Étape par Étape

### 1. Ouvrir l'Onglet SMTP

Dans Emailer Simple Tool :
1. Allez dans l'onglet **📧 SMTP**
2. Vous verrez le formulaire de configuration SMTP

### 2. Entrer les Paramètres du Serveur

#### Serveur SMTP
- Entrez l'adresse du serveur SMTP de votre fournisseur
- Exemples : `smtp.gmail.com`, `smtp-mail.outlook.com`
- Pas besoin de préfixe `http://` ou `https://`

#### Port
- **587** - Le plus courant, utilise le chiffrement TLS
- **465** - Chiffrement SSL (ancien standard)
- **25** - Non chiffré (non recommandé)

#### Sécurité
- **TLS/STARTTLS** - Recommandé, fonctionne avec le port 587
- **SSL** - Ancien standard, fonctionne avec le port 465
- **Aucune** - Non chiffré, non recommandé

### 3. Entrer les Identifiants

#### Nom d'Utilisateur
- Généralement votre adresse email complète
- Certains fournisseurs peuvent utiliser juste la partie nom d'utilisateur
- Sensible à la casse pour certains fournisseurs

#### Mot de Passe
- **Gmail** : Utilisez un Mot de Passe d'Application (16 caractères)
- **Outlook** : Généralement le mot de passe habituel
- **Yahoo** : Mot de Passe d'Application recommandé
- **Autres** : Vérifiez les exigences du fournisseur

### 4. Tester la Connexion

#### Testez Toujours d'Abord
1. Cliquez sur le bouton **"Tester la Connexion"**
2. Attendez le résultat de la connexion
3. Corrigez tout problème avant de continuer

#### Indicateurs de Succès
- ✅ "Connexion réussie"
- ✅ "Authentification réussie"
- ✅ "Prêt à envoyer des emails"

#### Messages d'Erreur
- ❌ "Connexion échouée" → Vérifiez le serveur et le port
- ❌ "Authentification échouée" → Vérifiez nom d'utilisateur/mot de passe
- ❌ "Erreur SSL/TLS" → Vérifiez les paramètres de sécurité

## Dépannage des Problèmes Courants

### Connexion Échouée

#### Vérifier le Réseau
- **Connexion internet** fonctionne ?
- **Pare-feu** bloque la connexion ?
- **VPN** interfère avec la connexion ?

#### Vérifier les Paramètres
- **Adresse du serveur** orthographiée correctement ?
- **Numéro de port** correct pour votre fournisseur ?
- **Type de sécurité** correspond aux exigences du fournisseur ?

### Authentification Échouée

#### Problèmes de Mot de Passe
- **Gmail** : Utilisez un Mot de Passe d'Application (pas le mot de passe habituel) ?
- **Caractères spéciaux** dans le mot de passe causent des problèmes ?
- **Copier/coller** le mot de passe pour éviter les fautes de frappe ?

#### Problèmes de Nom d'Utilisateur
- **Adresse email complète** vs juste nom d'utilisateur ?
- **Sensibilité à la casse** - essayez en minuscules ?
- **Espaces supplémentaires** avant ou après le nom d'utilisateur ?

### Erreurs SSL/TLS

#### Paramètres de Sécurité
- **Port 587** → Utilisez TLS/STARTTLS
- **Port 465** → Utilisez SSL
- **Port 25** → Utilisez Aucune (si autorisé)

#### Exigences du Fournisseur
- Certains fournisseurs **exigent** des types de sécurité spécifiques
- Vérifiez la documentation du fournisseur pour les exigences
- Essayez différentes combinaisons sécurité/port

### Problèmes Spécifiques aux Fournisseurs

#### Problèmes Gmail
- **Authentification à 2 facteurs** activée ?
- **Mot de Passe d'Application** généré et utilisé ?
- **"Applications moins sécurisées"** désactivées (utilisez un Mot de Passe d'Application à la place) ?

#### Problèmes d'Email d'Entreprise
- **Politiques IT** peuvent bloquer l'accès SMTP externe
- **VPN requis** pour l'accès externe ?
- **Méthodes d'authentification spéciales** requises ?
- Contactez votre département IT pour assistance

## Configuration Avancée

### Fournisseurs SMTP Personnalisés

#### Serveurs Exchange d'Entreprise
- Serveur généralement : `mail.votreentreprise.com`
- Peut nécessiter une authentification de domaine : `DOMAINE\nomutilisateur`
- Vérifiez avec le département IT pour les paramètres exacts

#### Services Email Tiers
- **SendGrid**, **Mailgun**, **Amazon SES**, etc.
- Chacun a des paramètres SMTP spécifiques
- Nécessitent généralement des clés API ou une authentification spéciale
- Vérifiez la documentation du service pour la configuration SMTP

### Considérations de Sécurité

#### Sécurité des Mots de Passe
- **Les Mots de Passe d'Application** sont plus sûrs que les mots de passe habituels
- **Mot de passe différent** pour chaque application
- **Révoquer l'accès** facilement si nécessaire

#### Sécurité de Connexion
- **Utilisez toujours TLS/SSL** quand disponible
- **Évitez les connexions non chiffrées** (port 25)
- **Vérifiez les avertissements de certificat** s'ils apparaissent

## Tester Votre Configuration

### Processus de Test d'Email

#### Avant d'Envoyer des Campagnes
1. **Configurez les paramètres SMTP**
2. **Testez la connexion** avec succès
3. **Créez une campagne de test simple** (1-2 destinataires)
4. **Test à blanc d'abord** pour vérifier la génération d'email
5. **Envoyez une campagne de test** à vous-même
6. **Vérifiez l'email reçu** pour le formatage et le contenu

#### Ce qu'il Faut Vérifier
- **L'email arrive** dans la boîte de réception (pas spam)
- **Formatage préservé** (si utilisant .docx)
- **Pièces jointes incluses** (s'il y en a)
- **Personnalisation fonctionne** correctement
- **Images s'affichent** correctement (si utilisant le générateur d'images)

### Test de Performance

#### Vitesse de Connexion
- **Testez avec de petites campagnes** d'abord
- **Surveillez la vitesse d'envoi** et le taux de succès
- **Vérifiez les limites de débit** de votre fournisseur

#### Limites des Fournisseurs
- **Gmail** : ~100 emails/jour pour les comptes gratuits
- **Outlook** : ~300 emails/jour pour les comptes gratuits
- **Entreprise** : Vérifiez avec IT pour les limites
- **Services payants** : Généralement des limites plus élevées

## Meilleures Pratiques

### Délivrabilité des Emails

#### Éviter les Filtres Spam
- **Utilisez un fournisseur d'email réputé** (Gmail, Outlook, etc.)
- **Authentifiez-vous correctement** avec les bons identifiants
- **Évitez les mots déclencheurs de spam** dans les lignes d'objet
- **Gardez les listes de destinataires propres** et pertinentes

#### Envoi Professionnel
- **Utilisez une adresse email d'entreprise** quand possible
- **Incluez des informations de désabonnement** pour les emails marketing
- **Respectez les préférences des destinataires**
- **Surveillez les taux de rebond** et supprimez les mauvaises adresses

### Meilleures Pratiques de Sécurité

#### Gestion des Identifiants
- **Utilisez des Mots de Passe d'Application** quand disponibles
- **Ne partagez pas les identifiants** avec d'autres
- **Changez les mots de passe régulièrement**
- **Révoquez les mots de passe d'application inutilisés**

#### Test Sécurisé
- **Testez toujours avec vous-même d'abord**
- **Utilisez des tests à blanc** avant l'envoi réel
- **Commencez avec de petites listes de destinataires**
- **Vérifiez le contenu** avant l'envoi

## Liste de Vérification de Dépannage

Quand SMTP ne fonctionne pas, vérifiez ces éléments dans l'ordre :

### ✅ Vérifications de Base
- [ ] Connexion internet fonctionne
- [ ] Adresse du serveur SMTP correcte
- [ ] Numéro de port correct
- [ ] Type de sécurité correspond au port

### ✅ Vérifications d'Authentification
- [ ] Nom d'utilisateur est l'adresse email complète
- [ ] Mot de passe est correct (Mot de Passe d'Application pour Gmail)
- [ ] Pas d'espaces supplémentaires dans les identifiants
- [ ] Sensibilité à la casse considérée

### ✅ Vérifications Spécifiques au Fournisseur
- [ ] Authentification à 2 facteurs activée (Gmail)
- [ ] Mot de Passe d'Application généré (Gmail/Yahoo)
- [ ] Applications moins sécurisées désactivées (utilisez Mot de Passe d'Application)
- [ ] Politiques d'entreprise autorisent SMTP (comptes d'entreprise)

### ✅ Vérifications Réseau
- [ ] Pare-feu ne bloque pas la connexion
- [ ] VPN n'interfère pas
- [ ] Antivirus ne bloque pas
- [ ] Essayez un réseau différent si possible

### ✅ Vérifications Avancées
- [ ] Essayez différentes combinaisons port/sécurité
- [ ] Testez avec un client email (Outlook, Thunderbird)
- [ ] Vérifiez la page de statut du fournisseur
- [ ] Contactez le support du fournisseur si nécessaire

---

## Prochaines Étapes

Une fois SMTP configuré avec succès :

1. **📁 Créer une Campagne** - Configurez votre campagne email
2. **🚀 Tester avec Test à Blanc** - Testez toujours avant d'envoyer
3. **📧 Envoyer la Campagne** - Envoyez vos emails personnalisés
4. **📊 Examiner les Résultats** - Vérifiez les rapports d'envoi et la livraison

**Rappelez-vous** : Testez toujours votre configuration SMTP avec une petite campagne de test avant d'envoyer à votre liste complète de destinataires !

---

*Besoin de plus d'aide ? Vérifiez la section FAQ ou utilisez la fonction de recherche pour trouver des informations spécifiques de dépannage SMTP.*
