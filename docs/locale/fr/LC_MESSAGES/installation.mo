��    3      �              L  �   M     �  1        7  
   <     G  H   S  -   �  &   �     �               *  i   3  0   �  
   �  )   �       >        O  Q   U  P   �     �  i   �  �   f  D   �  T   C  	   �  �   �     2	  	   ;	  9   E	  %   	     �	  n   �	  Q   ,
  S   ~
  ]   �
  =   0     n     �  D   �  <   �  w        �  u   �     "  9   9  $   s     �  T  �  �        �  2   �     �            P     9   n  1   �     �     �            z   &  :   �  
   �  1   �  
     R   $     w  R   }  V   �     '  l   +  �   �  O   F  V   �  	   �  �   �     �  	   �  N   �  1   	  "   ;  t   ^  T   �  V   (  b     [   �     >     \  j   s  [   �  �   :     �  |   �     j  @   �  )   �     �   At the project root directory, the ``scripts`` directory provides bash script wrappers to execute these commands. Thus, you could create cron rules similar to something like:: Backend Behind the scenes, it runs several *testenv* for: Demo Deployment Development For example, create a file in ``/etc/cron.d/clonescheduled``, and edit:: Further notes about some additional settings: Install dependencies (in virtualenv):: Install dependencies:: Installation Internationalization Manually Only *French* internationalisation/translations are supported for now. But any contributions are welcome! PostgreSQL **only** (no MySQL or SQLite support) Production Python >= 3.4 (no backward compatibility) Requirements Set up cron tasks on server to execute the following commands: Tests The deployment is the same as any other Django projects. Here is a quick summary: To have a quick look, you could generate some data with the following commands:: Tox WSGI will use the ``production.py`` settings, whereas ``manage.py`` will use the ``local.py`` by default. Whichever method is used, you must create a setting file for testing. Copy ``mymoney/settings/test.dist`` to ``mymoney/settings/test.py`` and edit it:: You can also clear any data relatives to the project's models with:: You can use `Tox`_. At the project root directory without virtualenv, just execute:: `Sphinx`_ ``USE_L10N_DIST``: Whether to use the minify file including translations. It imply that the translated file is generated by the MyMoney client. `isort`_ `pylama`_ cleanup tasks (only usefull with further user accounts):: cloning recurring bank transactions:: collect statics files:: configure the settings (see :ref:`installation-backend-production` or :ref:`installation-backend-development`) copy ``mymoney/settings/l10n.dist`` to ``mymoney/settings/l10n.py`` and edit it:: copy ``mymoney/settings/local.dist`` to ``mymoney/settings/local.py`` and edit it:: copy ``mymoney/settings/production.dist`` to ``mymoney/settings/production.py`` and edit it:: create a PostgreSQL database in a cluster with role and owner create a super user:: create a virtualenv:: edit your final setting file to use the l10n configuration instead:: execute the Django check command and apply fixes if needed:: export the ``DJANGO_SETTINGS_MODULE`` to easily use the ``manage.py`` with the proper production setting. For example:: import the SQL schema:: install dependencies with pip (see :ref:`installation-backend-production` or :ref:`installation-backend-development`) install dependencies:: install required system packages. For example on Debian:: test suites with coverage and report then execute tests:: Project-Id-Version: MyMoney 1.0
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2016-02-26 16:40+0100
PO-Revision-Date: 2016-02-26 16:42+0100
Last-Translator: 
Language: fr
Language-Team: 
Plural-Forms: nplurals=2; plural=(n > 1)
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.2.0
 À la racine du projet, le répertoire ``scripts`` fourni des scripts bash pour exécuter ces commandes. Par conséquent, vous pouvez les utiliser en créant des règles cron similaire à:: Serveur En coulisses, plusieurs *testenv* sont exécutés: Démo Déploiement Développement Par exemple, créez un fichier à ``/etc/cron.d/clonescheduled``, puis éditez:: Plusieurs remarques sur les paramètres supplémentaires: Installer les dépendances (dans un virtualenv):: Installer les dépendances:: Installation Internationalisation Manuellement Les traductions en *français* sont uniquement supportées pour le moment. Mais toutes contributions sont les bienvenues ! PostgreSQL **uniquement** (pas de support MySQL ou SQLite) Production Python >= 3.4 (pas de compabitilité descendante) Prérequis Configurer des tâches cron sur le serveur pour exécuter les commandes suivantes: Tests Le déploiement est similaire à d'autres projets Django. Voici un bref résumé : Pour un aperçu rapide, vous pouvez générer des données avec la commande suivante:: Tox WSGI utilisera les paramètres ``production.py`` alors que ``manage.py`` utilisera ``local.py`` par défaut. Qu'importe la méthode utilisée, vous devez créer un fichier de configuration de test. Copiez ``mymoney/settings/test.dist`` à ``mymoney/settings/test.py`` et éditez le. Vous pouvez aussi nettoyer les données relatives aux modèles du projet avec:: Vous pouvez utiliser `Tox`_. À la racine du projet sans virtualenv, exécutez juste:: `Sphinx`_ ``USE_L10N_DIST``: Faut-il utiliser ou non le fichier minifié qui inclut les traductions. Cela implique que le fichier de traduction a été généré avec le client MyMoney. `isort`_ `pylama`_ tâches de nettoyages (utile uniquement avec plusieurs comptes utilisateurs):: dupliquer les transactions bancaires récurrentes collecter les fichiers statiques:: configurer les paramètres ( voir :ref:`installation-backend-production` ou :ref:`installation-backend-development`) copiez ``mymoney/settings/l10n.dist`` à ``mymoney/settings/l10n.py`` et éditez le. copiez ``mymoney/settings/local.dist`` à ``mymoney/settings/local.py`` et éditez le. copier ``mymoney/settings/production.dist`` en ``mymoney/settings/production.py`` puis l'éditer:: créer un cluster de base de données pour PostgreSQL ainsi qu'un rôle et un propriétaire créer un super utilisateur:: créer un virtualenv:: éditez votre fichier de configuration finale pour utiliser le fichier de configuration l10n à la place:: exécuter la commande de vérification de Django puis appliquer des corrections si besoin:: exporter la variable d'environnement ``DJANGO_SETTINGS_MODULE`` pour facilement utiliser ``manage.py`` avec les paramètres de production. Par exemple:: importer le schéma SQL:: installer les dépendances avec pip (voir :ref:`installation-backend-production` ou :ref:`installation-backend-development`) installer les dépendances:: installer les paquets systèmes requis. Par exemple sur Debian:: suite de tests avec couverture et rapport puis exécutez les tests:: 