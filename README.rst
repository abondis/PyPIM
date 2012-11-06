README
======

* imap webmail
* imap calendar ?
* imap contacts ?

Installation
------------

* pull project

.. code-block:: bash

  git clone git@github.com:abondis/PyPIM.git
  cd PyPIM

* get virtualenv

.. code-block:: bash

  apt-get install python-virtualenv

* setup virtualenv

.. code-block:: bash

  virtualenv env
  . env/bin/activate

* install requirements

.. code-block:: bash

  pip install -r requirements.txt

* get bodystructure's module

.. code-block:: bash

  wget https://raw.github.com/bpeterso2000/IMAP-Tools/master/bodystructure.py

* start the project

.. code-block:: bash

  python webmail.py
