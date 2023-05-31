import sqlite3


DB_NAME = "db_catalog.db"


def create_connection(db_file):
    connection = None
    try:
        connection = sqlite3.connect(db_file)
        print(sqlite3.version)
    except sqlite3.Error as err:
        print(err)
    
    return connection


def execute_query(connection, query):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(query)
    except sqlite3.Error as err:
        print(err)

    return cursor.fetchall()


def main():
    db_connection = create_connection(DB_NAME)
    
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
            device_id VARCHAR(32),
            timestamp INTEGER NOT NULL,
            PRIMARY KEY(device_id)
        );
        """,
        """
        CREATE TABLE device_end_points (
            device_id VARCHAR(32),
            end_point VARCHAR(200),
            type VARCHAR(50),
            PRIMARY KEY(device_id, end_point, type),
            FOREIGN KEY(device_id) REFERENCES devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE 
        );
        """,
        """
        CREATE TABLE device_resources (
            device_id VARCHAR(32),
            resource VARCHAR(100),
            PRIMARY KEY(device_id, resource),
            FOREIGN KEY(device_id) REFERENCES devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE 
        );
        """,
        """
        CREATE TABLE users (
            user_id VARCHAR(32),
            name VARCHAR(50) NOT NULL,
            surname VARCHAR(50) NOT NULL,
            PRIMARY KEY(user_id)
        );
        """,
        """
        CREATE TABLE user_emails (
            user_id VARCHAR(32),
            email VARCHAR(100),
            PRIMARY KEY(user_id, email),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE 
        );
        """,
        """
        CREATE TABLE services (
            service_id VARCHAR(32),
            description VARCHAR(200) NOT NULL,
            timestamp INTEGER NOT NULL,
            PRIMARY KEY(service_id)
        );
        """,
        """
        CREATE TABLE service_end_points (
            service_id VARCHAR(32),
            end_point VARCHAR(200),
            type VARCHAR(50),
            PRIMARY KEY(service_id, end_point, type),
            FOREIGN KEY(service_id) REFERENCES services(service_id) ON DELETE CASCADE ON UPDATE CASCADE 
        );
        """
    ]

    for query in queries:
        execute_query(db_connection, query)

    db_connection.close()


if __name__=='__main__':
    main()