import logging

from bson import ObjectId

from ..database.mongo_collections import MONGO_COLLECTION_DATA_CYCLES
from ..database.mongodb import MongoAPI
from ..utility.utils import get_datetime, get_message_error

log = logging.getLogger(__name__)


def new_cycle(json: dict):
    try:
        if 'id' in json:
            data = {
                'collection': MONGO_COLLECTION_DATA_CYCLES,
                'Filter': {
                    '_id': ObjectId(json.get('id')),
                    'active': True
                },
                'DataToBeUpdated': {
                    'name_cycle': json.get('name_cycle'),
                    'start_cycle': json.get('start_cycle'),
                    'end_cycle': json.get('end_cycle'),
                    'updated_at': get_datetime(),
                }
            }
            mongodb = MongoAPI(data)
            response = mongodb.update()
        else:
            data = {
                'collection': MONGO_COLLECTION_DATA_CYCLES,
                'Document': {
                    'name_cycle': json.get('name_cycle'),
                    'start_cycle': json.get('start_cycle'),
                    'end_cycle': json.get('end_cycle'),
                    'type_cycle': json.get('type_cycle'),
                    'active': True,
                    'created_at': get_datetime(),
                },
                'Filter': {
                    'name_cycle': json.get('name_cycle'),
                    'type_cycle': json.get('type_cycle')
                }
            }
            mongodb = MongoAPI(data)
            response = mongodb.write(data)
    except Exception as e:
        log.exception(e)
        response = get_message_error(e)

    return response


def get_cycle(pid: str):
    try:
        data = {
            'collection': MONGO_COLLECTION_DATA_CYCLES,
            'Filter': {
                '_id': ObjectId(pid),
                'active': True,
            }
        }
        mongodb = MongoAPI(data)
        response = mongodb.read()
    except Exception as e:
        log.exception(e)
        response = get_message_error(e)

    return response


def update_cycle(pid: str, json):
    try:
        data = {
            'collection': MONGO_COLLECTION_DATA_CYCLES,
            'Filter': {
                '_id': ObjectId(pid)
            },
            'DataToBeUpdated': {
                'name_cycle': json.get('name_cycle'),
                'start_cycle': json.get('start_cycle'),
                'end_cycle': json.get('end_cycle'),
                'type_cycle': json.get('type_cycle'),
                'updated_at': get_datetime(),
            }
        }
        mongodb = MongoAPI(data)
        response = mongodb.update()
    except Exception as e:
        log.exception(e)
        response = get_message_error(e)

    return response


def delete_cycle(pid: str):
    try:
        data = {
            'collection': MONGO_COLLECTION_DATA_CYCLES,
            'Filter': {
                '_id': ObjectId(pid)
            }
        }
        mongodb = MongoAPI(data)
        response = mongodb.write(data)

        if response:
            data = {
                'collection': MONGO_COLLECTION_DATA_CYCLES,
                'Filter': {
                    '_id': ObjectId(pid)
                },
                'DataToBeUpdated': {
                    'active': False,
                    'updated_at': get_datetime(),
                }
            }
            mongodb = MongoAPI(data)
            response = mongodb.update()
            if response:
                response = {'Status': 'Eliminación exitosa'}

    except Exception as e:
        log.exception(e)
        response = get_message_error(e)

    return response


def get_all_cycles():
    try:
        data = {
            'collection': MONGO_COLLECTION_DATA_CYCLES,
            'Filter': {
                'active': True
            }
        }
        mongodb = MongoAPI(data)
        response = mongodb.all()
    except Exception as e:
        log.exception(e)
        response = get_message_error(e)
    return response
