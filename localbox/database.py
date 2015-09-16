"""
Database implementation class
"""
from logging import getLogger
from logging import DEBUG
from logging import StreamHandler

from os.path import exists
from ConfigParser import NoSectionError

from MySQLdb import connect as mysql_connect
from sqlite3 import connect as sqlite_connect
from MySQLdb import Error


from .config import ConfigSingleton

def database_execute(command, params=None):
    """
    Function to execute a sql statement on the database
    """
    getLogger("database").debug("database_execute(" + command + ", " + str(params) + ")")
    parser = ConfigSingleton()
    dbtype = parser.get('database', 'type')
    if dbtype == "mysql":
        command = command.replace('?', '%s')
        return mysql_execute(command, params)
    elif (dbtype == "sqlite3") or (dbtype == "sqlite"):
        return sqlite_execute(command, params)
    else:
        print "Unknown database type, cannot continue"

def sqlite_execute(command, params=None):
    """
    Function to execute a sql statement on the mysql database
    """
    #NOTE mostly copypasta'd from mysql_execute, may be a better way
    getLogger("database").debug("sqlite_execute(" + command + ", " + str(params) + ")")
    try:
        parser = ConfigSingleton()
        filename = parser.get('database', 'filename')
        init_db = not exists(filename)
        connection = sqlite_connect(filename)
        cursor = connection.cursor()
        if init_db:
            print"#iinitialising the database"
            for sql in file('database.sql').read().split("\n"):
                if sql != "" and sql != None:
                    cursor.execute(sql)
                    connection.commit()
        if params:
            cursor.execute(command, params)
        else:
            cursor.execute(command)
        connection.commit()
        return cursor.fetchall()
    except Error as mysqlerror:
        print "MySQL Error: %d: %s" % (mysqlerror.args[0], mysqlerror.args[1])
    except NoSectionError:
        print "Please configure the database"
    finally:
        try:
            if connection:
                connection.close()
        except UnboundLocalError:
            pass
 

def mysql_execute(command, params=None):
    """
    Function to execute a sql statement on the mysql database
    """
    getLogger("database").debug("mysql_execute(" + command + ", " + str(params) + ")")
    parser = ConfigSingleton()
    try:
        host = parser.get('database', 'hostname')
        user = parser.get('database', 'username')
        pawd = parser.get('database', 'password')
        dbse = parser.get('database', 'database')
        port = parser.getint('database', 'port')
        connection = mysql_connect(host=host, port=port, user=user, passwd=pawd, db=dbse)
        cursor = connection.cursor()
        cursor.execute(command, params)
        connection.commit()
        return cursor.fetchall()
    except Error as mysqlerror:
        print "MySQL Error: %d: %s" % (mysqlerror.args[0], mysqlerror.args[1])
    except NoSectionError:
        print "Please configure the database"
    finally:
        try:
            if connection:
                connection.close()
        except UnboundLocalError:
            pass
