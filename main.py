import dotenv
import os
from utils import secrets

if not os.environ["PRODUCTION"]:
    print("Loading dotenv...")
    dotenv.load_dotenv()

if os.environ["AWS"]:
    try:
        aws_envs = secrets.get_secret()
        if not aws_envs:
            print("Secrets not found!")
            exit()
        os.environ["ADMIN_WALLET_PUBLIC_KEY"] = aws_envs["ADMIN_WALLET_PUBLIC_KEY"]
        os.environ["ADMIN_WALLET_PRIVATE_KEY"] = aws_envs["ADMIN_WALLET_PRIVATE_KEY"]
        print("AWS Secrets configured!")
    except Exception as e:
        print("ERROR: ", e)

from celery_app import app
from datetime import timedelta
from sync_service_new import sync_db_and_tasks
from utils import redbeat_helper
import time
import json


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    preform_sync.delay()
    sender.add_periodic_task(timedelta(seconds=120), preform_sync.s(), name="sync_service")
    sender.add_periodic_task(timedelta(seconds=180), daily_draw_disbursal.s(), name="daily_draw_disbursal_service")

@app.task
def preform_sync():
    return sync_db_and_tasks()

@app.task(autoretry_for=(Exception,), retry_backoff=3, retry_kwargs={'max_retries': 5})
def test_contract(contract_address, abi, frequency_in_sec, task_name):
    try:
        from web3 import Web3
        from web3.middleware import geth_poa_middleware
        WEB3_PROVIDER_URL = os.environ["WEB3_PROVIDER_URL"]

        web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        caller = os.environ["ADMIN_WALLET_PUBLIC_KEY"]
        private_key = os.environ["ADMIN_WALLET_PRIVATE_KEY"]  # To sign the transaction

        # Initialize address nonce
        nonce = web3.eth.get_transaction_count(caller)

        # Create smart contract instance
        contract = web3.eth.contract(address=contract_address, abi=json.loads(abi))

        # status = contract.functions.getRoundStatus().call()
        # print("BEFORE CALL:",status)
        # initialize the chain id, we need it to build the transaction for replay protection
        Chain_id = os.environ["CHAIN_ID"] # TODO: CHECK if can get this from DB
        # Chain_id = 11155111

        # Call your function
        call_function = contract.functions.startRound().build_transaction({"chainId": int(Chain_id), "from": caller, "nonce": nonce})

        # Sign transaction
        signed_tx = web3.eth.account.sign_transaction(call_function, private_key=private_key)

        # Send transaction
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        # Wait for transaction receipt
        tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)
        print(tx_receipt) # Optional
        status = contract.functions.getRoundStatus().call()
        print("AFTER CALL:", status)
        t = contract.functions.roundEndTime().call()
        currt = contract.functions.getCurrentBlockTimeStamp().call()
        # currt = time.time()
        print("END TIME: ", t, "CURR: ", currt, f"DIFF: {currt - time.time()}", f"LEFT: {t-currt}")
        redbeat_helper.reset_schedule_timer(name=task_name, app=app)
    except Exception as e:
        print("ERROR: ", e)
        t = contract.functions.roundEndTime().call()
        # currt = time.time()
        currt = contract.functions.getCurrentBlockTimeStamp().call()
        print("END TIME: ", t, "CURR: ", currt, f"DIFF: {currt - time.time()}", f"LEFT: {t-currt}")
        raise Exception(e)

@app.task
def daily_draw_disbursal():
    try:
        from ParticipantsMongoRepo import ParticipantsMongoRepo
        import random

        # fetch participants from last 24HRs 
        participants_repo = ParticipantsMongoRepo()

        participants = participants_repo.getParticipationsInLast24Hr()

        print(participants)

        # choose randomly
        selected = None
        if len(participants) > 0:
            selected = random.choice(participants)

            print("Selected: ", selected["_id"])

        if selected == None: 
            print("None selected")
            return

        winner =  selected["_id"]
            
        # setup instance of draw contract
        from web3 import Web3
        from web3.middleware import geth_poa_middleware
        import os
        WEB3_PROVIDER_URL = os.environ["WEB3_PROVIDER_URL"]

        web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        caller = os.environ["ADMIN_WALLET_PUBLIC_KEY"]
        private_key = os.environ["ADMIN_WALLET_PRIVATE_KEY"]  # To sign the transaction

        # Initialize address nonce
        nonce = web3.eth.get_transaction_count(caller)

        draw_contract_address = os.environ["DRAW_CONTRACT_ADDRESS"]

        with open("drawABI.json", 'r') as file:
            abi = json.load(file)

        # Create smart contract instance # TODO: setup ABI
        contract = web3.eth.contract(address=draw_contract_address, abi=abi)

        # initialize the chain id, we need it to build the transaction for replay protection
        Chain_id = os.environ["CHAIN_ID"] # TODO: CHECK if can get this from DB

        # create a txn for disbursal 
        # Call your function
        call_function = contract.functions.disburseToWinner(winner).build_transaction({"chainId": int(Chain_id), "from": caller, "nonce": nonce})

        # Sign transaction
        signed_tx = web3.eth.account.sign_transaction(call_function, private_key=private_key)

        # Send transaction
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        # Wait for transaction receipt
        tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)
        print(tx_receipt) # Optional

    # store
    except Exception as e:
        if "No funds available to disburse" in str(e):
            print("WARNING: No funds to disburse!")    
        else:
            print("ERROR: ", e)
            raise Exception(e)