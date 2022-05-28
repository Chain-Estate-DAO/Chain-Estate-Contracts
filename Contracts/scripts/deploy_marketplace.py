from brownie import network, config, ChainEstateNFT, ChainEstateNFTV1, ChainEstateMarketplace
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from web3 import Web3

# CHAIN_ESTATE_TOKEN_ADDRESS_RINKEBY = "0xd2cf313CdAD8F99bCdEd14120d679c15218b787A"
CHAIN_ESTATE_TOKEN_ADDRESS_TEST = "0x42b3be0E4769D5715b7D5a8D8D765C2E9D2aeD9D"
CHAIN_ESTATE_TOKEN_ADDRESS = "0x31832D10f68D3112d847Bd924331F3d182d268C4"
OLD_NFT_ADDRESS = "0x9C743B164f3C5BE29a3655578aeDd4C9a93E9E1c"
PROD = False

def deploy_chain_estate_marketplace(chainEstateTokenAddress=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        chainEstateTokenAddress = CHAIN_ESTATE_TOKEN_ADDRESS
    elif not chainEstateTokenAddress:
        chainEstateTokenAddress = CHAIN_ESTATE_TOKEN_ADDRESS_TEST

    publishSource = currNetwork not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    chainEstateMarketplace = ChainEstateMarketplace.deploy(chainEstateTokenAddress, {"from": account}, publish_source=publishSource)
    print(f"Chain Estate Marketplace deployed to {chainEstateMarketplace.address}")

    chainEstateNFTV1 = ChainEstateNFTV1.deploy(chainEstateMarketplace.address, {"from": account}, publish_source=publishSource)
    print(f"Chain Estate NFT V1 deployed to {chainEstateNFTV1.address}")

    chainEstateNFT = ChainEstateNFT.deploy(chainEstateMarketplace.address, chainEstateNFTV1.address, {"from": account}, publish_source=publishSource)
    print(f"Chain Estate NFT deployed to {chainEstateNFT.address}")

    transaction = chainEstateMarketplace.setChainEstateNFT(chainEstateNFT.address, {"from": account})
    transaction.wait(1)
    print("Successfully set the CHES NFT reference for the marketplace.")

    return chainEstateMarketplace, chainEstateNFT

def main():
    deploy_chain_estate_marketplace()