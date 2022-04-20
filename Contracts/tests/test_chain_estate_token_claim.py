from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, DONT_PUBLISH_SOURCE_ENVIRONMENTS, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_chain_estate
from scripts.deployV1 import deploy_chain_estate_V1
from scripts.deploy_token_claim import deploy_token_claim
from scripts.set_CHES_claim_balances import set_CHES_claim_balances
from brownie import network, accounts, exceptions, chain
from web3 import Web3
from pathlib import Path
import pytest
import math
import time
import csv

LIQUIDITY_SUPPLY = Web3.toWei(300000000, "ether")

def test_owner_can_setup_balances():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    # Act
    accounts = [account.address, account2.address, account3.address, account4.address, account5.address]
    balances = [100, 200, 300, 400, 500]
    chainEstateTokenClaim.setupTokenBalances(accounts, balances, {"from": account})

    # Assert
    for i in range(len(accounts)):
        assert chainEstateTokenClaim.balances(accounts[i]) == balances[i]
        assert chainEstateTokenClaim.claimed(accounts[i]) == False

def test_non_owner_cant_setup_balances():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    # Act/Assert
    accounts = [account.address, account2.address, account3.address, account4.address, account5.address]
    balances = [100, 200, 300, 400, 500]

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateTokenClaim.setupTokenBalances(accounts, balances, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)

def test_owner_can_update_claimed():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    # Act
    chainEstateTokenClaim.setUserClaimedV2CHES(account2.address, True, {"from": account})

    # Assert
    assert chainEstateTokenClaim.claimed(account2.address) == True    

def test_non_owner_cant_update_claimed():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateTokenClaim.setUserClaimedV2CHES(account3.address, True, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)    

def test_owner_can_update_user_balance():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    # Act
    newUserBalance = 12345
    chainEstateTokenClaim.setUserV2CHESBalance(account2.address, newUserBalance, {"from": account})

    # Assert
    assert chainEstateTokenClaim.balances(account2.address) == newUserBalance    

def test_non_owner_cant_update_user_balance():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        newUserBalance = 12345
        chainEstateTokenClaim.setUserV2CHESBalance(account3.address, newUserBalance, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)    

def test_user_can_claim_v2_CHES_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    chainEstateTokenV1.excludeUserFromFees(chainEstateTokenClaim.address, {"from": account})

    # Transfer V1 CHES tokens from account to each of the other accounts
    account2Balance, account3Balance, account4Balance, account5Balance = (200000, 300000, 400000, 500000)
    chainEstateTokenV1.transfer(account2.address, account2Balance, {"from": account})
    chainEstateTokenV1.transfer(account3.address, account3Balance, {"from": account})
    chainEstateTokenV1.transfer(account4.address, account4Balance, {"from": account})
    chainEstateTokenV1.transfer(account5.address, account5Balance, {"from": account})

    # Act
    initialTimeStamp = chain.time()
    chain.mine(100)
    chain.sleep(100)
    chain.mine(100)
    currentTimeStamp = chain.time()

    account1Balance = chainEstateTokenV1.balanceOf(account.address)
    totalBalance = account1Balance + account2Balance + account3Balance + account4Balance + account5Balance

    # Transfer the necessary V2 tokens to the claim contract to distribute to all the accounts claiming
    chainEstateTokenV2.transfer(chainEstateTokenClaim.address, totalBalance, {"from": account})

    accounts = [account.address, account2.address, account3.address, account4.address, account5.address]
    balances = [account1Balance, account2Balance, account3Balance, account4Balance, account5Balance]
    chainEstateTokenClaim.setupTokenBalances(accounts, balances, {"from": account})

    chainEstateTokenV1.approve(chainEstateTokenClaim.address, account1Balance, {"from": account})
    chainEstateTokenV1.approve(chainEstateTokenClaim.address, account2Balance, {"from": account2})
    chainEstateTokenV1.approve(chainEstateTokenClaim.address, account3Balance, {"from": account3})
    chainEstateTokenV1.approve(chainEstateTokenClaim.address, account4Balance, {"from": account4})
    chainEstateTokenV1.approve(chainEstateTokenClaim.address, account5Balance, {"from": account5})

    chainEstateTokenClaim.claimV2CHESTokens({"from": account})
    chainEstateTokenClaim.claimV2CHESTokens({"from": account2})
    chainEstateTokenClaim.claimV2CHESTokens({"from": account3})
    chainEstateTokenClaim.claimV2CHESTokens({"from": account4})
    chainEstateTokenClaim.claimV2CHESTokens({"from": account5})

    # Assert
    assert chainEstateTokenV2.excludedFromFees(chainEstateTokenClaim.address) == True

    assert chainEstateTokenV1.balanceOf(account.address) == 0
    assert chainEstateTokenV1.balanceOf(account2.address) == 0
    assert chainEstateTokenV1.balanceOf(account3.address) == 0
    assert chainEstateTokenV1.balanceOf(account4.address) == 0
    assert chainEstateTokenV1.balanceOf(account5.address) == 0
    assert chainEstateTokenV1.balanceOf(chainEstateTokenClaim.address) == totalBalance

    assert chainEstateTokenV2.balanceOf(account.address) == account1Balance
    assert chainEstateTokenV2.balanceOf(account2.address) == account2Balance
    assert chainEstateTokenV2.balanceOf(account3.address) == account3Balance
    assert chainEstateTokenV2.balanceOf(account4.address) == account4Balance
    assert chainEstateTokenV2.balanceOf(account5.address) == account5Balance
    assert chainEstateTokenV2.balanceOf(chainEstateTokenClaim.address) == 0

    assert chainEstateTokenClaim.claimed(account.address) == True
    assert chainEstateTokenClaim.claimed(account2.address) == True
    assert chainEstateTokenClaim.claimed(account3.address) == True
    assert chainEstateTokenClaim.claimed(account4.address) == True
    assert chainEstateTokenClaim.claimed(account5.address) == True

    assert initialTimeStamp < currentTimeStamp
    assert abs(chainEstateTokenV2.airDropInvestTime(account.address) - initialTimeStamp) < 20
    assert abs(chainEstateTokenV2.airDropInvestTime(account2.address) - initialTimeStamp) < 20
    assert abs(chainEstateTokenV2.airDropInvestTime(account3.address) - initialTimeStamp) < 20
    assert abs(chainEstateTokenV2.airDropInvestTime(account4.address) - initialTimeStamp) < 20
    assert abs(chainEstateTokenV2.airDropInvestTime(account5.address) - initialTimeStamp) < 20

