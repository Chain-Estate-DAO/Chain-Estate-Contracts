from brownie import network, ChainEstateToken, ChainEstateAirDrop, ChainEstatePolling
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from web3 import Web3

INITIAL_SUPPLY = Web3.toWei(1000000000, "ether")

def deploy_chain_estate(realEstateWalletAddress=None, liquidityWalletAddress=None, marketingWalletAddress=None, developerWalletAddress=None, burnWalletAddress=None):
    account = retrieve_account()

    if not realEstateWalletAddress:
        realEstateWalletAddress = account.address
    if not liquidityWalletAddress:
        liquidityWalletAddress = account.address
    if not marketingWalletAddress:
        marketingWalletAddress = account.address
    if not developerWalletAddress:
        developerWalletAddress = account.address
    if not burnWalletAddress:
        burnWalletAddress = account.address

    publishSource = network.show_active() not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    chainEstateAirDrop = ChainEstateAirDrop.deploy({"from": account}, publish_source=publishSource)
    chainEstateToken = ChainEstateToken.deploy(
        INITIAL_SUPPLY,
        chainEstateAirDrop.address,
        burnWalletAddress,
        realEstateWalletAddress,
        liquidityWalletAddress,
        marketingWalletAddress,
        developerWalletAddress,
        {"from": account},
        publish_source=publishSource
    )
    print(f"Chain Estate Token deployed to {chainEstateToken.address}")

    chainEstatePolling = ChainEstatePolling.deploy(chainEstateToken.address, {"from": account}, publish_source=publishSource)
    transaction = chainEstateAirDrop.setToken(chainEstateToken.address, {"from": account})
    transaction.wait(1)
    print("Successfully set the CHES token for the air drop.")

    return chainEstateToken, chainEstateAirDrop, chainEstatePolling

def main():
    deploy_chain_estate()