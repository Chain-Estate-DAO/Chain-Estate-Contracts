from brownie import network, config, ChainEstateToken, ChainEstateTokenClaim
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from web3 import Web3

CHAIN_ESTATE_TOKEN_ADDRESS_V1_TEST = "0x42b3be0E4769D5715b7D5a8D8D765C2E9D2aeD9D"
CHAIN_ESTATE_TOKEN_ADDRESS_V2_TEST = "0x42b3be0E4769D5715b7D5a8D8D765C2E9D2aeD9D"
CHAIN_ESTATE_TOKEN_ADDRESS_V1 = "0x31832D10f68D3112d847Bd924331F3d182d268C4"
CHAIN_ESTATE_TOKEN_ADDRESS_V2 = "0x31832D10f68D3112d847Bd924331F3d182d268C4"
PROD = False

def deploy_token_claim(chainEstateTokenAddressV1=None, chainEstateTokenAddressV2=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        chainEstateTokenAddressV1 = CHAIN_ESTATE_TOKEN_ADDRESS_V1
        chainEstateTokenAddressV2 = CHAIN_ESTATE_TOKEN_ADDRESS_V2

    if not chainEstateTokenAddressV1:
        chainEstateTokenAddressV1 = CHAIN_ESTATE_TOKEN_ADDRESS_V1_TEST

    if not chainEstateTokenAddressV2:
        chainEstateTokenAddressV2 = CHAIN_ESTATE_TOKEN_ADDRESS_V2_TEST

    publishSource = currNetwork not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    chainEstateTokenClaim = ChainEstateTokenClaim.deploy(chainEstateTokenAddressV1, chainEstateTokenAddressV2, {"from": account}, publish_source=publishSource)
    print(f"Chain Estate Token Claim contract deployed to {chainEstateTokenClaim.address}")

    chainEstateTokenV2ABI = ChainEstateToken.abi
    chainEstateTokenV2 = Contract.from_abi("ChainEstateToken", chainEstateTokenAddressV2, chainEstateTokenV2ABI)

    chainEstateTokenV2.excludeUserFromFees(chainEstateTokenClaim.address, {"from": account})

    return chainEstateTokenClaim

def main():
    deploy_token_claim()