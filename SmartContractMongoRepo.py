from utils import mongo_helper

class SmartContractMongoRepo:

    def __init__(self):
        self.db = mongo_helper.connect_to_mongo() #TODO:
        self.collection = mongo_helper.fetch_collection(self.db, "contracts")


    def getAll(self):
        return mongo_helper.fetch_all_records(self.collection)
        