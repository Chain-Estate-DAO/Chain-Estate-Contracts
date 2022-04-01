from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_chain_estate
from brownie import network, accounts, exceptions, chain
from web3 import Web3
import pytest
import time

LIQUIDITY_SUPPLY = Web3.toWei(300000000, "ether")

def test_can_transfer_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

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
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account3.address, account4.address, account5.address, account5.address)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account5})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Account 3 is the real estate wallet
    realEstateWalletAddress = chainEstateToken.realEstateWalletAddress()
    # Account 4 is the marketing wallet
    marketingWalletAddress = chainEstateToken.marketingWalletAddress()
    # Account 5 is the developer wallet
    developerWalletAddress = chainEstateToken.developerWalletAddress()
    chainEstateTokenAddress = chainEstateToken.getContractAddress()

    realEstateFee = chainEstateToken.realEstateTransactionFeePercent()
    marketingFee = chainEstateToken.marketingFeePercent()
    developerFee = chainEstateToken.developerFeePercent()

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
    assert chainEstateToken.balanceOf(account2.address) == transferAmount * ((100 - realEstateFee - marketingFee - developerFee) / 100)

    realEstateFeeAmount = transferAmount * (realEstateFee / 100)
    marketingFeeAmount = transferAmount * (marketingFee / 100)
    developerFeeAmount = transferAmount * (developerFee / 100)
    assert chainEstateToken.balanceOf(chainEstateTokenAddress) == realEstateFeeAmount + marketingFeeAmount + developerFeeAmount

def test_air_drop_time_is_calculated_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

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
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

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
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

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

def test_transaction_fee_works_on_transfer_from():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account3.address, account4.address, account5.address, account5.address)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account5})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Account 3 is the real estate wallet
    realEstateWalletAddress = chainEstateToken.realEstateWalletAddress()
    # Account 4 is the marketing wallet
    marketingWalletAddress = chainEstateToken.marketingWalletAddress()
    # Account 5 is the developer wallet
    developerWalletAddress = chainEstateToken.developerWalletAddress()
    chainEstateTokenAddress = chainEstateToken.getContractAddress()
    realEstateInitialBalance = chainEstateToken.balanceOf(realEstateWalletAddress)
    marketingInitialBalance = chainEstateToken.balanceOf(marketingWalletAddress)
    developerInitialBalance = chainEstateToken.balanceOf(developerWalletAddress)

    realEstateFee = chainEstateToken.realEstateTransactionFeePercent()
    marketingFee = chainEstateToken.marketingFeePercent()
    developerFee = chainEstateToken.developerFeePercent()

    # Act
    tokenAmount = 1000000
    initialAccountBalance = chainEstateToken.balanceOf(account.address)
    initialAccount2Balance = chainEstateToken.balanceOf(account2.address)
    chainEstateToken.transfer(account.address, tokenAmount, {"from": account5})
    chainEstateToken.transfer(account2.address, tokenAmount, {"from": account5})

    assert chainEstateToken.balanceOf(account.address) == initialAccountBalance + tokenAmount
    assert chainEstateToken.balanceOf(account2.address) == initialAccount2Balance + tokenAmount

    # Approve account 1 to spend account 2's tokens and then spend them with the transferFrom function.
    initialAccount2Balance = chainEstateToken.balanceOf(account2.address)
    initialAccount3Balance = chainEstateToken.balanceOf(account3.address)
    chainEstateToken.includeUsersInFees(account3.address, {"from": account})
    chainEstateToken.approve(account.address, tokenAmount, {"from": account2})
    chainEstateToken.transferFrom(account2.address, account3.address, tokenAmount, {"from": account})

    # Assert
    assert chainEstateToken.balanceOf(account3.address) == initialAccount3Balance + tokenAmount * ((100 - realEstateFee - marketingFee - developerFee) / 100)
    assert chainEstateToken.balanceOf(account2.address) == initialAccount2Balance - tokenAmount

    realEstateFeeAmount = tokenAmount * (realEstateFee / 100)
    marketingFeeAmount = tokenAmount * (marketingFee / 100)
    developerFeeAmount = tokenAmount * (developerFee / 100)
    assert chainEstateToken.balanceOf(chainEstateTokenAddress) == realEstateFeeAmount + marketingFeeAmount + developerFeeAmount

