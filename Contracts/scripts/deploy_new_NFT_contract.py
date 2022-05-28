from brownie import network, config, ChainEstateNFT, ChainEstateNFTV1, ChainEstateMarketplace
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from web3 import Web3

OLD_NFT_ADDRESS_TEST = "0x2941F00c3fC86C91333219C5cE43A174F48e500f"
OLD_NFT_ADDRESS = "0x9C743B164f3C5BE29a3655578aeDd4C9a93E9E1c"
MARKETPLACE_ADDRESS_TEST = "0x10Fe48F39F57dbF87B415ADf1Fa559FadAdaE031"
MARKETPLACE_ADDRESS = "0xD5e8144757C1c0DfC8B2249cdA58277FA3d1d06d"
PROD = True

def deploy_new_NFT_contract(oldNFTAddress=None, marketplaceAddress=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        oldNFTAddress = OLD_NFT_ADDRESS
    elif not oldNFTAddress:
        oldNFTAddress = OLD_NFT_ADDRESS_TEST

    if PROD:
        marketplaceAddress = MARKETPLACE_ADDRESS
    elif not marketplaceAddress:
        marketplaceAddress = MARKETPLACE_ADDRESS_TEST

    publishSource = currNetwork not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    chainEstateNFT = ChainEstateNFT.deploy(marketplaceAddress, oldNFTAddress, {"from": account}, publish_source=publishSource)
    print(f"Chain Estate NFT deployed to {chainEstateNFT.address}")

    NFTV1ABI = ChainEstateNFTV1.abi
    NFTV1 = Contract.from_abi("ChainEstateNFT", oldNFTAddress, NFTV1ABI)

    for id in range(1, NFTV1._tokenIds() + 1):
        chainEstateNFT.transferFrom(account.address, NFTV1.ownerOf(id), id, {"from": account})

    print("Finished sending NFTs to old owners.")

    marketplaceABI = ChainEstateMarketplace.abi
    marketplaceContract = Contract.from_abi("ChainEstateMarketplace", marketplaceAddress, marketplaceABI)

    transaction = marketplaceContract.setChainEstateNFT(chainEstateNFT.address, {"from": account})
    transaction.wait(1)
    print("Successfully set the CHES NFT reference for the marketplace.")

    return chainEstateNFT

def main():
    deploy_new_NFT_contract()