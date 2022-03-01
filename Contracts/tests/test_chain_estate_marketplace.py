from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_chain_estate
from scripts.deploy_marketplace import deploy_chain_estate_marketplace
from brownie import network, accounts, exceptions, chain
from web3 import Web3
import pytest
import time

LIQUIDITY_SUPPLY = Web3.toWei(300000000, "ether")
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

def test_chain_estate_marketplace():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate(account3, account4, account5, account5, account5)
    chainEstateMarketplace, chainEstateNFT = deploy_chain_estate_marketplace(chainEstateToken.address)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account5})

    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Owner can create an NFT
    chainEstateNFT.createToken("Test Token", 1, {"from": account})
    tokenId = chainEstateNFT._tokenIds()
    
    tokenOwner = chainEstateNFT.ownerOf(tokenId)
    assert tokenOwner == account.address

    # Non-owner can't create an NFT
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateNFT.createToken("Test Token 2", 2, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)

    # Owner can set the listing fee for the marketplace
    listingFee = chainEstateMarketplace.getListingPrice()
    assert listingFee == Web3.toWei(0.2, "ether")
    newListingFee = Web3.toWei(0.0001, "ether")
    chainEstateMarketplace.setListingPrice(newListingFee, {"from": account})

    # Non-owner can't set the listing fee for the marketplace
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateMarketplace.setListingPrice(newListingFee, {"from": account3})
    assert "Ownable: caller is not the owner" in str(ex.value)

    # Owner can't create an NFT with an invalid NFT address
    listingFee = chainEstateMarketplace.getListingPrice()
    NFTPrice = 1000000
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateMarketplace.createMarketItem(ZERO_ADDRESS, tokenId, NFTPrice, {"from": account})
    assert "revert: This isn't a valid Chain Estate DAO NFT contract" in str(ex.value)

    # Owner can add the NFT to the marketplace without a fee
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, tokenId, NFTPrice, {"from": account})

    # Assert the NFT was added to the marketplace properly
    marketplaceNFTs = chainEstateMarketplace.fetchMarketItems()
    createdNFT = marketplaceNFTs[0]
    
    assert createdNFT[0] == 1
    assert createdNFT[1] == chainEstateNFT.address
    assert createdNFT[2] == 1
    assert createdNFT[3] == account.address
    assert createdNFT[4] == ZERO_ADDRESS
    assert createdNFT[5] == NFTPrice
    assert createdNFT[6] == False

    # User can't purchase the NFT without sending the proper amount
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateMarketplace.createMarketSale(chainEstateNFT.address, tokenId, NFTPrice / 2, {"from": account5})
    assert "revert: Please submit the asking price in order to complete the purchase" in str(ex.value)

    # User can't purchase an NFT from an invalid NFT address
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateMarketplace.createMarketSale(ZERO_ADDRESS, tokenId, NFTPrice, {"from": account5})
    assert "revert: This isn't a valid Chain Estate DAO NFT contract" in str(ex.value)

    # User can't purchase an NFT without first approving the marketplace to spend their CHES tokens
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateMarketplace.createMarketSale(chainEstateNFT.address, tokenId, NFTPrice, {"from": account5})
    assert "revert: ERC20: transfer amount exceeds allowance" in str(ex.value)

    # User can purchase the NFT listed on the marketplace
    initialAccountBalance = chainEstateToken.balanceOf(account5.address)
    chainEstateToken.approve(chainEstateMarketplace.address, NFTPrice, {"from": account5})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, tokenId, NFTPrice, {"from": account5})
    assert chainEstateToken.balanceOf(account5.address) == initialAccountBalance - NFTPrice

    accountNFTs = chainEstateMarketplace.fetchMyNFTs({"from": account5})
    assert len(accountNFTs) == 1
    assert accountNFTs[0][3] == account.address
    assert accountNFTs[0][4] == account5.address

    tokenOwner = chainEstateNFT.ownerOf(tokenId)
    assert tokenOwner == account5.address

    # User can't list the NFT they just purchased without paying the listing fee
    newNFTPrice = NFTPrice * 2
    chainEstateNFT.approve(chainEstateMarketplace.address, tokenId, {"from": account5})
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateMarketplace.createMarketItem(chainEstateNFT.address, tokenId, newNFTPrice, {"from": account5})
    assert "revert: Price must be equal to listing price" in str(ex.value)

    # User can list the NFT they just purchased if they pay the listing fee
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, tokenId, newNFTPrice, {"from": account5, "value": listingFee})

    # Assert the NFT was added to the marketplace properly
    marketplaceNFTs = chainEstateMarketplace.fetchMarketItems()
    createdNFT = marketplaceNFTs[0]
    
    assert createdNFT[0] == 2
    assert createdNFT[1] == chainEstateNFT.address
    assert createdNFT[2] == 1
    assert createdNFT[3] == account5.address
    assert createdNFT[4] == ZERO_ADDRESS
    assert createdNFT[5] == newNFTPrice
    assert createdNFT[6] == False

    # User can purchase the NFT listed on the marketplace by another user (not the owner)
    initialAccount4Balance = chainEstateToken.balanceOf(account4.address)
    initialAccount5Balance = chainEstateToken.balanceOf(account5.address)
    marketItemId = 2
    ownerInitialBalance = account.balance()

    chainEstateToken.approve(chainEstateMarketplace.address, newNFTPrice, {"from": account4})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, marketItemId, newNFTPrice, {"from": account4})

    accountNFTs = chainEstateMarketplace.fetchMyNFTs({"from": account4})
    assert len(accountNFTs) == 1

    assert chainEstateToken.balanceOf(account4.address) == initialAccount4Balance - newNFTPrice
    assert chainEstateToken.balanceOf(account5.address) == initialAccount5Balance + newNFTPrice

    assert accountNFTs[0][3] == account5.address
    assert accountNFTs[0][4] == account4.address

    tokenOwner = chainEstateNFT.ownerOf(tokenId)
    assert tokenOwner == account4.address

    assert account.balance() == ownerInitialBalance + listingFee

    accountNFTs = chainEstateMarketplace.fetchMyNFTs({"from": account4})
    assert len(accountNFTs) == 1
    assert accountNFTs[0][0] == 2
    assert accountNFTs[0][1] == chainEstateNFT.address
    assert accountNFTs[0][2] == 1
    assert accountNFTs[0][3] == account5.address
    assert accountNFTs[0][4] == account4.address
    assert accountNFTs[0][5] == newNFTPrice
    assert accountNFTs[0][6] == True