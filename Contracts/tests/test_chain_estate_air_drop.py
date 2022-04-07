from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_chain_estate
from brownie import network, accounts, exceptions, chain
from web3 import Web3
import pytest
import time

LIQUIDITY_SUPPLY = Web3.toWei(300000000, "ether")

def test_owner_can_open_air_drop():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act
    chainEstateAirDrop.openAirDrop({"from": account})

    # Assert
    assert chainEstateAirDrop.airDropActive()

def test_only_owner_can_open_air_drop():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act/Assert
    nonOwner = accounts.add()
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateAirDrop.openAirDrop({"from": nonOwner})
    assert "Ownable: caller is not the owner" in str(ex.value)

def test_owner_can_close_air_drop():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act
    chainEstateAirDrop.openAirDrop({"from": account})
    chainEstateAirDrop.closeAirDrop({"from": account})

    # Assert
    assert not chainEstateAirDrop.airDropActive()

def test_only_owner_can_close_air_drop():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act/Assert
    chainEstateAirDrop.openAirDrop({"from": account})
    nonOwner = accounts.add()
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateAirDrop.closeAirDrop({"from": nonOwner})
    assert "Ownable: caller is not the owner" in str(ex.value)

def test_user_can_claim_air_drop():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account2, account2, account2, account2, account2)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account2})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Act
    tokensSent = 500000000
    chainEstateToken.transfer(account.address, tokensSent, {"from": account2})
    chainEstateAirDrop.changeMinimumInvestTime(1, False, {"from": account})
    chainEstateAirDrop.changeAirDropMinimumToInvest(tokensSent, {"from": account})
    print(f"Air drop time stamp: {chainEstateToken.airDropInvestTime(account.address)}")
    chainEstateAirDrop.openAirDrop({"from": account})
    chain.mine(100)
    chain.sleep(100)
    chain.mine(100)
    chainEstateAirDrop.claimAirDrop({"from": account})

    # Assert
    assert chainEstateToken.balanceOf(account.address) > tokensSent
    assert chainEstateToken.balanceOf(account.address) <= tokensSent * 1.2

def test_owner_can_change_initial_airdrop_reward_percentage():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account2, account2, account2, account2, account2)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account2})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Act
    tokensSent = 5000000
    chainEstateToken.transfer(account.address, tokensSent, {"from": account2})
    chain.mine(100)
    chain.sleep(100)
    chain.mine(100)
    chainEstateAirDrop.changeMinimumInvestTime(1, False, {"from": account})
    chainEstateAirDrop.changeAirDropMinimumToInvest(tokensSent, {"from": account})
    chainEstateAirDrop.changeAirDropInitialPercent(50, {"from": account})
    chainEstateAirDrop.openAirDrop({"from": account})
    chainEstateAirDrop.claimAirDrop({"from": account})

    # Assert
    assert chainEstateAirDrop.airDropInitialPercent() == 50
    assert chainEstateToken.balanceOf(account.address) > tokensSent * 1.8
    assert chainEstateToken.balanceOf(account.address) <= tokensSent * 2

def test_owner_can_change_initial_airdrop_reward_percentage_2():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account2, account2, account2, account2, account2)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account2})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Act
    tokensSent = 5000000
    chainEstateToken.transfer(account.address, tokensSent, {"from": account2})
    chain.mine(100)
    chain.sleep(100)
    chain.mine(100)
    chainEstateAirDrop.changeMinimumInvestTime(1, False, {"from": account})
    chainEstateAirDrop.changeAirDropMinimumToInvest(tokensSent, {"from": account})
    chainEstateAirDrop.changeAirDropInitialPercent(20, {"from": account})
    chainEstateAirDrop.openAirDrop({"from": account})
    chainEstateAirDrop.claimAirDrop({"from": account})

    # Assert
    assert chainEstateAirDrop.airDropInitialPercent() == 20
    assert chainEstateToken.balanceOf(account.address) > tokensSent * 1.3
    assert chainEstateToken.balanceOf(account.address) <= tokensSent * 1.4

def test_user_cant_claim_air_drop_twice():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account2, account2, account2, account2, account2)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account2})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Act
    tokensSent = 50
    chainEstateToken.transfer(account.address, tokensSent, {"from": account2})
    chainEstateAirDrop.changeMinimumInvestTime(1, False, {"from": account})
    chainEstateAirDrop.changeAirDropMinimumToInvest(tokensSent, {"from": account})
    chainEstateAirDrop.openAirDrop({"from": account})
    chainEstateAirDrop.claimAirDrop({"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateAirDrop.claimAirDrop({"from": account})
    assert "You've already claimed your rewards from this air drop!" in str(ex.value)

def test_user_cant_claim_when_not_invested_enough():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account2, account2, account2, account2, account2)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account2})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Act
    tokensSent = 50
    chainEstateToken.transfer(account.address, tokensSent, {"from": account2})
    chainEstateAirDrop.changeMinimumInvestTime(1, False, {"from": account})
    chainEstateAirDrop.changeAirDropMinimumToInvest(tokensSent + 1, {"from": account})
    chainEstateAirDrop.openAirDrop({"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateAirDrop.claimAirDrop({"from": account})
    assert "You need to have more invested to receive rewards from air drops!" in str(ex.value)

def test_user_cant_claim_when_not_invested_long_enough():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account2, account2, account2, account2, account2)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account2})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Act
    tokensSent = 50
    chainEstateToken.transfer(account.address, tokensSent, {"from": account2})
    chainEstateAirDrop.changeMinimumInvestTime(30, True, {"from": account})
    chainEstateAirDrop.changeAirDropMinimumToInvest(tokensSent, {"from": account})
    chainEstateAirDrop.openAirDrop({"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateAirDrop.claimAirDrop({"from": account})
    assert "Too many of your recent investments were made too close to the air drop time. You can claim your rewards in" in str(ex.value)    

def test_user_cant_claim_when_airdrop_is_closed():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account2, account2, account2, account2, account2)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account2})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Act
    tokensSent = 50
    chainEstateToken.transfer(account.address, tokensSent, {"from": account2})
    chainEstateAirDrop.changeMinimumInvestTime(1, False, {"from": account})
    chainEstateAirDrop.changeAirDropMinimumToInvest(tokensSent, {"from": account})
    chainEstateAirDrop.openAirDrop({"from": account})
    chainEstateAirDrop.closeAirDrop({"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateAirDrop.claimAirDrop({"from": account})
    assert "The air drop is not currently active. You can claim your air drop rewards when an air drop is ongoing." in str(ex.value)    
