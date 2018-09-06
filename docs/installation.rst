Installation
============

Requirements
------------

* Python >= 3.4 (no backward compatibility)
* PostgreSQL **only** (no MySQL or SQLite support)

Deployment
----------

Backend
```````

The deployment is the same as any other Django projects. Here is a quick
summary:

1. install required system packages. For example on Debian::

    apt-get install python3 python3-dev postgresql libpq-dev virtualenv

2. create a PostgreSQL database in a cluster with role and owner

3. create a virtualenv::

    virtualenv <NAME> -p python3

4. install dependencies with pip (see :ref:`installation-backend-production`
   or :ref:`installation-backend-development`)

5. configure the settings (see :ref:`installation-backend-production` or
   :ref:`installation-backend-development`)

6. export the ``DJANGO_SETTINGS_MODULE`` to easily use the ``manage.py`` with
   the proper production setting. For example::

    export DJANGO_SETTINGS_MODULE="mymoney.settings.prod"

7. import the SQL schema::

    ./manage.py migrate

8. create a super user::

    ./manage.py createsuperuser
    
9. Connect to the `/admin` Web interface to create a first bank account.

.. note::
    WSGI will use the ``prod.py`` settings

.. _installation-backend-production:

Production
++++++++++

* Install dependencies (in virtualenv)::

    pip install -r requirements/prod.txt

* copy ``mymoney/settings/local.py.dist`` to
  ``mymoney/settings/local.py`` and edit it::

    cp mymoney/settings/local.py.dist mymoney/settings/local.py

* collect statics files::

    ./manage.py collectstatic

* execute the Django check command and apply fixes if needed::

    ./manage.py check --deploy

* Set up cron tasks on server to execute the following commands:

    * cloning recurring bank transactions::

        ./manage.py clonescheduled

At the project root directory, the ``scripts`` directory provides bash script
wrappers to execute these commands.
Thus, you could create cron rules similar to something like::

    0 1 * * *  ABSOLUTE_PATH/scripts/clonescheduled.sh <ABSOLUTE_PATH_TO_V_ENV>

For example, create a file in ``/etc/cron.d/clonescheduled``, and edit::

   0 2 * * * <USER> /ABSOLUTE_PATH/scripts/clonescheduled.sh <ABSOLUTE_PATH_TO_V_ENV>

.. _installation-backend-development:

Development
+++++++++++

* Install dependencies::

    pip install -r requirements/dev.txt

* copy ``mymoney/settings/local.py.dist`` to ``mymoney/settings/local.py`` and
  edit it::

    cp mymoney/settings/local.py.dist mymoney/settings/local.py

.. _installation-deployment-frontend:


Tox
```

You can use `Tox`_. At the project root directory without virtualenv, just
execute::

    tox

.. _`Tox`: http://tox.readthedocs.org

Manually
````````

1. install dependencies::

    pip install -r requirements/test.txt

2. then execute tests::

    ./manage.py test --settings=mymoney.settings.test mymoney
