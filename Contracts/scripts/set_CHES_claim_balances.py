from brownie import network, config, ChainEstateTokenClaim
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from pathlib import Path
from web3 import Web3
import math
import csv

CHAIN_ESTATE_TOKEN_CLAIM_ADDRESS_TEST = "0x7975F710Fb0Ba0C0f680c50767e1071F38D5997b"
CHAIN_ESTATE_TOKEN_CLAIM_ADDRESS = "0x074d07B5c9F0388D306Cfe00786C94fCA35166e4"
PROD = True
SET_BALANCES = True

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
                    if Web3.toWei(holder[1], "ether") > Web3.toWei("1", "ether"):
                        balances.append(Web3.toWei(holder[1], "ether") - Web3.toWei("1", "ether"))
                    else:
                        balances.append(Web3.toWei(holder[1], "ether"))
                except:
                    print(f"Skipping: {holder[0]}, balance: {holder[1]}")

    assert len(accounts) == len(balances)
    print(f"Number of holders: {len(accounts)}")
    
    if SET_BALANCES:
        splitNum = 10
        for i in range(splitNum):
            lowerLimit = int(math.floor((len(accounts) / splitNum)) * i)
            upperLimit = int(math.ceil((len(accounts) / splitNum)) * (i + 1))
            print(f"index is: {i}, lower limit is: {lowerLimit}, upper limit is: {upperLimit}")
            chainEstateTokenClaim.setupTokenBalances(accounts[lowerLimit:upperLimit], balances[lowerLimit:upperLimit], {"from": account})
    else:
        print(f"Sum of all account balances is: {sum(balances)}")

    print(f"Account BNB balance is currently: {account.balance()}")

def main():
    set_CHES_claim_balances()