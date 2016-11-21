User Manual
***********

Installation
============
Execute the installer (eg. LocalBoxInstaller.exe)

* Agree to the EUPL [I Agree]
* choose a different directory to install (optional) or choose the default install folder.
* Choose [Install] You can also choose [More details] for monitoring the installation.
* Possible there is a message that there is a installation of the software found: 'A prior wxPython installation was found in this directory. It is recommended that it be uninstalled first. Should I do it?' Answer: is [Yes].
* Wait for the installer starts PyCrypto-xxx ---> push or click [Next >] [Next >] [Next >] {Finish}
* Wait for the installer starts LocalboxSync-xxx start. push or click [Next >] [Next >] [Next >] {Finish}
* If all goes well there is a completed window, and you can than click [Close]
* Reboot or not (yep... it's Windows) or try to start the program, and you see in the taskbar a new localbox icon


Explaning LocalBox
==================

The LocalBox user can setup a directory on his computer to be stored securely on a remote server.
Using the same account the user can synchronize the same files with other devices / computers.
Each user has his own LocalBox directory on the server. All the files inside this directory are encrypted.
When the files are downloaded to the computer they are encrypted.
When the file are uploaded to the server they are encrypted.

.. image:: ../_diagrams/gen/current_scenario.svg


Creating your first localbox
============================

This document provides guidelines on how to test the YourLocalBox sync client.

Look in the “Start menu” for the LocalBox sync link

.. image:: ../_static/usermanual/localbox-startmenu.jpeg

It opens directly to tray,

.. image:: ../_static/usermanual/localbox-tray.jpeg

Here is the main interface

.. image:: ../_static/usermanual/localbox-main.jpeg

Get started using the “Add” button

.. image:: ../_static/usermanual/localbox-add-new.jpeg

Description of the inputs:
* Label: An identifier for of the sync / localbox. **Don’t use special characters in it**.
* URL: address of the YourLocalBox backend server. Just type: https://box.yourlocalbox.org
* Path: path to the directory on your computer whose contents will be uploaded and synced to the remote server. Use the “Select” button to choose one.

On the next step, you’ll be asked for your credentials. For a new account send an e-mail to: wilson.santos@penguinformula.com

.. image:: ../_static/usermanual/localbox-username-password.jpeg

As a final step you must provide a passphrase. This will be used to encrypt / decrypt your files.  The security of the files depends on the complexity of this passphrase.

.. image:: ../_static/usermanual/localbox-new-passphrase.jpeg

That’s it! Now it’s time to add a file to your localbox.

.. image:: ../_static/usermanual/localbox-new-file.jpeg

By default the syncing progress only runs once an hour so feel free to use the “Force sync” option on the tray icon.

.. image:: ../_static/usermanual/localbox-force-sync.jpeg

and… we are done! The files are up in the serve
