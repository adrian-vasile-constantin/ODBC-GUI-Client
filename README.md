# odbc-client-app
GUI client application for ODBC databases (using Qt and python)

Conect to a database or a data source using an ODBC connection string or an ODBC data source name (DSN), and test and run any SQL queries supported by the data source.

Some aditional features like list of existing functions, tables and views are also available (some drivers return an empty list if the product does not support views for example).

If you have the connection details like a database name, server hostname, username, etc, you can build a connection string according to the documentation of your database
ODBC driver. The resulting connection string can be saved as a data source name (DSN) for reconnecting later with the same connection information.

All major databases publish an ODBC driver for their product. Microsoft for example makes available ODBC drivers for reading Excel spreadsheets or Access databases,
(included with Office), SQL Server databases, even the old FoxPro had a driver, but you should have the specific product installed first.

Client-server databases let you install the ODBC driver (as a client only) without installing the main product (the database server). In this case you can use the
driver to connect to a remote server, by specifying the server hostname in the connection string.

## Instalation
You should install [python](https://www.python.org/downloads/), then install PySide6, Traits and pyodbc with commands like
```sh
pip install PySide6
pip install Traits
pip install pyodbc
```

To start the application you should run the odbc-client.py script. On Windows if python is on PATH and is configured to run .py scripts, you can just say
```cmd
odbc-client
```
from the project directory, or if that does not work use:
```cmd
python odbc-client.py
```
from the main project directory.

## Sample application only
This application is only meant for learning and parcticing Qt and python bindings, so it is not a full-blown database client with all possible features.
