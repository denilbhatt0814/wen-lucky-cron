import dotenv
import os

if not os.environ["PRODUCTION"]:
    print("Loading dotenv...")
    dotenv.load_dotenv()

from SmartContractMongoRepo import SmartContractMongoRepo
from ParticipantsMongoRepo import ParticipantsMongoRepo
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import logging

def handle_event(event):
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
    infura_url = os.environ["WEB3_PROVIDER_URL_ALCHEMY"]

    web3 = Web3(Web3.HTTPProvider(infura_url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not web3.is_connected():
        logger.error("Web3 provider couldn't be connected")
        exit()
    else:
        logger.info("Web3 provider connected!")

    # get list of running smart contracts
    contracts = sm_repo.getAll()
    contract_instances = [web3.eth.contract(address=contract["contractAddress"], abi=json.loads(contract["abiJson"])) for contract in contracts]
    logger.debug(f"Instanciated {len(contract_instances)} contracts...")

    # add a listener onto that contract
    event_filters =[ contract.events.Deposited.create_filter(fromBlock="latest") for contract in contract_instances]
    logger.debug(f"Created {len(event_filters)} event filters...")

    # process incoming requests
    logger.info("Listening...")
    while True:
        for event_filter in event_filters:
            for event in event_filter.get_new_entries():
                handle_event(event)


if __name__ == "__main__":
    logger = logging.getLogger("participation_svc")
    logger.setLevel(logging.DEBUG)

    # Create console handler and set level to debug
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add formatter to console handler
    console_handler.setFormatter(formatter)

    # Add console handler to logger
    logger.addHandler(console_handler)

    sm_repo = SmartContractMongoRepo()
    participants_repo = ParticipantsMongoRepo()
    main()