import json
import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.models.requests.account_info import AccountInfo
from xrpl.core import addresscodec

# Define the network client
JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
CLIENT = JsonRpcClient(JSON_RPC_URL)


def get_account_info(address: str):
    # Look up info about your account
    acct_info = AccountInfo(
        account=address,
        ledger_index="validated",
        strict=True,
    )
    response = CLIENT.request(acct_info)
    result = response.result
    print("response.status: ", response.status)
    print(json.dumps(response.result, indent=4, sort_keys=True))


def get_xaddress(account: str):
    # Derive an x-address from the classic address:
    # https://xrpaddress.info/
    test_xaddress = addresscodec.classic_address_to_xaddress(account, tag=12345, is_test_network=True)
    print(f"Classic address: {account}")
    print(f"X-address: {test_xaddress}")


def generate_wallet():
    # Create a wallet using the testnet faucet:
    # https://xrpl.org/xrp-testnet-faucet.html
    return generate_faucet_wallet(CLIENT, debug=True)


account_a = generate_wallet()
get_account_info(account_a.classic_address)
account_b = generate_wallet()
get_account_info(account_b.classic_address)

my_payment = xrpl.models.transactions.Payment(
    account=account_a.classic_address,
    amount=xrpl.utils.xrp_to_drops(13),
    destination=account_b.classic_address
)

signed_tx = xrpl.transaction.safe_sign_and_autofill_transaction(
        my_payment, account_a, CLIENT)
max_ledger = signed_tx.last_ledger_sequence
tx_id = signed_tx.get_hash()
print("Signed transaction:", signed_tx)
print("Transaction cost:", xrpl.utils.drops_to_xrp(signed_tx.fee), "XRP")
print("Transaction expires after ledger:", max_ledger)
print("Identifying hash:", tx_id)

# Submit transaction -----------------------------------------------------------
try:
    tx_response = xrpl.transaction.send_reliable_submission(signed_tx, CLIENT)
except xrpl.transaction.XRPLReliableSubmissionException as e:
    exit(f"Submit failed: {e}")

# Wait for validation ----------------------------------------------------------
# send_reliable_submission() handles this automatically, but it can take 4-7s.

print(json.dumps(tx_response.result, indent=4, sort_keys=True))
print(f"Explorer link: https://testnet.xrpl.org/transactions/{tx_id}")
metadata = tx_response.result.get("meta", {})
if metadata.get("TransactionResult"):
    print("Result code:", metadata["TransactionResult"])
if metadata.get("delivered_amount"):
    print("XRP delivered:", xrpl.utils.drops_to_xrp(
                metadata["delivered_amount"]))


print("------after transaction------")

get_account_info(account_a.classic_address)
get_account_info(account_b.classic_address)

