"""
Database implementation class
"""
from logging import getLogger
from os.path import exists
try:
    from ConfigParser import NoSectionError
except ImportError:
    from configparser import NoSectionError  # pylint: disable=F0401

try:
    from MySQLdb import connect as mysql_connect
    from MySQLdb import Error as MySQLError
except ImportError:
    mysql_connect = None

from sqlite3 import connect as sqlite_connect


from .config import ConfigSingleton


def database_execute(command, params=None):
    """
    Function to execute a sql statement on the database. Executes the right
    backend and makes sure '?' is replaced for the local substitution variable
    if needed.
    @param command the sql command to execute
    @param params a list of tuple of values to substitute in command
    @returns a list of dictionaries representing the sql result
    """
    getLogger("database").debug("database_execute(" + command + ", " +
                                str(params) + ")", extra={'ip': '127.0.0.1', 'name': 'database'})
    parser = ConfigSingleton()
    dbtype = parser.get('database', 'type')

    if dbtype == "mysql":
        if mysql_execute is None:
            exit("Trying to use a MySQL database without python-MySQL module.")
        command = command.replace('?', '%s')
        return mysql_execute(command, params)

    elif (dbtype == "sqlite3") or (dbtype == "sqlite"):
        return sqlite_execute(command, params)
    else:
        print("Unknown database type, cannot continue")


def sqlite_execute(command, params=None):
    """
    Function to execute a sql statement on the mysql database. This function is
    called by the database_execute function when the sqlite backend is set in
    the configuration file
    @param command the sql command to execute
    @param params a list of tuple of values to substitute in command
    @returns a list of dictionaries representing the sql result
    """
    # NOTE mostly copypasta'd from mysql_execute, may be a better way
    getLogger("database").debug("sqlite_execute(" + command + ", " +
                                str(params) + ")", extra={'ip': '127.0.0.1', 'name': 'database'})
    try:
        parser = ConfigSingleton()
        filename = parser.get('database', 'filename')
        init_db = not exists(filename)
        connection = sqlite_connect(filename)
        cursor = connection.cursor()
        if init_db:
            for sql in open('database.sql').read().split("\n"):
                if sql != "" and sql is not None:
                    cursor.execute(sql)
                    connection.commit()
        if params:
            cursor.execute(command, params)
        else:
            cursor.execute(command)
        connection.commit()
        return cursor.fetchall()
    except MySQLError as mysqlerror:
        print("MySQL Error: %d: %s" % (mysqlerror.args[0], mysqlerror.args[1]))
    except NoSectionError:
        print("Please configure the database")
    finally:
        try:
            if connection:
                connection.close()
        except UnboundLocalError:
            pass


def mysql_execute(command, params=None):
    """
    Function to execute a sql statement on the mysql database. This function is
    called by the database_execute function when the mysql backend is set in
    the configuration file.
    @param command the sql command to execute
    @param params a list of tuple of values to substitute in command
    @returns a list of dictionaries representing the sql result
    """
    getLogger("database").debug("mysql_execute(" + command + ", " + str(params)
                                + ")", extra={'ip': '127.0.0.1', 'name': 'database'})
    parser = ConfigSingleton()
    try:
        host = parser.get('database', 'hostname')
        user = parser.get('database', 'username')
        pawd = parser.get('database', 'password')
        dbse = parser.get('database', 'database')
        port = parser.getint('database', 'port')
        connection = mysql_connect(host=host, port=port, user=user,
                                   passwd=pawd, db=dbse)
        cursor = connection.cursor()
        cursor.execute(command, params)
        connection.commit()
        return cursor.fetchall()
    except MySQLError as mysqlerror:
        print("MySQL Error: %d: %s" % (mysqlerror.args[0], mysqlerror.args[1]))
    finally:
        try:
            if connection:
                connection.close()
        except UnboundLocalError:
            pass


def get_key_and_iv(localbox_path, user):
    """
    Fetches RSA encrypted key and IV from the database
    @param localbox_path (localbox specific) path to the encrypted file
    @param user name of whoes key to fetch
    @return a tuple containing the key and iv for a certain file.
    """
    sql = "select key, iv from keys where path = ? and user = ?"
    result = database_execute(sql, (localbox_path, user))[0]
    return result