def test_owner_cant_update_fees_past_limit():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    realEstateFeeLimit = 20
    marketingFeeLimit = 5
    developerFeeLimit = 5

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.updateRealEstateTransactionFee(realEstateFeeLimit + 1, {"from": account})
    assert "The real estate transaction fee can't be more than 20%." in str(ex.value)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.updateMarketingTransactionFee(marketingFeeLimit + 1, {"from": account})
    assert "The marketing transaction fee can't be more than 5%." in str(ex.value)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.updateDeveloperTransactionFee(developerFeeLimit + 1, {"from": account})
    assert "The developer transaction fee can't be more than 5%." in str(ex.value)

def test_owner_can_update_fees_within_limit():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()
    chainEstateToken.setContractCHESDivisor(1, {"from": account})
    chainEstateTokenAddress = chainEstateToken.getContractAddress()

    realEstateFeeLimit = 20
    marketingFeeLimit = 5
    developerFeeLimit = 5

    # Act
    chainEstateToken.updateRealEstateTransactionFee(realEstateFeeLimit, {"from": account})
    chainEstateToken.updateMarketingTransactionFee(marketingFeeLimit, {"from": account})
    chainEstateToken.updateDeveloperTransactionFee(developerFeeLimit, {"from": account})

    # Assert
    realEstateFee = chainEstateToken.realEstateTransactionFeePercent()
    marketingFee = chainEstateToken.marketingFeePercent()
    developerFee = chainEstateToken.developerFeePercent() 

    assert realEstateFee == realEstateFeeLimit
    assert marketingFee == marketingFeeLimit
    assert developerFee == developerFeeLimit

def test_transaction_fees_work_after_fee_update():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account3.address, account4.address, account5.address, account5.address)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account5})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Account 3 is the real estate wallet
    realEstateWalletAddress = chainEstateToken.realEstateWalletAddress()
    # Account 4 is the marketing wallet
    marketingWalletAddress = chainEstateToken.marketingWalletAddress()
    # Account 5 is the developer wallet
    developerWalletAddress = chainEstateToken.developerWalletAddress()
    chainEstateTokenAddress = chainEstateToken.getContractAddress()

    realEstateFeeLimit = 20
    marketingFeeLimit = 5
    developerFeeLimit = 5

    # Act
    chainEstateToken.updateRealEstateTransactionFee(realEstateFeeLimit, {"from": account})
    chainEstateToken.updateMarketingTransactionFee(marketingFeeLimit, {"from": account})
    chainEstateToken.updateDeveloperTransactionFee(developerFeeLimit, {"from": account})

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
    assert chainEstateToken.balanceOf(account2.address) == transferAmount * ((100 - realEstateFeeLimit - marketingFeeLimit - developerFeeLimit) / 100)

    realEstateFeeAmount = transferAmount * (realEstateFeeLimit / 100)
    marketingFeeAmount = transferAmount * (marketingFeeLimit / 100)
    developerFeeAmount = transferAmount * (developerFeeLimit / 100)
    assert chainEstateToken.balanceOf(chainEstateTokenAddress) == realEstateFeeAmount + marketingFeeAmount + developerFeeAmount

