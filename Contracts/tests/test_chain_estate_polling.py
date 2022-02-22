from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_chain_estate
from brownie import network, accounts, exceptions
from web3 import Web3
import pytest

LIQUIDITY_SUPPLY = Web3.toWei(300000000, "ether")

def test_owner_can_make_poll():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, chainEstatePolling = deploy_chain_estate()

    # Act
    chainEstatePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})

    # Assert
    assert chainEstatePolling.votingOpen() == True
    assert chainEstatePolling.currPollTitle() == "Test Poll"
    assert chainEstatePolling.getNumberOfProposals() == 3
    assert chainEstatePolling.proposals(0)[0] == "Test Option 1"
    assert chainEstatePolling.proposals(0)[1] == 0
    assert chainEstatePolling.proposals(1)[0] == "Test Option 2"
    assert chainEstatePolling.proposals(1)[1] == 0
    assert chainEstatePolling.proposals(2)[0] == "Test Option 3"
    assert chainEstatePolling.proposals(2)[1] == 0

def test_non_owner_cant_make_poll():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
    
    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, chainEstatePolling = deploy_chain_estate()

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstatePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)

def test_users_can_vote_in_poll():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, chainEstatePolling = deploy_chain_estate()
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Act
    chainEstateToken.transfer(account2.address, 5000000, {"from": account})
    chainEstatePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})
    chainEstatePolling.vote(0, {"from": account})
    chainEstatePolling.vote(1, {"from": account2})

    # Assert
    assert chainEstatePolling.proposals(0)[1] == chainEstateToken.balanceOf(account.address)
    assert chainEstatePolling.proposals(1)[1] == chainEstateToken.balanceOf(account2.address)
    assert chainEstatePolling.winningProposalName() == "Test Option 1"

def test_users_can_vote_in_poll_2():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, chainEstatePolling = deploy_chain_estate()
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Act
    chainEstateToken.transfer(account2.address, 10000000, {"from": account})
    chainEstatePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})
    chainEstatePolling.vote(2, {"from": account})
    chainEstatePolling.vote(2, {"from": account2})

    # Assert
    assert chainEstatePolling.proposals(2)[1] == chainEstateToken.balanceOf(account.address) + chainEstateToken.balanceOf(account2.address)
    assert chainEstatePolling.winningProposalName() == "Test Option 3"

def test_user_without_CHES_cant_vote():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, chainEstatePolling = deploy_chain_estate()
    chainEstatePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})

    # Assert/Act
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstatePolling.vote(0, {"from": account2})
    assert "You need CHES tokens to be able to vote." in str(ex.value)

def test_user_cant_vote_twice():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, chainEstatePolling = deploy_chain_estate()
    chainEstatePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})

    # Assert/Act
    chainEstatePolling.vote(0, {"from": account})
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstatePolling.vote(1, {"from": account})
    assert "You have already voted in this poll." in str(ex.value)

def test_owner_can_close_poll():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    chainEstateToken, chainEstateAirDrop, chainEstatePolling = deploy_chain_estate()
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Act
    chainEstateToken.transfer(account2.address, 5000000, {"from": account})
    chainEstatePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})
    chainEstatePolling.vote(2, {"from": account})
    chainEstatePolling.vote(0, {"from": account2})

    chainEstatePolling.closePoll({"from": account})

    # Assert
    assert chainEstatePolling.votingOpen() == False
    assert chainEstatePolling.winningProposalName() == "Test Option 3"
    assert chainEstatePolling.pastPolls(0)[0] == "Test Poll" 
    assert chainEstatePolling.pastPolls(0)[1] == "Test Option 3" 
    assert chainEstatePolling.pastPolls(0)[2] == 3
    
    for i in range(chainEstatePolling.pastPolls(0)[2]):
        assert chainEstatePolling.getPastProposal(0, i)[0] == f"Test Option {i + 1}"

    assert chainEstatePolling.getPastProposal(0, 0)[1] == chainEstateToken.balanceOf(account2.address)
    assert chainEstatePolling.getPastProposal(0, 2)[1] == chainEstateToken.balanceOf(account.address)

def test_past_proposals_store_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    chainEstateToken, chainEstateAirDrop, chainEstatePolling = deploy_chain_estate()
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Act
    chainEstateToken.transfer(account2.address, 5000000, {"from": account})
    chainEstateToken.transfer(account3.address, 10000000, {"from": account})
    chainEstatePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})
    chainEstatePolling.vote(2, {"from": account})
    chainEstatePolling.vote(0, {"from": account2})
    chainEstatePolling.vote(1, {"from": account3})

    chainEstatePolling.closePoll({"from": account})

    chainEstatePolling.createNewPoll("Test Poll 2", ["Test Option 4", "Test Option 5", "Test Option 6", "Test Option 7", "Test Option 8"], {"from": account})
    chainEstatePolling.vote(3, {"from": account})
    chainEstatePolling.vote(3, {"from": account2})
    chainEstatePolling.vote(4, {"from": account3})

    chainEstatePolling.closePoll({"from": account})

    # Assert
    assert chainEstatePolling.votingOpen() == False
    assert chainEstatePolling.winningProposalName() == "Test Option 7"
    assert chainEstatePolling.pastPolls(1)[0] == "Test Poll 2" 
    assert chainEstatePolling.pastPolls(1)[1] == "Test Option 7" 
    assert chainEstatePolling.pastPolls(1)[2] == 5
    assert chainEstatePolling.numPastPolls() == 2

    for i in range(chainEstatePolling.numPastPolls()):
        for j in range(chainEstatePolling.pastPolls(i)[2]):
            assert chainEstatePolling.getPastProposal(i, j)[0] == f"Test Option {3*i + j + 1}"

    assert chainEstatePolling.getPastProposal(0, 0)[1] == chainEstateToken.balanceOf(account2.address)
    assert chainEstatePolling.getPastProposal(0, 1)[1] == chainEstateToken.balanceOf(account3.address)
    assert chainEstatePolling.getPastProposal(0, 2)[1] == chainEstateToken.balanceOf(account.address)

    assert chainEstatePolling.getPastProposal(1, 3)[1] == chainEstateToken.balanceOf(account.address) + chainEstateToken.balanceOf(account2.address)
    assert chainEstatePolling.getPastProposal(1, 4)[1] == chainEstateToken.balanceOf(account3.address)