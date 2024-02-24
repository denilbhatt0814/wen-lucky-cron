from utils import mongo_helper
from datetime import datetime, timedelta

class ParticipantsMongoRepo:

    def __init__(self):
        self.db = mongo_helper.connect_to_mongo() #TODO:
        self.collection = mongo_helper.fetch_collection(self.db, "participants")

    def getAll(self):
        return mongo_helper.fetch_all_records(self.collection)
        
    def add(self, contract_adress, wallet_address, round_number, amount):
        result = self.collection.insert_one({"contract_address": contract_adress, "wallet_address":wallet_address, "round_number": round_number, "amount": amount,"createdAt": datetime.utcnow()})
        return result

    def getParticipationsInLast24Hr(self):
        twenty_four_hrs_ago = datetime.utcnow() - timedelta(hours=24)
        result = self.collection.aggregate([
            {
                '$match': {
                    'createdAt': {
                        '$gte': twenty_four_hrs_ago
                    }
                }
            }, {
                '$group': {
                    '_id': '$wallet_address', 
                    'count': {
                        '$sum': 1
                    }
                }
            }])
        return list(result)