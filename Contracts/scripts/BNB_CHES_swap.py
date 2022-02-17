from brownie import network, interface
from scripts.common_funcs import retrieve_account
import datetime

UNISWAP_ROUTER_ADDRESS = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
RINKEBY_WETH_ADDRESS = "0xc778417E063141139Fce010982780140Aa0cD5Ab"
RINKEBY_DAI_ADDRESS = "0x5592EC0cfb4dbc12D3aB100b257153436a1f0FEa"
RINKEBY_CHAINLINK_ADDRESS = "0x01BE23585060835E02B77ef475b0Cc51aA1e0709"
ACCOUNT_ADDRESS = "0xC00005f9a29AcA2c2462c8a548fAAF8d1c761cB9"
POOL_FEE_005_PERCENT = 500
POOL_FEE_03_PERCENT = 3000
POOL_FEE_1_PERCENT = 10000
DEADLINE = int((datetime.datetime.now() + datetime.timedelta(minutes=10)).timestamp())

def swap_CHES_for_BNB():
    account = retrieve_account()

    WETHContract = interface.IERC20(RINKEBY_WETH_ADDRESS)
    WETHContract.approve(UNISWAP_ROUTER_ADDRESS, 10000000000000000, {"from": account})

    uniswapRouter = interface.ISwapRouter(UNISWAP_ROUTER_ADDRESS)
    print("Got the Uniswap router.")

    uniswapRouter.exactInputSingle([
        RINKEBY_WETH_ADDRESS, RINKEBY_DAI_ADDRESS, POOL_FEE_03_PERCENT,
        account, DEADLINE, 10000000000000000, 0, 0
    ], {"from": account})

    print("Ran a swap.")

def main():
    swap_CHES_for_BNB()


'''
struct ExactInputSingleParams {
    address tokenIn = 0xc778417E063141139Fce010982780140Aa0cD5Ab
    address tokenOut = 0x5592EC0cfb4dbc12D3aB100b257153436a1f0FEa
    uint24 fee = 1
    address recipient = 0xC00005f9a29AcA2c2462c8a548fAAF8d1c761cB9
    uint256 deadline = datetime.datetime.now() + datetime.timedelta(minutes=10)
    uint256 amountIn = 1
    uint256 amountOutMinimum = 0
    uint160 sqrtPriceLimitX96 = 0
}
'''

'''
{
    "tokenIn": RINKEBY_WETH_ADDRESS,
    "tokenOut": RINKEBY_DAI_ADDRESS,
    "fee": 1,
    "recipient": ACCOUNT_ADDRESS,
    "deadline": DEADLINE,
    "amountIn": 1,
    "amountOutMinimum": 0,
    "sqrtPriceLimitX96": 0
}
'''