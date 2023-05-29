import sqlite3


def main():
    db_name = "/SW_lab02/ex01/db_catalog.db"
    db_connection = create_connection(db_name)
    
    queries = [
        "DROP TABLE IF EXISTS devices;",
        "DROP TABLE IF EXISTS device_end_points;",
        "DROP TABLE IF EXISTS device_resources;",
        "DROP TABLE IF EXISTS users;",
        "DROP TABLE IF EXISTS user_emails;",
        "DROP TABLE IF EXISTS services; ",
        "DROP TABLE IF EXISTS service_end_points;",
        """
        CREATE TABLE devices (
            deviceId VARCHAR(32),
            timestamp INTEGER NOT NULL,
            PRIMARY KEY(deviceId)
        );
        """,
        """
        CREATE TABLE device_end_points (
            deviceId VARCHAR(32),
            ip VARCHAR(32),
            port INTEGER,
            type CHAR(4),
            topic VARCHAR(200) NULL,
            PRIMARY KEY(deviceId, ip, port, type),
            FOREIGN KEY(deviceId) REFERENCES devices(deviceId) ON DELETE CASCADE ON UPDATE CASCADE 
        );
        """,
        """
        CREATE TABLE device_resources (
            deviceId VARCHAR(32),
            resource VARCHAR(100),
            PRIMARY KEY(deviceId, resource),
            FOREIGN KEY(deviceId) REFERENCES devices(deviceId) ON DELETE CASCADE ON UPDATE CASCADE 
        );
        """,
        """
        CREATE TABLE users (
            userId VARCHAR(32),
            name VARCHAR(50) NOT NULL,
            surname VARCHAR(50) NOT NULL,
            PRIMARY KEY(userId)
        );
        """,
        """
        CREATE TABLE user_emails (
            userId VARCHAR(32),
            email VARCHAR(100),
            PRIMARY KEY(userId, email),
            FOREIGN KEY(userId) REFERENCES users(userId) ON DELETE CASCADE ON UPDATE CASCADE 
        );
        """,
        """
        CREATE TABLE services (
            serviceId VARCHAR(32),
            description VARCHAR(200) NOT NULL,
            timestamp INTEGER NOT NULL,
            PRIMARY KEY(serviceId)
        );
        """,
        """
        CREATE TABLE service_end_points (
            serviceId VARCHAR(32),
            ip VARCHAR(32),
            port INTEGER,
            type CHAR(4),
            topic VARCHAR(200) NULL,
            PRIMARY KEY(serviceId, ip, port, type),
            FOREIGN KEY(serviceId) REFERENCES services(serviceId) ON DELETE CASCADE ON UPDATE CASCADE 
        );
        """
    ]

    for query in queries:
        execute_query(db_connection, query)


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    connection = None
    try:
        connection = sqlite3.connect(db_file)
        print(sqlite3.version)
    except sqlite3.Error as err:
        print(err)
    
    return connection


def execute_query(connection, query):
    try:
        cursor = connection.cursor()
        cursor.execute(query)
    except sqlite3.Error as err:
        print(err)


if __name__=='__main__':
    main()