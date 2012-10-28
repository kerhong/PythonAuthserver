class TCAuthSettings:
    LISTEN_IP="0.0.0.0"
    LISTEN_PORT=3724
    LISTEN_BACKLOG=50
    DB_CONNECTIONS=5
    DB_USER="database_user"
    DB_HOST="databse_host"
    DB_PASSWORD="database_password"
    DB_DATABASE="database_database"
    ALLOWED_BUILDS=[8606,12340]
    REALMLIST_UPDATE_DELAY=10

def Log(text):
    print text
    # save to log file
    
def Debug(text):
    print text
