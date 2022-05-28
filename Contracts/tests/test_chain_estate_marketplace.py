from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_chain_estate
from scripts.deploy_marketplace import deploy_chain_estate_marketplace
from scripts.update_NFT_token_URIs import update_NFT_token_URIs
from brownie import network, accounts, exceptions, chain
from web3 import Web3
import requests
import pytest
import time

LIQUIDITY_SUPPLY = Web3.toWei(300000000, "ether")
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

TEST_NFT_TOKEN_URI_UPDATE = True

def test_chain_estate_NFT_token_URI_updating():
    # Don't want to upload to IPFS all the time, so only run this test of the flag for it is set.
    if not TEST_NFT_TOKEN_URI_UPDATE:
        pytest.skip("The flag for this test isn't set so it won't be run.")

    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()
    chainEstateMarketplace, chainEstateNFT = deploy_chain_estate_marketplace(chainEstateToken.address)

    NFT1TokenURI = '{\"name\": \"test NFT\", \"price\": \"1000\", \"image\": \"test image\"}'
    NFT2TokenURI = '{\"name\": \"test NFT 2\", \"price\": \"10000\", \"image\": \"test image 2\"}'
    NFT3TokenURI = '{\"name\": \"test NFT 3\", \"price\": \"100000\", \"image\": \"test image 3\"}'

    NFTTokenURIs = [NFT1TokenURI, NFT2TokenURI, NFT3TokenURI]

    for NFTTokenURI in NFTTokenURIs:
        files = {'file': NFTTokenURI}
        response = requests.post('https://ipfs.infura.io:5001/api/v0/add', files=files)
        tokenURIHash = response.json()["Hash"]
        newTokenURI = f"https://ipfs.infura.io/ipfs/{tokenURIHash}"

        listingFee = Web3.toWei(0.05, "ether")
        chainEstateNFT.createToken(newTokenURI, 0, listingFee, {"from": account})

        NFTTokenURI = newTokenURI

        print(newTokenURI)

    update_NFT_token_URIs(chainEstateNFT.address, [1, 2, 3], ["D:\\Chain-Estate-Frontend\\public\\Apartment.png", "D:\\Chain-Estate-Frontend\\public\\SingleFamilyHome.png", "D:\\Chain-Estate-Frontend\\public\\Apartment.png"])

    print(chainEstateNFT.tokenURI(1))
    print(chainEstateNFT.tokenURI(2))
    print(chainEstateNFT.tokenURI(3))

