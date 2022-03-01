from brownie import network, config, ChainEstateToken, ChainEstateAirDrop, ChainEstatePolling, MockWETH, PancakeRouter, PancakePair, PancakeFactory
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from web3 import Web3

INITIAL_SUPPLY = Web3.toWei(1000000000, "ether")

PROD_REAL_ESTATE_ADDRESS = "0x965C421073f0aD56a11b2E3aFB80C451038F6178"
PROD_MARKETING_ADDRESS = "0x4abAc87EeC0AD0932B71037b5d1fc88B7aC2Defd"
PROD_DEVELOPER_ADDRESS = "0x9406B17dE6949aB3F32e7c6044b0b29e1987f9ab"
PROD_LIQUIDITY_ADDRESS = "0xB164Eb7844F3A05Fd3eF01CF05Ac4961a74D47fF"
BURN_ADDRESS = "0x000000000000000000000000000000000000dEaD"

PROD = False

def deploy_chain_estate(realEstateWalletAddress=None, marketingWalletAddress=None, developerWalletAddress=None, liquidityWalletAddress=None, burnWalletAddress=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD and currNetwork in config["networks"] and "pancakeswap_router" in config["networks"][currNetwork]:
        realEstateWalletAddress = PROD_REAL_ESTATE_ADDRESS
        marketingWalletAddress = PROD_MARKETING_ADDRESS
        developerWalletAddress = PROD_DEVELOPER_ADDRESS
        liquidityWalletAddress = PROD_LIQUIDITY_ADDRESS
        burnWalletAddress = BURN_ADDRESS
    else:
        if not realEstateWalletAddress:
            realEstateWalletAddress = account.address
        if not marketingWalletAddress:
            marketingWalletAddress = account.address
        if not developerWalletAddress:
            developerWalletAddress = account.address
        if not liquidityWalletAddress:
            liquidityWalletAddress = account.address
        if not burnWalletAddress:
            # 0x000000000000000000000000000000000000dEaD is a standard burn wallet address.
            burnWalletAddress = BURN_ADDRESS

    if currNetwork in config["networks"] and "pancakeswap_router" in config["networks"][currNetwork]:
        pancakeSwapRouterAddress = config["networks"][currNetwork]["pancakeswap_router"]
    else:
        # Deploy mocked PancakeSwap router and factory.
        WETHAddress = MockWETH.deploy({"from": account})
        pancakeSwapFactoryAddress = PancakeFactory.deploy(account.address, {"from": account})
        pancakeSwapRouterAddress = PancakeRouter.deploy(pancakeSwapFactoryAddress, WETHAddress, {"from": account})


    publishSource = currNetwork not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    chainEstateAirDrop = ChainEstateAirDrop.deploy({"from": account}, publish_source=publishSource)
    if type(chainEstateAirDrop) == 'TransactionReceipt':
        print(dir(chainEstateAirDrop))
        chainEstateAirDrop.wait(1)
        chainEstateAirDrop = chainEstateAirDrop.return_value
    
    print(f"Chain Estate air drop deployed to {chainEstateAirDrop.address}")
    chainEstateToken = ChainEstateToken.deploy(
        INITIAL_SUPPLY,
        chainEstateAirDrop.address,
        burnWalletAddress,
        liquidityWalletAddress,
        realEstateWalletAddress,
        marketingWalletAddress,
        developerWalletAddress,
        pancakeSwapRouterAddress,
        {"from": account},
        publish_source=publishSource
    )

    if type(chainEstateToken) == 'TransactionReceipt':
        chainEstateToken.wait(1)
        chainEstateToken = chainEstateToken.return_value

    print(f"Chain Estate Token deployed to {chainEstateToken.address}")

    chainEstatePolling = ChainEstatePolling.deploy(chainEstateToken.address, {"from": account}, publish_source=publishSource)
    transaction = chainEstateAirDrop.setToken(chainEstateToken.address, {"from": account})
    transaction.wait(1)
    print("Successfully set the CHES token for the air drop.")

    return chainEstateToken, chainEstateAirDrop, chainEstatePolling

def main():
    deploy_chain_estate()