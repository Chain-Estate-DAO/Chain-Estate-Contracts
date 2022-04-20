from brownie import network, config, accounts
import time

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]
DONT_PUBLISH_SOURCE_ENVIRONMENTS = ["development", "ganache-local", "rinkeby"]

DECIMALS = 18

def retrieve_account(accountNum=1):
    if network.show_active() == "development":
        return accounts[accountNum - 1]
    else:
        fromKeyNum = f"_{accountNum}" if accountNum != 1 else ""
        return accounts.add(config["wallets"][f"from_key{fromKeyNum}"])

def waitForTransactionsToComplete():
    time.sleep(0.1)