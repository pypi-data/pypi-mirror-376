# MongoDB Configuration
import os

HOST_MONGODB = os.getenv('HOST_MONGODB', '172.20.3.37')
PORT_MONGODB = os.getenv('PORT_MONGODB', '27027')

MONGO_BATCH_SIZE = 100000
MONGO_DB_HOST = HOST_MONGODB
MONGO_DB_PORT = PORT_MONGODB
MONGO_DB_NAME = 'optidata_db'
MONGO_DB_URI = f'mongodb://{MONGO_DB_HOST}:{MONGO_DB_PORT}/{MONGO_DB_NAME}'
MONGO_DB_USER = 'admin@optimisa.cl'  # get_config_params('DB_USER')
MONGO_DB_PWD = '0pt1m1542560_2024'  # get_config_params('DB_PWD')
