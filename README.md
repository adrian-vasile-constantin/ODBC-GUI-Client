# ODBC GUI Client
GUI client application for ODBC databases (built using Qt and python).

ODBC or [Open Database Connectivity](https://en.wikipedia.org/wiki/Open_Database_Connectivity) is an open standard that allows programs to access any kind of data source (database) that supports ODBC. Since 1995 this is a part of the SQL standard, called SQL/CLI ([Call Level Interface](https://en.wikipedia.org/wiki/Call_Level_Interface)).

Use this tool to connect to a database or a data source, using an ODBC connection string or an ODBC data source name (DSN), and to test and run any SQL statements (queries) supported by the data source. You can use SQL queries to search for records of interest in a table, or use other SQL statements to create and modify records and tables (populate the database) if you need to.

Some aditional features like list of existing functions, tables and views are also made available if provided by the data source.

If you have the connection details (like a database name, server name, username, etc) you can build a connection string with these details, according to the documentation of the ODBC driver provided by the database. The resulting connection string can be saved with a simple name (as a data source name DSN) and used for reconnecting the same way later. Usually you should avoid writing the username and password inline in the connection string. Instead, you should use the dedicated username and password fields (see image bellow, these fields use the keyring to save the sensitive information).

All major databases (commercial and open-source) publish an ODBC driver for their product. Microsoft for example makes available ODBC drivers for reading Excel spreadsheets or Access databases,
(included with Office), SQL Server databases, even the old FoxPro had a driver, but you should have the specific product installed first.

You should install the ODBC driver that matches your data source or database, or the driver provided by your database product / vendor.

Client-server databases also let you install the ODBC driver (as a client only) without installing the main product (the database server). In this case you can use the
driver to connect to a remote server, by specifying the server in the connection string.

## Installation
On Windows you should download and install [python](https://www.python.org/downloads/) (python is free, you should choose the latest version), then install the python modules PySide6, Traits, pyodbc, keyring and crc with commands like:
```sh
python -m pip install PySide6 Traits pyodbc keyring crc
```
You may want to check the option to add python to the PATH environment variable, during installation of python. `pip` command (`python -m pip`) often recommends setting up a virtual environment for the above installation, but I always found it easier to use the direct installation, and running the `pip` command above as Administrator for this purpose.

On Linux systems (not implemented) using the packages provided by Linux is preferred over the python `pip` packages. For example if your Linux distribution uses rpms:
```sh
dnf install python3-pyside6 python3-Traits python3-pyodbc
```
if your distribution does not have one of the packages (like python3-pyside6), you can still use the `pip` command above to install it.

To start the application you should run the `odbc-client.py` script.

On Windows if python launcher is installed, or python is on PATH and is configured to run .py scripts, you can just say:
```cmd
odbc-client
```
from the project directory, or if that does not work use:
```cmd
python odbc-client.py
```
also from the main project directory.

To run a SQL query like a SELECT in the editor, you should select the text of the query and press Ctrl + Enter.

## Screenshots
### Connection dialog
!["Explicit connection string for MS SQL Server Express edition"](screenshots/ConnectionDialog1.png "Save connection string as DSN")
### Connection dialog
!["Connect to existing DSN for MS SQL Server Express edition"](screenshots/ConnectionDialog2.png "Connect to DSN")
### Query window
!["See database objects in a tree and run simple query on the MS SQL Server connection"](screenshots/QueryWindow.png "See database tables and run new queries")
In this example on the left side we can see a tree with available tables in the database, and available SQL procedures / functions and views.

## Sample application only
This application is only meant for learning and practicing Qt and python bindings, so it is not a full-blown database client with all possible features (though I wish it could be).