def test_chain_estate_marketplace_whitelisting():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()
    chainEstateMarketplace, chainEstateNFT = deploy_chain_estate_marketplace(chainEstateToken.address)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})

    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    # Give some tokens to each of the accounts.
    chainEstateToken.transfer(account2.address, 1000000000, {"from": account})
    chainEstateToken.transfer(account3.address, 1000000000, {"from": account})
    chainEstateToken.transfer(account4.address, 1000000000, {"from": account})
    chainEstateToken.transfer(account5.address, 1000000000, {"from": account})

    # Create CHES NFTs
    listingFee = Web3.toWei(0.05, "ether")
    chainEstateNFT.createToken("CHES NFT 1", 2, listingFee, {"from": account})
    chainEstateNFT.createToken("CHES NFT 2", 3, listingFee, {"from": account})
    chainEstateNFT.createToken("CHES NFT 3", 4, listingFee, {"from": account})
    chainEstateNFT.createToken("CHES NFT 4", 5, listingFee, {"from": account})
    chainEstateNFT.createToken("CHES NFT 5", 6, listingFee, {"from": account})

    # Whitelist the first NFT to account 2 (token ID = 1) and the second NFT to account 3 (token ID = 2)
    chainEstateNFT.addWhiteListToToken(account2.address, 1)
    chainEstateNFT.addWhiteListToToken(account3.address, 2)

    # List the NFTs on the marketplace, no listing fee for the owner account (account 1)
    NFTPrice = 2000000
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 1, NFTPrice, {"from": account})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 2, NFTPrice, {"from": account})

    # account 2 can't purchase the NFT for account 3
    chainEstateToken.approve(chainEstateMarketplace.address, NFTPrice, {"from": account2})
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 2, NFTPrice, {"from": account2})
    assert "This NFT has been assigned to someone through a Whitelist spot. Only they can purchase this NFT." in str(ex.value)

    # account can't purchase the NFT for account 2
    chainEstateToken.approve(chainEstateMarketplace.address, NFTPrice, {"from": account})
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 1, NFTPrice, {"from": account})
    assert "This NFT has been assigned to someone through a Whitelist spot. Only they can purchase this NFT." in str(ex.value)

    # Purchase the NFT for account 2 that was assigned through the whitelist spot
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 1, NFTPrice, {"from": account2})
    assert chainEstateNFT.ownerOf(1) == account2.address

    # Purchase the NFT for account 3 that was assigned through the whitelist spot
    chainEstateToken.approve(chainEstateMarketplace.address, NFTPrice, {"from": account3})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 2, NFTPrice, {"from": account3})
    assert chainEstateNFT.ownerOf(2) == account3.address

    # Have account 2 list the NFT it just purchased back on the marketplace
    chainEstateNFT.approve(chainEstateMarketplace.address, 1, {"from": account2})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 1, NFTPrice * 2, {"from": account2, "value": listingFee})

    # Since the whitelist spot only applies when the contract owner is selling
    # the NFT, make sure a different account can now purchase the NFT that account 2 is selling.
    chainEstateToken.approve(chainEstateMarketplace.address, NFTPrice * 2, {"from": account5})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 3, NFTPrice * 2, {"from": account5})
    assert chainEstateNFT.ownerOf(1) == account5.address

    # Have account 3 list the NFT it just purchased back on the marketplace
    chainEstateNFT.approve(chainEstateMarketplace.address, 2, {"from": account3})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 2, NFTPrice * 5, {"from": account3, "value": listingFee})

    # Since the whitelist spot only applies when the contract owner is selling
    # the NFT, make sure a different account can now purchase the NFT that account  3is selling.
    chainEstateToken.approve(chainEstateMarketplace.address, NFTPrice * 5, {"from": account})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 4, NFTPrice * 5, {"from": account})
    assert chainEstateNFT.ownerOf(2) == account.address

