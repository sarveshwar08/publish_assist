from pymongo import MongoClient, database

def get_mongo(db_url: str, db_name: str) -> database.Database:
    client = MongoClient(db_url)
    
    return client[db_name]