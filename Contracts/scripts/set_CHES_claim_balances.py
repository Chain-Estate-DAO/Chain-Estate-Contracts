from brownie import network, config, ChainEstateTokenClaim
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from pathlib import Path
from web3 import Web3
import math
import csv

CHAIN_ESTATE_TOKEN_CLAIM_ADDRESS_TEST = "0x42b3be0E4769D5715b7D5a8D8D765C2E9D2aeD9D"
CHAIN_ESTATE_TOKEN_CLAIM_ADDRESS = "0x31832D10f68D3112d847Bd924331F3d182d268C4"
PROD = False

def set_CHES_claim_balances(chainEstateTokenClaimAddress=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        chainEstateTokenClaimAddress = CHAIN_ESTATE_TOKEN_CLAIM_ADDRESS

    if not chainEstateTokenClaimAddress:
        chainEstateTokenClaimAddress = CHAIN_ESTATE_TOKEN_CLAIM_ADDRESS_TEST

    chainEstateTokenClaimABI = ChainEstateTokenClaim.abi
    chainEstateTokenClaim = Contract.from_abi("ChainEstateTokenClaim", chainEstateTokenClaimAddress, chainEstateTokenClaimABI)

    print(f"Account BNB balance is currently: {account.balance()}")

    accounts = []
    balances = []

    filePath = Path(__file__).parent.parent
    with open(f'{filePath}/holder-data/CHESHolders.csv', 'r') as holderDataFile:
        holderData = csv.reader(holderDataFile, delimiter=',')

        for holder in holderData:
            if holder[0] != "HolderAddress":
                try:
                    accounts.append(holder[0])
                    balances.append(Web3.toWei(holder[1], "ether"))
                except:
                    print(f"Skipping: {holder[0]}, balance: {holder[1]}")

    assert len(accounts) == len(balances)
    print(f"Number of holders: {len(accounts)}")
    
    splitNum = 10
    for i in range(splitNum):
        lowerLimit = int(math.floor((len(accounts) / splitNum)) * i)
        upperLimit = int(math.ceil((len(accounts) / splitNum)) * (i + 1))
        print(f"index is: {i}, lower limit is: {lowerLimit}, upper limit is: {upperLimit}")
        chainEstateTokenClaim.setupTokenBalances(accounts[lowerLimit:upperLimit], balances[lowerLimit:upperLimit], {"from": account})

    print(f"Account BNB balance is currently: {account.balance()}")

def main():
    set_CHES_claim_balances()