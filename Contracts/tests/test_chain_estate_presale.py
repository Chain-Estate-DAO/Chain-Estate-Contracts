from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_chain_estate
from brownie import network, accounts, exceptions
import pytest

# Presale is no longer going to happen so these tests will not be run. Keeping the code here for reference.

'''
def test_user_can_purchase_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, chainEstatePreSale, _ = deploy_chain_estate()
    initialPreSaleBalance = chainEstateToken.balanceOf(chainEstatePreSale.address)
    initialAccountBalance = chainEstateToken.balanceOf(account.address)
    initialAccountBalanceBNB = account.balance()

    # Act
    BNBSent = 5
    chainEstatePreSale.purchaseCHESTokens({"from": account, "value": BNBSent})

    # Assert
    BNBToCHESRate = chainEstatePreSale.BNBToCHESRate()
    assert chainEstateToken.balanceOf(account.address) == initialAccountBalance + BNBToCHESRate * BNBSent
    assert chainEstatePreSale.getContractTokens() == initialPreSaleBalance - BNBToCHESRate * BNBSent
    assert account.balance() == initialAccountBalanceBNB - BNBSent
    assert chainEstatePreSale.getContractBNB() == BNBSent

def test_owner_can_change_purchase_cap():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, chainEstatePreSale, _ = deploy_chain_estate()

    # Act
    initialPurchaseCap = chainEstatePreSale.purchaseCap()
    purchaseCap = initialPurchaseCap / 2
    chainEstatePreSale.changeCHESPurchaseCap(purchaseCap, {"from": account})

    # Assert
    assert chainEstatePreSale.purchaseCap() == purchaseCap

def test_user_cant_purchase_above_purchase_cap():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, chainEstatePreSale, _ = deploy_chain_estate()

    BNBToCHESRate = chainEstatePreSale.BNBToCHESRate()
    purchaseCap = 10
    chainEstatePreSale.changeCHESPurchaseCap(purchaseCap, {"from": account})

    # Act/Assert
    BNBSent = 5
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstatePreSale.purchaseCHESTokens({"from": account, "value": BNBSent})
    assert "You cannot purchase this many CHES tokens, that would put you past your presale cap" in str(ex.value)

def test_user_cant_purchase_above_purchase_cap_2():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, chainEstatePreSale, _ = deploy_chain_estate()

    BNBToCHESRate = chainEstatePreSale.BNBToCHESRate()
    BNBSent = 5
    purchaseCap = BNBSent * 2 * BNBToCHESRate
    chainEstatePreSale.changeCHESPurchaseCap(purchaseCap, {"from": account})

    # Act/Assert
    chainEstatePreSale.purchaseCHESTokens({"from": account, "value": BNBSent})
    accountPurchaseAmount = chainEstatePreSale.addressToAmountPurchased(account.address)
    assert accountPurchaseAmount == purchaseCap / 2

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstatePreSale.purchaseCHESTokens({"from": account, "value": BNBSent + 1})
    assert "You cannot purchase this many CHES tokens, that would put you past your presale cap" in str(ex.value)

def test_only_owner_can_change_purchase_cap():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, chainEstatePreSale, _ = deploy_chain_estate()

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstatePreSale.changeCHESPurchaseCap(10, {"from": account2})
    assert "revert: Ownable: caller is not the owner" in str(ex.value)

def test_owner_can_change_BNB_conversion_rate():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, chainEstatePreSale, _ = deploy_chain_estate()
    initialPreSaleBalance = chainEstateToken.balanceOf(chainEstatePreSale.address)
    initialAccountBalance = chainEstateToken.balanceOf(account.address)
    initialAccountBalanceBNB = account.balance()

    # Act
    BNBSent = 2
    initialConversionRate = chainEstatePreSale.BNBToCHESRate()
    newConversionRate = 75000
    chainEstatePreSale.purchaseCHESTokens({"from": account, "value": BNBSent})
    chainEstatePreSale.changeBNBToCHESRate(75000, {"from": account})
    chainEstatePreSale.purchaseCHESTokens({"from": account, "value": BNBSent})

    # Assert
    BNBToCHESRate = chainEstatePreSale.BNBToCHESRate()
    assert BNBToCHESRate == newConversionRate
    assert chainEstateToken.balanceOf(account.address) == initialAccountBalance + (initialConversionRate + BNBToCHESRate) * BNBSent
    assert chainEstatePreSale.getContractTokens() == initialPreSaleBalance - (initialConversionRate + BNBToCHESRate) * BNBSent
    assert account.balance() == initialAccountBalanceBNB - BNBSent * 2
    assert chainEstatePreSale.getContractBNB() == BNBSent * 2

def test_only_owner_can_change_BNB_conversion_rate():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, chainEstatePreSale, _ = deploy_chain_estate()

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstatePreSale.changeBNBToCHESRate(75000, {"from": account})
    assert "revert: Ownable: caller is not the owner" in str(ex.value)

def test_owner_can_withdraw_funds():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, chainEstatePreSale, _ = deploy_chain_estate()

    initialPreSaleBalance = chainEstateToken.balanceOf(chainEstatePreSale.address)
    initialAccount2Balance = chainEstateToken.balanceOf(account2.address)
    initialAccountBalanceBNB = account.balance()
    initialAccount2BalanceBNB = account2.balance()
    
    # Act
    BNBSent = 10
    chainEstatePreSale.purchaseCHESTokens({"from": account2, "value": BNBSent})

    # Assert
    BNBToCHESRate = chainEstatePreSale.BNBToCHESRate()
    assert chainEstateToken.balanceOf(account2.address) == initialAccount2Balance + BNBToCHESRate * BNBSent
    assert chainEstateToken.balanceOf(chainEstatePreSale.address) == initialPreSaleBalance - BNBToCHESRate * BNBSent
    assert account2.balance() == initialAccount2BalanceBNB - BNBSent
    assert chainEstatePreSale.balance() == BNBSent

    # Act 2
    bnbWithdraw = 8
    presaleBNBBalance = chainEstatePreSale.balance()
    chainEstatePreSale.withdrawBNB(bnbWithdraw, {"from": account})

    # Assert 2
    assert account.balance() == initialAccountBalanceBNB + bnbWithdraw
    assert chainEstatePreSale.balance() == presaleBNBBalance - bnbWithdraw
    
def test_owner_cant_over_withdraw():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, chainEstatePreSale, _ = deploy_chain_estate()

    # Act
    BNBSent = 5
    BNBWithdraw = BNBSent * 2
    chainEstatePreSale.purchaseCHESTokens({"from": account2, "value": BNBSent})

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstatePreSale.withdrawBNB(BNBWithdraw, {"from": account})
    assert "revert: Failed to send BNB" in str(ex.value)

def test_only_owner_can_withdraw_funds():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
    
    account = retrieve_account()
    account2 = retrieve_account(2)

    # Act
    BNBSent = 8
    chainEstateToken, chainEstateAirDrop, chainEstatePreSale, _ = deploy_chain_estate()
    chainEstatePreSale.purchaseCHESTokens({"from": account, "value": BNBSent})

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstatePreSale.withdrawBNB(BNBSent / 2, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)
'''