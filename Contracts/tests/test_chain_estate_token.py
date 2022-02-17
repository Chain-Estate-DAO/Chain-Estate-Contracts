from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_chain_estate
from brownie import network, accounts, exceptions, chain
import pytest
import time

def test_can_transfer_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act
    chainEstateToken.transfer(account2.address, 10000, {"from": account})
    chainEstateToken.transfer(account.address, 2000, {"from": account2})

    # Assert
    account2Balance = chainEstateToken.balanceOf(account2.address)
    assert account2Balance == 8000
    waitForTransactionsToComplete()

def test_transaction_fees_work():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account3.address, account4.address, account5.address, account5.address, account5.address)

    # Account 3 is the real estate wallet
    realEstateWalletAddress = chainEstateToken.realEstateWalletAddress()
    # Account 5 is the developer/marketing wallet
    marketingWalletAddress = chainEstateToken.marketingWalletAddress()
    developerWalletAddress = chainEstateToken.developerWalletAddress()
    realEstateInitialBalance = chainEstateToken.balanceOf(realEstateWalletAddress)
    marketingInitialBalance = chainEstateToken.balanceOf(marketingWalletAddress)
    developerInitialBalance = chainEstateToken.balanceOf(developerWalletAddress)

    realEstateFee = chainEstateToken.realEstateTransactionFeePercent()
    devTeamMarketingFee = chainEstateToken.developerFeePercent() + chainEstateToken.marketingFeePercent()

    # Act
    # Account deployed the smart contract and thus was excluded from fees by default, so needs to be added.
    chainEstateToken.includeUsersInFees(account.address, {"from": account})

    # Send tokens from account5 to account
    tokensSent = 10000
    chainEstateToken.transfer(account.address, tokensSent, {"from": account5})

    # Transfer some tokens to account2
    transferAmount = 100
    chainEstateToken.transfer(account2.address, transferAmount, {"from": account})

    # Assert
    assert chainEstateToken.balanceOf(account.address) == tokensSent - transferAmount
    assert chainEstateToken.balanceOf(account2.address) == transferAmount * ((100 - realEstateFee - devTeamMarketingFee) / 100)
    assert chainEstateToken.balanceOf(realEstateWalletAddress) == realEstateInitialBalance + transferAmount * (realEstateFee / 100)
    assert chainEstateToken.balanceOf(marketingWalletAddress) == marketingInitialBalance + transferAmount * (devTeamMarketingFee / 100) - tokensSent
    assert chainEstateToken.balanceOf(developerWalletAddress) == developerInitialBalance + transferAmount * (devTeamMarketingFee / 100) - tokensSent

def test_air_drop_time_is_calculated_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act
    chainEstateToken.transfer(account2.address, 10000, {"from": account})

    # Assert
    epoch_time = chain.time()
    account2AirDropInvestTime = chainEstateToken.airDropInvestTime(account2.address)
    assert abs(epoch_time - account2AirDropInvestTime) <= 2
    waitForTransactionsToComplete()

def test_air_drop_time_is_calculated_correctly_2():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act
    waitSeconds = 5
    chainEstateToken.transfer(account2.address, 1000000, {"from": account})
    time.sleep(waitSeconds)
    chainEstateToken.transfer(account2.address, 10, {"from": account})

    # Assert
    epoch_time = chain.time()
    account2AirDropInvestTime = chainEstateToken.airDropInvestTime(account2.address)
    assert abs(epoch_time - account2AirDropInvestTime - waitSeconds) <= 2
    waitForTransactionsToComplete()

def test_air_drop_time_is_calculated_correctly_3():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act
    waitSeconds = 10
    chainEstateToken.transfer(account2.address, 10000, {"from": account})
    time.sleep(waitSeconds)
    chainEstateToken.transfer(account2.address, 10000, {"from": account})

    # Assert
    epoch_time = chain.time()
    account2AirDropInvestTime = chainEstateToken.airDropInvestTime(account2.address)
    assert abs(epoch_time - account2AirDropInvestTime - (waitSeconds/2)) <= 2
    waitForTransactionsToComplete()

def test_owner_can_exclude_users_from_fees():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act
    chainEstateToken.excludeUserFromFees(account2.address, {"from": account})

    # Assert
    assert chainEstateToken.excludedFromFees(account2.address)

def test_only_owner_can_exclude_users_from_fees():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act/Assert
    nonOwner = accounts.add()
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.excludeUserFromFees(nonOwner.address, {"from": nonOwner})
    assert "Ownable: caller is not the owner" in str(ex.value)

def test_owner_can_include_users_into_fees():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act
    chainEstateToken.includeUsersInFees(chainEstateAirDrop.address, {"from": account})

    # Assert
    assert not chainEstateToken.excludedFromFees(chainEstateAirDrop.address)

def test_only_owner_can_include_users_from_fees():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act/Assert
    nonOwner = accounts.add()
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.includeUsersInFees(chainEstateAirDrop.address, {"from": nonOwner})
    assert "Ownable: caller is not the owner" in str(ex.value)