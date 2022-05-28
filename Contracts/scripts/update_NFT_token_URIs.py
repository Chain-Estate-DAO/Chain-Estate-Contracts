from brownie import network, config, ChainEstateNFT
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from pathlib import Path
from web3 import Web3
import requests
import math
import json
import csv

CHAIN_ESTATE_NFT_ADDRESS_TEST = "0x2941F00c3fC86C91333219C5cE43A174F48e500f"
CHAIN_ESTATE_NFT_ADDRESS = "0x2b2c820100e2106aea2695c8421558f19aad8061"
PROD = True

tokenIds = [
    11, 24, 26, 27, 29,
    5,
    22,
    6,
    2,
    31
]
images = [
    "D:\\Chain-Estate-DAO\\NFTs\\NFT1.jpg",
    "D:\\Chain-Estate-DAO\\NFTs\\NFT1.jpg",
    "D:\\Chain-Estate-DAO\\NFTs\\NFT1.jpg",
    "D:\\Chain-Estate-DAO\\NFTs\\NFT1.jpg",
    "D:\\Chain-Estate-DAO\\NFTs\\NFT1.jpg",
    "D:\\Chain-Estate-DAO\\NFTs\\NFT2.jpg",
    "D:\\Chain-Estate-DAO\\NFTs\\NFT4.jpg",
    "D:\\Chain-Estate-DAO\\NFTs\\NFT1.jpg",
    "D:\\Chain-Estate-DAO\\NFTs\\NFT1.jpg",
    "D:\\Chain-Estate-DAO\\NFTs\\NFT8.jpg",
]

imageToURL = {}

def update_NFT_token_URIs(chainEstateNFTAddress=None, tokenIds=tokenIds, images=images):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        chainEstateNFTAddress = CHAIN_ESTATE_NFT_ADDRESS

    if not chainEstateNFTAddress:
        chainEstateNFTAddress = CHAIN_ESTATE_NFT_ADDRESS_TEST

    if len(tokenIds) != len(images):
        print("Token ID array length doesn't match the images array length.")
        return

    chainEstateNFTABI = ChainEstateNFT.abi
    chainEstateNFT = Contract.from_abi("ChainEstateNFT", chainEstateNFTAddress, chainEstateNFTABI)

    if chainEstateNFT._tokenIds() < max(tokenIds):
        print("There are token IDs in the token ID array that aren't in the NFT contract.")

    print(f"Account BNB balance is currently: {account.balance()}")

    for i in range(len(tokenIds)):
        currTokenId = tokenIds[i]
        currImage = images[i]

        currTokenURI = chainEstateNFT.tokenURI(currTokenId)
        response = requests.get(currTokenURI)
        # print(str(response.content).replace("\'", "\"")[2:-1])
        NFTTokenURI = json.loads(str(response.content).replace("\'", "\"")[2:-1])

        imageURL = ""
        if currImage in imageToURL.keys():
            imageURL = imageToURL[currImage]
        else:
            with open(currImage, "rb") as imageFile:
                files = {'file': imageFile}
                response = requests.post('https://ipfs.infura.io:5001/api/v0/add', files=files)
                imageHash = response.json()["Hash"]
                
                imageURL = f"https://ipfs.infura.io/ipfs/{imageHash}"
                imageToURL[currImage] = imageURL

        NFTTokenURI["image"] = imageURL

        files = {'file': str(NFTTokenURI).replace("\'", "\"")}
        response = requests.post('https://ipfs.infura.io:5001/api/v0/add', files=files)
        tokenURIHash = response.json()["Hash"]
        newTokenURI = f"https://ipfs.infura.io/ipfs/{tokenURIHash}"

        print(newTokenURI)

        chainEstateNFT.setTokenURI(currTokenId, newTokenURI, {"from": account})

    print(f"Account BNB balance is currently: {account.balance()}")

def main():
    update_NFT_token_URIs()