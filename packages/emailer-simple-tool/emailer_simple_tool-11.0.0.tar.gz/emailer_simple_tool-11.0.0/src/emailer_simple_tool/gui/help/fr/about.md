# ℹ️ À Propos d'Emailer Simple Tool

## Qu'est-ce qu'Emailer Simple Tool ?

Emailer Simple Tool est une application professionnelle de gestion de campagnes email conçue pour rendre l'envoi d'emails personnalisés simple et accessible à tous.

## 🎯 Parfait Pour

- **Invitations d'Événements** avec détails personnels
- **Newsletters** avec noms des destinataires
- **Communications d'Affaires** à plusieurs clients
- **Campagnes Marketing** avec images personnalisées
- **Tout email** nécessitant des informations personnelles pour chaque destinataire

## ✨ Fonctionnalités Clés

### 🎨 Interface Duale
- **Interface Graphique (GUI)** - Pointer-cliquer pour les débutants
- **Interface en Ligne de Commande (CLI)** - Automatisation pour les utilisateurs avancés

### 📧 Personnalisation d'Emails
- Utilisez les données CSV pour personnaliser les emails avec des `{{variables}}`
- Support pour des modèles de personnalisation complexes
- Validation automatique des données et modèles

### 🖼️ Génération d'Images
- Créez des images personnalisées avec texte et graphiques
- Création de projet guidée par assistant
- Capacités de fusion d'images professionnelles

### 📎 Support de Contenu Riche
- Messages **Texte Brut** (fichiers .txt)
- Support **Texte Enrichi** avec fichiers .docx (polices, couleurs, formatage)
- **Pièces Jointes Statiques** - Ajoutez des fichiers à tous les emails
- **Images Dynamiques** - Images personnalisées par destinataire

### 🛡️ Sécurité et Sûreté
- **Test à Blanc** - Prévisualisez les emails avant envoi
- **Identifiants Chiffrés** - Stockage sécurisé des mots de passe SMTP
- **Traitement Local** - Toutes les données restent sur votre ordinateur
- **Validation Complète** - Prévenez les erreurs courantes

### 🌍 Support Multi-Langues
- Interfaces **Anglais** et **Français**
- **Changement de Langue Dynamique** - Changez de langue sans redémarrage
- **Documentation Localisée** - Aide dans votre langue préférée

## 📊 Performance

- **Génération d'Images** : 180 images/seconde
- **Traitement d'Emails** : 478 emails/seconde
- **Recommandé** : Jusqu'à 100 destinataires par campagne pour des performances optimales

## 🖥️ Configuration Système Requise

### Exigences Minimales
- **Python 3.8** ou supérieur
- **512MB RAM** disponible
- **100MB d'espace** de stockage
- **Connexion Internet** pour envoyer des emails

### Plateformes Supportées
- **Windows** 10/11
- **macOS** 10.14 ou ultérieur
- **Linux** (Ubuntu, Debian, CentOS, etc.)

### Fournisseurs d'Email Supportés
- **Gmail** (avec Mots de Passe d'Application)
- **Outlook/Hotmail**
- **Yahoo Mail**
- **Serveurs Exchange** d'entreprise
- **Tout service email** compatible SMTP

## 🏗️ Architecture Technique

### Composants Principaux
- **Gestionnaire de Campagne** - Gère la création et validation de campagnes
- **Expéditeur d'Email** - Gère les connexions SMTP et la livraison d'emails
- **Générateur d'Images** - Crée des images personnalisées avec fusion de texte
- **Processeur de Modèles** - Gère la personnalisation d'emails avec données CSV

### Structure de Fichiers
```
Dossier Campagne/
├── recipients.csv          # Liste d'emails avec données de personnalisation
├── subject.txt            # Modèle d'objet d'email
├── msg.txt ou msg.docx    # Modèle de message d'email
├── attachments/           # Fichiers statiques à joindre
├── picture-generator/     # Projets d'images personnalisées
├── dryrun/               # Sorties d'emails de test
└── logs/                 # Journaux d'application
```

## 🔒 Sécurité et Confidentialité

### Protection des Données
- **Traitement Local** - Toutes les données traitées sur votre ordinateur
- **Pas de Stockage Cloud** - Aucune donnée envoyée vers des serveurs externes
- **Identifiants Chiffrés** - Mots de passe SMTP chiffrés localement
- **Transmission Sécurisée** - Emails envoyés via connexions SMTP sécurisées

### Ce Que Nous Ne Collectons Pas
- **Aucune Collecte de Données Personnelles**
- **Aucune Analytique d'Usage** envoyée externement
- **Aucun Contenu d'Email** stocké ou transmis à des tiers
- **Aucune Liste de Destinataires** partagée ou stockée externement

## 📜 Informations de Version

### Version Actuelle
**Version 10.0.8** - Publiée le 18 août 2025

### Mises à Jour Récentes
- **Correction Rotation Texte Windows** - Résolu les problèmes de découpage pour le texte pivoté
- **Génération d'Images Améliorée** - Rotation de texte basée sur PIL améliorée
- **Compatibilité Multi-Plateforme** - Meilleur support Windows, macOS, Linux

### Historique des Versions
- **v10.x** - Implémentation GUI avec génération d'images
- **v9.x** - Onglet d'envoi et gestion de campagnes
- **v8.x** - Générateur d'images avec fusion de texte
- **v7.x** - GUI et validation améliorés
- **v6.x** - Implémentation GUI initiale
- **v5.x** - Fondation CLI et fonctionnalités principales

## 🤝 Support et Communauté

### Obtenir de l'Aide
- **📚 Aide Intégrée** - Ce système d'aide (vous l'utilisez maintenant !)
- **📖 Documentation** - Guides utilisateur complets en anglais et français
- **❓ FAQ** - Questions courantes et solutions
- **🔧 Dépannage** - Résolution de problèmes étape par étape

### Commentaires et Contributions
Nous accueillons les commentaires et suggestions pour améliorer Emailer Simple Tool !

## 📄 Licence et Légal

### Open Source
Emailer Simple Tool est développé comme logiciel open source, le rendant gratuit à utiliser pour un usage personnel et commercial.

### Composants Tiers
- **PySide6** - Framework GUI (Qt pour Python)
- **Pillow (PIL)** - Bibliothèque de traitement d'images
- **cryptography** - Stockage sécurisé d'identifiants
- **python-docx** - Traitement de documents Microsoft Word

## 🚀 Développement Futur

### Fonctionnalités Prévues
- **Système d'Aide Amélioré** - Tutoriels et guides interactifs
- **Modèles d'Images Avancés** - Plus d'options de personnalisation d'images
- **Performance Améliorée** - Traitement plus rapide pour les grandes campagnes
- **Langues Supplémentaires** - Plus d'options de langues d'interface

### Philosophie de Développement
- **Convivial** - Conçu pour les utilisateurs non techniques
- **Sécurisé par Défaut** - Confidentialité et sécurité intégrées
- **Multi-Plateforme** - Fonctionne partout où Python fonctionne
- **Extensible** - Facile d'ajouter de nouvelles fonctionnalités et capacités

---

## 🎉 Merci !

Merci d'utiliser Emailer Simple Tool ! Nous espérons qu'il rend vos campagnes email plus efficaces et agréables à créer.

**Bon Emailing !** 📧

---

*Emailer Simple Tool - Rendre les campagnes d'emails personnalisés simples et accessibles.*
