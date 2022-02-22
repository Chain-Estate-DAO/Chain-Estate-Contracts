from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_chain_estate
from brownie import network, accounts, exceptions, chain
from web3 import Web3
import pytest
import time

LIQUIDITY_SUPPLY = Web3.toWei(300000000, "ether")

def test_integration():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account3, account4, account5, account5, account5)
    uniswapPair = chainEstateToken.uniswapPair()

    # if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Send CHES tokens from account3 to account
    tokensSent = 10000000000
    initialAccountBalanceBNB = account.balance()
    chainEstateToken.transfer(account.address, tokensSent, {"from": account5})

    # Transfer some of the CHES tokens to account2 when account is not included in fees.
    chainEstateToken.excludeUserFromFees(account.address, {"from": account})
    chainEstateToken.transfer(account2.address, tokensSent / 4, {"from": account})

    # Asserts that both accounts now have the correct amount of CHES tokens.
    assert chainEstateToken.balanceOf(account.address) == tokensSent * 3 / 4
    assert chainEstateToken.balanceOf(account2.address) == tokensSent / 4

    # Transfer some of the CHES tokens to account2 when account is included in fees.
    realEstateWalletAddress = chainEstateToken.realEstateWalletAddress()
    marketingWalletAddress = chainEstateToken.marketingWalletAddress()
    developerWalletAddress = chainEstateToken.developerWalletAddress()
    chainEstateTokenAddress = chainEstateToken.getContractAddress()
    realEstateInitialBalance = chainEstateToken.balanceOf(realEstateWalletAddress)
    devMarketingInitialBalance = chainEstateToken.balanceOf(marketingWalletAddress)
    account1InitialBalance = chainEstateToken.balanceOf(account.address)
    account2InitialBalance = chainEstateToken.balanceOf(account2.address)

    realEstateFee = chainEstateToken.realEstateTransactionFeePercent()
    marketingFee = chainEstateToken.marketingFeePercent()
    developerFee = chainEstateToken.developerFeePercent()

    chainEstateToken.includeUsersInFees(account.address, {"from": account})
    chainEstateToken.transfer(account2.address, tokensSent / 4, {"from": account})

    # Asserts that all accounts involved in the transaction have the correct amount of CHES tokens.
    assert chainEstateToken.balanceOf(account.address) == account1InitialBalance - tokensSent / 4
    assert chainEstateToken.balanceOf(account2.address) == account2InitialBalance + ((tokensSent / 4) * (float(100 - realEstateFee - marketingFee - developerFee) / 100))
    assert chainEstateToken.balanceOf(chainEstateTokenAddress) == ((tokensSent / 4) * (float(realEstateFee + marketingFee + developerFee) / 100))
    # assert chainEstateToken.balanceOf(realEstateWalletAddress) == realEstateInitialBalance + ((tokensSent / 4) * (float(realEstateFee) / 100))
    # assert chainEstateToken.balanceOf(marketingWalletAddress) == devMarketingInitialBalance + ((tokensSent / 4) * (float(marketingFee + developerFee) / 100))

    # Asserts that the accounts' air drop invest times have been set.
    assert chainEstateToken.airDropInvestTime(account.address) > chainEstateToken.initialTimeStamp()
    assert chainEstateToken.airDropInvestTime(account.address) < chainEstateToken.initialTimeStamp() + 1000
    assert chainEstateToken.airDropInvestTime(account2.address) > chainEstateToken.initialTimeStamp()
    assert chainEstateToken.airDropInvestTime(account2.address) < chainEstateToken.initialTimeStamp() + 1000

    # Claim the air drop rewards.
    initialAccountBalance = chainEstateToken.balanceOf(account.address)
    chainEstateAirDrop.changeAirDropMinimumToInvest(100000, {"from": account})
    chainEstateAirDrop.changeMinimumInvestTime(1, False, {"from": account})
    chainEstateAirDrop.openAirDrop({"from": account})

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        chain.mine(1)
        chain.sleep(10)
        chain.mine(1)
    else:
        time.sleep(10)

    chainEstateAirDrop.claimAirDrop({"from": account})

    # Asserts that the air drop rewards were sent to the account.
    airDropInitialPercent = chainEstateAirDrop.airDropInitialPercent()
    assert chainEstateToken.balanceOf(account.address) > initialAccountBalance + ((initialAccountBalance * airDropInitialPercent) / 100)
    assert chainEstateToken.balanceOf(account.address) < initialAccountBalance + ((initialAccountBalance * airDropInitialPercent) / 50)

    chainEstateAirDrop.changeAirDropMinimumToInvest(10000 * 10 ** 18, {"from": account})
    chainEstateAirDrop.changeMinimumInvestTime(30, True, {"from": account})
    chainEstateAirDrop.closeAirDrop({"from": account})