def test_blacklist_stops_trading():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act/Assert
    tokenAmount = 7500000
    tokenAmount2 = 1000000
    initialAccountCHESBalance = chainEstateToken.balanceOf(account.address)
    initialAccount2CHESBalance = chainEstateToken.balanceOf(account2.address)
    chainEstateToken.transfer(account2.address, tokenAmount, {"from": account})
    chainEstateToken.transfer(account.address, tokenAmount2, {"from": account2})

    assert chainEstateToken.balanceOf(account.address) == initialAccountCHESBalance - tokenAmount + tokenAmount2
    assert chainEstateToken.balanceOf(account2.address) == initialAccount2CHESBalance + tokenAmount - tokenAmount2

    # Blacklist account 2 and make sure they can't transfer or transferFrom
    chainEstateToken.updateBlackList(account2.address, True, {"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.transfer(account2.address, tokenAmount, {"from": account})
    assert "The address you are trying to send CHES to has been blacklisted from trading the CHES token. If you think this is an error, please contact the Chain Estate DAO team." in str(ex.value)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.transfer(account.address, tokenAmount2, {"from": account2})
    assert "You have been blacklisted from trading the CHES token. If you think this is an error, please contact the Chain Estate DAO team." in str(ex.value)

    chainEstateToken.approve(account.address, 1000000000, {"from": account2})
    chainEstateToken.approve(account3.address, 1000000000, {"from": account2})
    chainEstateToken.approve(account2.address, 1000000000, {"from": account})
    chainEstateToken.approve(account3.address, 1000000000, {"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.transferFrom(account.address, account3.address, tokenAmount, {"from": account2})
    assert "You have been blacklisted from trading the CHES token. If you think this is an error, please contact the Chain Estate DAO team." in str(ex.value)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.transferFrom(account2.address, account3.address, tokenAmount, {"from": account})
    assert "The address you're trying to spend the tokens from has been blacklisted from trading the CHES token. If you think this is an error, please contact the Chain Estate DAO team." in str(ex.value)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.transferFrom(account.address, account2.address, tokenAmount, {"from": account3})
    assert "The address you are trying to send tokens to has been blacklisted from trading the CHES token. If you think this is an error, please contact the Chain Estate DAO team." in str(ex.value)

    # Unblacklist account 2 and make sure they can trade again
    chainEstateToken.updateBlackList(account2.address, False, {"from": account})

    initialAccountCHESBalance = chainEstateToken.balanceOf(account.address)
    initialAccount2CHESBalance = chainEstateToken.balanceOf(account2.address)
    chainEstateToken.transfer(account2.address, tokenAmount, {"from": account})
    chainEstateToken.transfer(account.address, tokenAmount2, {"from": account2})

    assert chainEstateToken.balanceOf(account.address) == initialAccountCHESBalance - tokenAmount + tokenAmount2
    assert chainEstateToken.balanceOf(account2.address) == initialAccount2CHESBalance + tokenAmount - tokenAmount2

    initialAccountCHESBalance = chainEstateToken.balanceOf(account.address)
    initialAccount2CHESBalance = chainEstateToken.balanceOf(account2.address)
    chainEstateToken.transferFrom(account.address, account2.address, tokenAmount, {"from": account3})
    chainEstateToken.transferFrom(account2.address, account.address, tokenAmount2, {"from": account3})

    assert chainEstateToken.balanceOf(account.address) == initialAccountCHESBalance - tokenAmount + tokenAmount2
    assert chainEstateToken.balanceOf(account2.address) == initialAccount2CHESBalance + tokenAmount - tokenAmount2

def test_only_owner_can_add_minters():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.updateMinter(account.address, True, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)    

def test_only_minters_can_mint_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.mint(account2.address, 1000000, {"from": account})
    assert "You are not authorized to mint CHES tokens." in str(ex.value)

def test_only_minters_can_burn_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateToken.burn(account2.address, 1000000, {"from": account})
    assert "You are not authorized to burn CHES tokens." in str(ex.value)

def test_minters_can_mint_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act
    tokenMintAmount = 3500000
    initialTokenSupply = chainEstateToken.totalSupply()
    initialAccount2CHESBalance = chainEstateToken.balanceOf(account2.address)
    chainEstateToken.updateMinter(account.address, True, {"from": account})
    chainEstateToken.mint(account2.address, tokenMintAmount, {"from": account})

    # Assert
    assert chainEstateToken.balanceOf(account2.address) == initialAccount2CHESBalance + tokenMintAmount
    assert chainEstateToken.totalSupply() == initialTokenSupply + tokenMintAmount

def test_minters_can_burn_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()

    # Act
    tokenBurnAmount = 1000000
    initialTokenSupply = chainEstateToken.totalSupply()
    initialAccountCHESBalance = chainEstateToken.balanceOf(account.address)
    chainEstateToken.updateMinter(account.address, True, {"from": account})
    chainEstateToken.burn(account.address, tokenBurnAmount, {"from": account})

    # Assert
    assert chainEstateToken.balanceOf(account.address) == initialAccountCHESBalance - tokenBurnAmount
    assert chainEstateToken.totalSupply() == initialTokenSupply - tokenBurnAmount
