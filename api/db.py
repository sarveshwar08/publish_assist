from publish_assist.settings import settings
from publish_assist.infra.db.mongo import get_mongo

mongo_db = get_mongo(settings.DATABASE_NAME)