def test_chain_estate_marketplace_reflection_nfts():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    chainEstateToken, chainEstateAirDrop, _ = deploy_chain_estate()
    chainEstateMarketplace, chainEstateNFT = deploy_chain_estate_marketplace(chainEstateToken.address)
    uniswapPair = chainEstateToken.uniswapPair()
    chainEstateToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})

    chainEstateToken.setContractCHESDivisor(1, {"from": account})

    chainEstateToken.excludeUserFromFees(chainEstateMarketplace.address, {"from": account})
    chainEstateMarketplace.updateCanHaveMultipleReflectionNFTs(True, {"from": account})

    # Give some tokens to each of the accounts.
    chainEstateToken.transfer(account2.address, 1000000000, {"from": account})
    chainEstateToken.transfer(account3.address, 1000000000, {"from": account})
    chainEstateToken.transfer(account4.address, 1000000000, {"from": account})
    chainEstateToken.transfer(account5.address, 1000000000, {"from": account})

    # Create the reflection NFTs
    reflectionListingFee = Web3.toWei(0.02, "ether")
    chainEstateNFT.createToken("Reflection NFT 1", 1, reflectionListingFee, {"from": account})
    chainEstateNFT.createToken("Reflection NFT 2", 1, reflectionListingFee, {"from": account})
    chainEstateNFT.createToken("Reflection NFT 3", 1, reflectionListingFee, {"from": account})
    chainEstateNFT.createToken("Reflection NFT 4", 1, reflectionListingFee, {"from": account})
    chainEstateNFT.createToken("Reflection NFT 5", 1, reflectionListingFee, {"from": account})
    chainEstateNFT.createToken("Reflection NFT 6", 1, reflectionListingFee, {"from": account})
    chainEstateNFT.createToken("Reflection NFT 7", 1, reflectionListingFee, {"from": account})
    chainEstateNFT.createToken("Reflection NFT 8", 1, reflectionListingFee, {"from": account})
    chainEstateNFT.createToken("Reflection NFT 9", 1, reflectionListingFee, {"from": account})
    chainEstateNFT.createToken("Reflection NFT 10", 1, reflectionListingFee, {"from": account})

    # Create the regular NFTs (fake property NFTs)
    regularListingFee = Web3.toWei(0.03, "ether")
    chainEstateNFT.createToken("Regular NFT 1", 2, regularListingFee, {"from": account})
    chainEstateNFT.createToken("Regular NFT 2", 3, regularListingFee, {"from": account})
    chainEstateNFT.createToken("Regular NFT 3", 4, regularListingFee, {"from": account})
    chainEstateNFT.createToken("Regular NFT 4", 5, regularListingFee, {"from": account})
    chainEstateNFT.createToken("Regular NFT 5", 6, regularListingFee, {"from": account})

    # Make sure the token ID count is correct
    tokenId = chainEstateNFT._tokenIds()
    assert tokenId == 15

    # Put half of the reflection NFTs on the market - token IDs 1 through 5
    ReflectionNFTPrice = 100000
    initialAccountBalance = account.balance()
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 1, ReflectionNFTPrice, {"from": account, "value": reflectionListingFee})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 2, ReflectionNFTPrice, {"from": account, "value": reflectionListingFee})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 3, ReflectionNFTPrice, {"from": account, "value": reflectionListingFee})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 4, ReflectionNFTPrice, {"from": account, "value": reflectionListingFee})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 5, ReflectionNFTPrice, {"from": account, "value": reflectionListingFee})

    # Make sure owner doesn't get charged the listing fee
    assert account.balance() == initialAccountBalance

    # Put four of the regular NFTs on the market - token IDs 11 through 14
    RegularNFTPrice = 5000000
    initialAccountBalance = account.balance()
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 11, RegularNFTPrice, {"from": account, "value": regularListingFee})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 12, RegularNFTPrice, {"from": account, "value": regularListingFee})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 13, RegularNFTPrice, {"from": account, "value": regularListingFee})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 14, RegularNFTPrice, {"from": account, "value": regularListingFee})

    # Make sure owner doesn't get charged the listing fee
    assert account.balance() == initialAccountBalance

    # Have other accounts purchase the reflection NFTs
    # Account 2 and Account 3 will own two reflection NFTs, account 4 will own one, and account 5 will own none
    chainEstateToken.approve(chainEstateMarketplace.address, ReflectionNFTPrice * 2, {"from": account2})
    chainEstateToken.approve(chainEstateMarketplace.address, ReflectionNFTPrice * 2, {"from": account3})
    chainEstateToken.approve(chainEstateMarketplace.address, ReflectionNFTPrice, {"from": account4})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 1, ReflectionNFTPrice, {"from": account2})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 2, ReflectionNFTPrice, {"from": account2})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 3, ReflectionNFTPrice, {"from": account3})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 4, ReflectionNFTPrice, {"from": account3})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 5, ReflectionNFTPrice, {"from": account4})

    # Have account 5 purchase the regular NFT
    account1InitialBalance = account.balance()
    account2InitialBalance = account2.balance()
    account3InitialBalance = account3.balance()
    account4InitialBalance = account4.balance()
    chainEstateToken.approve(chainEstateMarketplace.address, RegularNFTPrice, {"from": account5})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 6, RegularNFTPrice, {"from": account5})

    # No one should have gotten any listing fees since this was an owner sold NFT
    assert account.balance() == account1InitialBalance
    assert account2.balance() == account2InitialBalance
    assert account3.balance() == account3InitialBalance
    assert account4.balance() == account4InitialBalance

    # Have account 5 put the regular NFT back on the marketplace with paying the listing fee
    account1InitialBalance = account.balance()
    account2InitialBalance = account2.balance()
    account3InitialBalance = account3.balance()
    account4InitialBalance = account4.balance()
    account5InitialBalance = account5.balance()
    chainEstateNFT.approve(chainEstateMarketplace.address, 11, {"from": account5})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 11, RegularNFTPrice, {"from": account5, "value": regularListingFee})

    # Make sure account5 paid the listing fee
    assert account5.balance() == account5InitialBalance - regularListingFee

    # Have account5 purchase back the NFT.
    chainEstateToken.approve(chainEstateMarketplace.address, RegularNFTPrice, {"from": account5})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 10, RegularNFTPrice, {"from": account5})

    # Make sure the listing fee was distributed correctly to the reflection NFT holders
    # Account 1 has 5 / 10 reflection NFTs, account 2 has 2 / 10, account 3 has 2 / 10, and account 4 has 1 / 10
    assert account.balance() == account1InitialBalance + regularListingFee / 2
    assert account2.balance() == account2InitialBalance + regularListingFee / 5
    assert account3.balance() == account3InitialBalance + regularListingFee / 5
    assert account4.balance() == account4InitialBalance + regularListingFee / 10

    # Have account 3 sell one of the reflection NFTs
    account1InitialBalance = account.balance()
    account2InitialBalance = account2.balance()
    account3InitialBalance = account3.balance()
    account4InitialBalance = account4.balance()
    account5InitialBalance = account5.balance()
    account2InitialCHESBalance = chainEstateToken.balanceOf(account2.address)
    account3InitialCHESBalance = chainEstateToken.balanceOf(account3.address)
    chainEstateNFT.approve(chainEstateMarketplace.address, 3, {"from": account3})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 3, ReflectionNFTPrice, {"from": account3, "value": reflectionListingFee})

    # Have account 2 purchase the reflection NFT
    chainEstateToken.approve(chainEstateMarketplace.address, ReflectionNFTPrice, {"from": account2})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 11, ReflectionNFTPrice, {"from": account2})

    # Make sure the listing fee was distributed correctly to the reflection NFT holders
    assert account.balance() == account1InitialBalance + reflectionListingFee * 6 / 10
    assert account2.balance() == account2InitialBalance + reflectionListingFee / 5
    assert account3.balance() == account3InitialBalance + reflectionListingFee / 10 - reflectionListingFee
    assert account4.balance() == account4InitialBalance + reflectionListingFee / 10
    assert chainEstateToken.balanceOf(account2.address) == account2InitialCHESBalance - ReflectionNFTPrice
    assert chainEstateToken.balanceOf(account3.address) == account3InitialCHESBalance + ReflectionNFTPrice

    # Have account 5 purchase and resell an NFT to ensure the reflection NFT owners are updated properly
    initialAccountCHESBalance = chainEstateToken.balanceOf(account.address)
    chainEstateToken.approve(chainEstateMarketplace.address, RegularNFTPrice, {"from": account5})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 7, RegularNFTPrice, {"from": account5})

    assert chainEstateToken.balanceOf(account.address) == initialAccountCHESBalance + RegularNFTPrice

    # Resell the NFT that was just purchased
    account1InitialBalance = account.balance()
    account2InitialBalance = account2.balance()
    account3InitialBalance = account3.balance()
    account4InitialBalance = account4.balance()
    account5InitialBalance = account5.balance()
    account3InitialCHESBalance = chainEstateToken.balanceOf(account3.address)
    account5InitialCHESBalance = chainEstateToken.balanceOf(account5.address)
    chainEstateNFT.approve(chainEstateMarketplace.address, 12, {"from": account5})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, 12, RegularNFTPrice, {"from": account5, "value": regularListingFee})

    # Have account 3 purchase the regular NFT that account 5 just listed
    chainEstateToken.approve(chainEstateMarketplace.address, RegularNFTPrice, {"from": account3})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, 12, RegularNFTPrice, {"from": account3})

    # Make sure the listing fee was distributed correctly to the reflection NFT holders
    assert account.balance() == account1InitialBalance + regularListingFee / 2
    assert account2.balance() == account2InitialBalance + regularListingFee * 3 / 10
    assert account3.balance() == account3InitialBalance + regularListingFee / 10
    assert account4.balance() == account4InitialBalance + regularListingFee / 10
    assert account5.balance() == account5InitialBalance - regularListingFee
    assert chainEstateToken.balanceOf(account3.address) == account3InitialCHESBalance - RegularNFTPrice
    assert chainEstateToken.balanceOf(account5.address) == account5InitialCHESBalance + RegularNFTPrice
    

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
    listingFee = Web3.toWei(0.02, "ether")
    chainEstateNFT.createToken("Test Token", 1, listingFee, {"from": account})
    tokenId = chainEstateNFT._tokenIds()
    
    tokenOwner = chainEstateNFT.ownerOf(tokenId)
    assert tokenOwner == account.address
    assert chainEstateNFT.tokenIdToListingFee(tokenId) == listingFee

    # User can fetch all token URIs for all NFTs someone owns
    tokenURIs = chainEstateNFT.getUserTokenURIs(account.address)
    # tokenURIs = tokenURIs.return_value
    assert len(tokenURIs) == 1
    assert tokenURIs[0] == "Test Token"

    # Non-owner can't create an NFT
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateNFT.createToken("Test Token 2", 2, listingFee, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)

    # Owner can set the listing fee for the marketplace
    defaultListingFee = chainEstateMarketplace.getDefaultListingPrice()
    assert defaultListingFee == Web3.toWei(0.05, "ether")
    newDefaultListingFee = Web3.toWei(0.0001, "ether")
    chainEstateMarketplace.setDefaultListingPrice(newDefaultListingFee, {"from": account})

    # Non-owner can't set the listing fee for the marketplace
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateMarketplace.setDefaultListingPrice(newDefaultListingFee, {"from": account3})
    assert "Ownable: caller is not the owner" in str(ex.value)

    # Owner can't create an NFT with an invalid NFT address
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
    assert createdNFT[7] == "Test Token"
    assert createdNFT[8] == listingFee

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
    assert "revert: ERC20: insufficient allowance" in str(ex.value)

    # User can purchase the NFT listed on the marketplace
    initialAccountBalance = chainEstateToken.balanceOf(account5.address)
    chainEstateToken.approve(chainEstateMarketplace.address, NFTPrice, {"from": account5})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, tokenId, NFTPrice, {"from": account5})
    assert chainEstateToken.balanceOf(account5.address) == initialAccountBalance - NFTPrice

    accountNFTs = chainEstateMarketplace.fetchMyNFTs(account5.address)
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
    assert "revert: Not enough or too much BNB was sent to pay the NFT listing fee." in str(ex.value)

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
    assert createdNFT[7] == "Test Token"
    assert createdNFT[8] == listingFee

    # User can purchase the NFT listed on the marketplace by another user (not the owner)
    initialAccount4Balance = chainEstateToken.balanceOf(account4.address)
    initialAccount5Balance = chainEstateToken.balanceOf(account5.address)
    marketItemId = 2
    ownerInitialBalance = account.balance()

    chainEstateToken.approve(chainEstateMarketplace.address, newNFTPrice, {"from": account4})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, marketItemId, newNFTPrice, {"from": account4})

    accountNFTs = chainEstateMarketplace.fetchMyNFTs(account4.address)
    assert len(accountNFTs) == 1

    assert chainEstateToken.balanceOf(account4.address) == initialAccount4Balance - newNFTPrice
    assert chainEstateToken.balanceOf(account5.address) == initialAccount5Balance + newNFTPrice

    assert accountNFTs[0][3] == account5.address
    assert accountNFTs[0][4] == account4.address

    tokenOwner = chainEstateNFT.ownerOf(tokenId)
    assert tokenOwner == account4.address

    assert account.balance() == ownerInitialBalance + listingFee

    accountNFTs = chainEstateMarketplace.fetchMyNFTs(account4.address)
    assert len(accountNFTs) == 1
    assert accountNFTs[0][0] == 2
    assert accountNFTs[0][1] == chainEstateNFT.address
    assert accountNFTs[0][2] == 1
    assert accountNFTs[0][3] == account5.address
    assert accountNFTs[0][4] == account4.address
    assert accountNFTs[0][5] == newNFTPrice
    assert accountNFTs[0][6] == True
    assert accountNFTs[0][7] == "Test Token"
    assert accountNFTs[0][8] == listingFee

    # Reflection NFTs function properly.
    # Account4 has the reflection NFT, so it should get the listing fee.
    listingFee = Web3.toWei(0.04, "ether")
    NFTPrice *= 2
    chainEstateNFT.createToken("Test Token Non Reflection", 2, listingFee, {"from": account})
    tokenId = chainEstateNFT._tokenIds()
    initialAccount4Balance = account4.balance()
    initialAccount5CHESBalance = chainEstateToken.balanceOf(account5.address)

    # Given the newly minted NFT to account2
    chainEstateNFT.transferFrom(account.address, account2.address, tokenId, {"from": account})
    assert chainEstateNFT.ownerOf(tokenId) == account2.address

    # Put the non-reflection NFT on the marketplace
    chainEstateNFT.approve(chainEstateMarketplace.address, tokenId, {"from": account2})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, tokenId, NFTPrice, {"from": account2, "value": listingFee})
    assert chainEstateNFT.ownerOf(tokenId) == chainEstateMarketplace.address

    # Have account5 purchase the NFT
    marketItemId += 1
    chainEstateToken.approve(chainEstateMarketplace.address, NFTPrice, {"from": account5})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, marketItemId, NFTPrice, {"from": account5})
    
    # Assert that the transaction was successful and that account4 got the listing fees
    # since account4 has the reflection NFT.
    assert chainEstateNFT.ownerOf(tokenId) == account5.address
    assert chainEstateToken.balanceOf(account5.address) == initialAccount5CHESBalance - NFTPrice
    assert account4.balance() == initialAccount4Balance + listingFee

    # User can cancel market sale
    assert len(chainEstateMarketplace.fetchMarketItems()) == 0
    initialAccount5Balance = account5.balance()
    chainEstateNFT.approve(chainEstateMarketplace.address, tokenId, {"from": account5})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, tokenId, NFTPrice, {"from": account5, "value": listingFee})
    assert account5.balance() == initialAccount5Balance - listingFee

    # Make sure someone random can't cancel the market sale
    marketItemId += 1
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateMarketplace.cancelMarketSale(chainEstateNFT.address, marketItemId, {"from": account2})
    assert "You can only cancel your own NFT listings." in str(ex.value)

    assert len(chainEstateMarketplace.fetchMarketItems()) == 1
    chainEstateMarketplace.cancelMarketSale(chainEstateNFT.address, marketItemId, {"from": account5})
    assert len(chainEstateMarketplace.fetchMarketItems()) == 0
    assert account5.balance() == initialAccount5Balance
    
    # Owner can cancel any NFT listing
    initialAccountBalance = account.balance()
    initialAccount5Balance = account5.balance()
    chainEstateNFT.approve(chainEstateMarketplace.address, tokenId, {"from": account5})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, tokenId, NFTPrice, {"from": account5, "value": listingFee})

    marketItemId += 1
    chainEstateMarketplace.cancelMarketSale(chainEstateNFT.address, marketItemId, {"from": account})
    assert chainEstateNFT.ownerOf(tokenId) == account5.address
    assert account.balance() == initialAccountBalance
    assert account5.balance() == initialAccount5Balance

    # Owner can create an NFT and assign a whitelist address to it.
    # Also make sure a non-owner can't assign a whitelist spot.
    listingFee = Web3.toWei(0.06, "ether")
    marketItemId += 1
    chainEstateNFT.createToken("Test Token", 1, listingFee, {"from": account})
    tokenId = chainEstateNFT._tokenIds()

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateNFT.addWhiteListToToken(account2.address, tokenId, {"from": account5})
    assert "revert: Ownable: caller is not the owner" in str(ex.value)

    # Add the whitelist address to the NFT.
    chainEstateNFT.addWhiteListToToken(account2.address, tokenId, {"from": account})
    assert chainEstateNFT.tokenIdToWhitelistAddress(tokenId) == account2.address

    # Put the NFT on the marketplace.
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, tokenId, NFTPrice, {"from": account})

    # Someone who isn't account2 can't purchase the NFT.
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        chainEstateMarketplace.createMarketSale(chainEstateNFT.address, marketItemId, NFTPrice, {"from": account5})
    assert "revert: This NFT has been assigned to someone through a Whitelist spot. Only they can purchase this NFT." in str(ex.value)

    # Account2 can purchase the NFT.
    chainEstateToken.approve(chainEstateMarketplace.address, NFTPrice, {"from": account2})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, marketItemId, NFTPrice, {"from": account2})

    assert chainEstateNFT.ownerOf(tokenId) == account2.address

    # Account2 can put the NFT back on the marketplace.
    chainEstateNFT.approve(chainEstateMarketplace.address, tokenId, {"from": account2})
    chainEstateMarketplace.createMarketItem(chainEstateNFT.address, tokenId, NFTPrice, {"from": account2, "value": listingFee})
    marketItemId += 1

    # Account5 can purchase the NFT spot now that the owner isn't the seller.
    chainEstateToken.approve(chainEstateMarketplace.address, NFTPrice, {"from": account5})
    chainEstateMarketplace.createMarketSale(chainEstateNFT.address, marketItemId, NFTPrice, {"from": account5})

    assert chainEstateNFT.ownerOf(tokenId) == account5.address
