from dotenv import load_dotenv
import os

if not os.environ["PRODUCTION"]:
    print("Loading dotenv...")
    load_dotenv()

import datetime
import logging
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from SmartContractMongoRepo import SmartContractMongoRepo
from ParticipantsMongoRepo import ParticipantsMongoRepo

def handle_event(event, logger, participants_repo):
    try:
        # on new deposit event store it to mongo db
        event_json = json.loads(Web3.to_json(event))
        logger.debug(f"EVENT JSON OBJECT: {event_json}")
        result = participants_repo.add(contract_adress=event_json["address"], wallet_address=event_json["args"]["player"], round_number=event_json["args"]["roundNumber"], amount=event_json["args"]["amount"])
        logger.debug(f"EVENT ADDED TO MONGO REPO: {result}")
        logger.info("EVENT HANDLED!")
    except Exception as e:
        logger.exception(e)

def main():
    load_dotenv()  # Load environment variables
    logger = logging.getLogger("participation_svc")
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    infura_url = os.environ["WEB3_PROVIDER_URL_ALCHEMY"]
    web3 = Web3(Web3.HTTPProvider(infura_url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not web3.is_connected():
        logger.error("Web3 provider couldn't be connected")
        exit()
    else:
        logger.info("Web3 provider connected!")

    sm_repo = SmartContractMongoRepo()
    participants_repo = ParticipantsMongoRepo()

    def fetch_contracts_and_create_filters():
        contracts = sm_repo.getAll()
        contract_instances = [web3.eth.contract(address=contract["contractAddress"], abi=json.loads(contract["abiJson"])) for contract in contracts]
        logger.debug(f"Instanciated {len(contract_instances)} contracts...")
        event_filters = [contract.events.Deposited.create_filter(fromBlock="latest") for contract in contract_instances]
        logger.debug(f"Created {len(event_filters)} event filters...")
        return event_filters

    event_filters = fetch_contracts_and_create_filters()
    last_fetch_time = datetime.datetime.now()

    logger.info("Listening...")
    while True:
        current_time = datetime.datetime.now()
        # to resync with DB
        if (current_time - last_fetch_time) > datetime.timedelta(minutes=2):
            event_filters = fetch_contracts_and_create_filters()
            logger.info("Synced with DB!")
            last_fetch_time = current_time

        for event_filter in event_filters:
            for event in event_filter.get_new_entries():
                handle_event(event, logger, participants_repo)

if __name__ == "__main__":
    main()