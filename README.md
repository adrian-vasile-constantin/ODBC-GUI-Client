# ODBC Client
Windows GUI client application for ODBC databases (using Qt and python)

Conect to a database or a data source using an ODBC connection string or an ODBC data source name (DSN), and test and run any SQL queries supported by the data source.

Some aditional features like list of existing functions, tables and views are also available (some drivers return an empty list if the product does not support views for example).

If you have the connection details like a database name, server hostname, username, etc, you can build a connection string according to the documentation of the ODBC driver provided by the database. The resulting connection string can be saved as a data source name (DSN) for reconnecting later with the same connection information.

All major databases publish an ODBC driver for their product. Microsoft for example makes available ODBC drivers for reading Excel spreadsheets or Access databases,
(included with Office), SQL Server databases, even the old FoxPro had a driver, but you should have the specific product installed first.

Client-server databases let you install the ODBC driver (as a client only) without installing the main product (the database server). In this case you can use the
driver to connect to a remote server, by specifying the server hostname in the connection string.

## Instalation
On Windows you should install [python](https://www.python.org/downloads/), then install PySide6, Traits, pyodbc, keyring and crc with commands like
```sh
pip install PySide6 Traits pyodbc keyring crc
```
For the `pip` command above to be available, you must check the option to install it during installation of python, and you should also check the option to add python to the PATH environment variable. `pip` command often recommends setting up a virtual environment for the above installation, but I always found it easier to use the direct installation, and running the `pip` command as Administrator for this purpose.

On Linux systems (not implemented) using the distribution packages is preferred over the python `pip` packages. For example if your distribution uses rpms:
```sh
dnf install python3-pyside6 python3-Traits python3-pyodbc
```
if your distribution does not have a package (like python3-pyside6), you can still use the `pip` command above to install it.

To start the application you should run the odbc-client.py script. On Windows if python is on PATH and is configured to run .py scripts, you can just say
```cmd
odbc-client
```
from the project directory, or if that does not work use:
```cmd
python odbc-client.py
```
also from the main project directory.

To run a query like a SELECT in the editor, you should select the entire text of the query and press Ctrl + Enter.

## Screenshots
### Connection dialog
!["Explicit connection string for MS SQL Server Express edition"](screenshots/ConnectionDialog1.png "Save connection string as DSN")
### Connection dialog
!["Connect to existing DSN for MS SQL Server Express edition"](screenshots/ConnectionDialog2.png "Connect to DSN")
### Query window
!["See database objects in a tree and run simple query on the MS SQL Server connection"](screenshots/QueryWindow.png "See database tables and run new queries")

## Sample application only
This application is only meant for learning and parcticing Qt and python bindings, so it is not a full-blown database client with all possible features ('though I wish it could be).
