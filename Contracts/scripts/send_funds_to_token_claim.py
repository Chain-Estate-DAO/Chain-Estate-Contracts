from brownie import network, config, ChainEstateToken
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from pathlib import Path
from web3 import Web3
import math
import csv

CHAIN_ESTATE_TOKEN_CLAIM_ADDRESS_TEST = "0x7975F710Fb0Ba0C0f680c50767e1071F38D5997b"
CHAIN_ESTATE_TOKEN_CLAIM_ADDRESS = ""
CHAIN_ESTATE_V2_TOKEN_ADDRESS_TEST = "0xaB527377C920009d92029Eb6C5a8C8c27591ad56"
CHAIN_ESTATE_V2_TOKEN_ADDRESS = ""
PROD = False

FUND_AMOUNT = Web3.toWei(400000000, "ether")

def send_funds_to_token_claim(chainEstateTokenClaimAddress=None, chainEstateV2Address=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        chainEstateTokenClaimAddress = CHAIN_ESTATE_TOKEN_CLAIM_ADDRESS
        chainEstateV2Address = CHAIN_ESTATE_V2_TOKEN_ADDRESS

    if not chainEstateTokenClaimAddress:
        chainEstateTokenClaimAddress = CHAIN_ESTATE_TOKEN_CLAIM_ADDRESS_TEST
    
    if not chainEstateV2Address:
        chainEstateV2Address = CHAIN_ESTATE_V2_TOKEN_ADDRESS_TEST

    CHESV2TokenABI = ChainEstateToken.abi
    CHESV2Token = Contract.from_abi("ChainEstateToken", chainEstateV2Address, CHESV2TokenABI)

    print(f"Account CHES balance is currently: {CHESV2Token.balanceOf(account.address)}")

    CHESV2Token.transfer(chainEstateTokenClaimAddress, FUND_AMOUNT, {"from": account})

    print(f"Account CHES balance is currently: {CHESV2Token.balanceOf(account.address)}")

def main():
    send_funds_to_token_claim()