def test_user_cant_claim_tokens_twice():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    uniswapPair = chainEstateTokenV1.uniswapPair()
    chainEstateTokenV1.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateTokenV1.setContractCHESDivisor(1, {"from": account})

    # Act/Assert
    accounts = [account2.address]
    account2V2Balance = 1000000
    balances = [account2V2Balance]
    chainEstateTokenClaim.setupTokenBalances(accounts, balances, {"from": account})

    accountBalance = chainEstateTokenV1.balanceOf(account.address)
    chainEstateTokenV2.transfer(chainEstateTokenClaim.address, accountBalance, {"from": account})
    chainEstateTokenV1.transfer(account2.address, account2V2Balance, {"from": account})

    chainEstateTokenV1.approve(chainEstateTokenClaim.address, account2V2Balance, {"from": account2})
    chainEstateTokenClaim.claimV2CHESTokens({"from": account2})   

    chainEstateTokenV1.approve(chainEstateTokenClaim.address, account2V2Balance, {"from": account2})
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateTokenClaim.claimV2CHESTokens({"from": account2}) 
    assert "You already claimed your CHES tokens for the v2 migration." in str(ex.value)   

def test_user_cant_claim_tokens_before_approving_v1_transfer():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    uniswapPair = chainEstateTokenV1.uniswapPair()
    chainEstateTokenV1.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateTokenV1.setContractCHESDivisor(1, {"from": account})

    # Act/Assert
    accounts = [account2.address]
    account2V2Balance = 1000000
    balances = [account2V2Balance]
    chainEstateTokenClaim.setupTokenBalances(accounts, balances, {"from": account})

    accountBalance = chainEstateTokenV1.balanceOf(account.address)
    chainEstateTokenV2.transfer(chainEstateTokenClaim.address, accountBalance, {"from": account})
    chainEstateTokenV1.transfer(account2.address, account2V2Balance, {"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateTokenClaim.claimV2CHESTokens({"from": account2}) 
    assert "You must first allow the token claim contract to spend your V1 CHES tokens before you can claim your V2 CHES tokens." in str(ex.value)     


def test_user_cant_claim_tokens_after_selling():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    uniswapPair = chainEstateTokenV1.uniswapPair()
    chainEstateTokenV1.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateTokenV1.setContractCHESDivisor(1, {"from": account})

    # Act/Assert
    accounts = [account2.address]
    account2V2Balance = 1000000
    balances = [account2V2Balance]
    chainEstateTokenClaim.setupTokenBalances(accounts, balances, {"from": account})

    accountBalance = chainEstateTokenV1.balanceOf(account.address)
    chainEstateTokenV2.transfer(chainEstateTokenClaim.address, accountBalance, {"from": account})
    chainEstateTokenV1.transfer(account2.address, account2V2Balance, {"from": account})

    chainEstateTokenV1.transfer(account.address, account2V2Balance / 2, {"from": account2}) 

    chainEstateTokenV1.approve(chainEstateTokenClaim.address, account2V2Balance, {"from": account2})
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateTokenClaim.claimV2CHESTokens({"from": account2}) 
    assert "You sold at least some of your V1 CHES tokens during the migration process so you cannot migrate to V2." in str(ex.value)  

def test_owner_can_withdraw_excess_v2_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    uniswapPair = chainEstateTokenV1.uniswapPair()
    uniswapPairV2 = chainEstateTokenV2.uniswapPair()
    chainEstateTokenV1.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateTokenV2.transfer(uniswapPairV2, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateTokenV1.setContractCHESDivisor(1, {"from": account})
    chainEstateTokenV2.setContractCHESDivisor(1, {"from": account})

    # Act
    accounts = [account2.address]
    account2V2Balance = 1000000
    balances = [account2V2Balance]
    chainEstateTokenClaim.setupTokenBalances(accounts, balances, {"from": account})

    accountBalance = chainEstateTokenV1.balanceOf(account.address)
    chainEstateTokenV2.transfer(chainEstateTokenClaim.address, accountBalance, {"from": account})
    chainEstateTokenV1.transfer(account2.address, account2V2Balance, {"from": account})

    chainEstateTokenV1.approve(chainEstateTokenClaim.address, account2V2Balance, {"from": account2})
    chainEstateTokenClaim.claimV2CHESTokens({"from": account2}) 

    chainEstateTokenClaim.withdrawV2CHESTokens(chainEstateTokenV2.balanceOf(chainEstateTokenClaim.address), {"from": account})  

    # Assert
    assert chainEstateTokenV2.balanceOf(account.address) == accountBalance - account2V2Balance

def test_non_owner_cant_withdraw_excess_v2_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    uniswapPair = chainEstateTokenV1.uniswapPair()
    chainEstateTokenV1.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateTokenV1.setContractCHESDivisor(1, {"from": account})

    # Act/Assert
    accounts = [account2.address]
    account2V2Balance = 1000000
    balances = [account2V2Balance]
    chainEstateTokenClaim.setupTokenBalances(accounts, balances, {"from": account})

    accountBalance = chainEstateTokenV1.balanceOf(account.address)
    chainEstateTokenV2.transfer(chainEstateTokenClaim.address, accountBalance, {"from": account})
    chainEstateTokenV1.transfer(account2.address, account2V2Balance, {"from": account})

    chainEstateTokenV1.approve(chainEstateTokenClaim.address, account2V2Balance, {"from": account2})
    chainEstateTokenClaim.claimV2CHESTokens({"from": account2}) 

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateTokenClaim.withdrawV2CHESTokens(chainEstateTokenV2.balanceOf(account2.address), {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)

def test_owner_can_import_holder_data():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    # Act
    accounts = []
    balances = []

    print(f"Account BNB balance is currently: {account.balance()}")

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

    # Assert
    for i in range(len(accounts)):
        assert chainEstateTokenClaim.balances(accounts[i]) == balances[i]
    
def test_set_CHES_balances_script_works():
    # Arrange
    if network.show_active() not in DONT_PUBLISH_SOURCE_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains or testnet.")
        
    account = retrieve_account()
    chainEstateTokenV1, chainEstateAirDropV1, _ = deploy_chain_estate_V1()
    chainEstateTokenV2, chainEstateAirDropV2, _ = deploy_chain_estate()
    chainEstateTokenClaim = deploy_token_claim(chainEstateTokenV1.address, chainEstateTokenV2.address)

    # Act
    set_CHES_claim_balances(chainEstateTokenClaim.address)


    # Assert
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
                    pass

    for i in range(len(accounts)):
        assert chainEstateTokenClaim.balances(accounts[i]) == balances[i]


