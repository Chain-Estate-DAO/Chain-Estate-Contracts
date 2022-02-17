# https://api.covalenthq.com/v1/56/events/address/0x2170ed0880ac9a755fd29b2688956bd959f933f8/?starting-block=12115107&ending-block=12240004&key=ckey_2f00368188254ee398a35aacb89

# Get latest block - https://api.covalenthq.com/v1/56/block_v2/latest/?key=ckey_2f00368188254ee398a35aacb89

from web3 import Web3
import requests
import time
import json
import os

API_KEY = "ckey_2f00368188254ee398a35aacb89"
CHAIN_ID = 56
CONTRACT_ADDRESS = "0x2170ed0880ac9a755fd29b2688956bd959f933f8"
CONTRACT_ABI = '[{"inputs": [{"internalType": "address","name": "account","type": "address"}],"name": "balanceOf","outputs": [{"internalType": "uint256","name": "","type": "uint256"}],"stateMutability": "view","type": "function"}]'
BINANCE_RPC_URL = "https://bsc-dataseed.binance.org/"

def main():
    provider = Web3.HTTPProvider(BINANCE_RPC_URL)
    w3 = Web3(provider)
    token = w3.eth.contract(address=Web3.toChecksumAddress(CONTRACT_ADDRESS), abi=CONTRACT_ABI)


    if not os.path.exists("tracker.json"):
        with open("tracker.json", "w") as jsonFile:
            json.dump({"lastBlockHeight": 0, "balances": {}, "brackets": {}, "transfers": [], "uniqueHashes": []}, jsonFile)

    loop = True
    while loop:
        loop = False
        response = requests.get(f"https://api.covalenthq.com/v1/56/block_v2/latest/?key={API_KEY}")
        responseJson = response.json()

        if responseJson["error"]:
            print("Error getting block height.")
            continue

        with open("tracker.json", "r") as trackerFile:
            tracker = json.load(trackerFile)

        blockHeight = int(responseJson["data"]["items"][0]["height"])
        startingBlock = tracker["lastBlockHeight"] if tracker["lastBlockHeight"] >= blockHeight - 10000 else blockHeight - 10000
        tracker["lastBlockHeight"] = blockHeight

        print(f"Block height: {blockHeight}")
        
        requestURL = f"https://api.covalenthq.com/v1/{CHAIN_ID}/events/address/{CONTRACT_ADDRESS}/?starting-block={startingBlock}&ending-block={blockHeight}&key={API_KEY}"
        print(requestURL)
        response = requests.get(requestURL)
        eventLogs = response.json()

        if eventLogs["error"]:
            print("Error getting event logs.")
            continue

        events = eventLogs["data"]["items"]
        for event in events:
            transactionHash = event["tx_hash"]
            blockTimeStamp = event["block_signed_at"]
            params = event["decoded"]["params"]
            sender = params[0]["value"]
            receiver = params[1]["value"]
            value = params[2]["value"]
            uniqueHash = f"{transactionHash}|{sender}|{receiver}|{value}"
            eventName = event["decoded"]["name"]

            if eventName == "Transfer" and uniqueHash not in tracker["uniqueHashes"]:
                senderTokenBalance = token.functions.balanceOf(Web3.toChecksumAddress(sender)).call()
                tracker["balances"][sender] = senderTokenBalance

                receiverTokenBalance = token.functions.balanceOf(Web3.toChecksumAddress(receiver)).call()
                tracker["balances"][receiver] = receiverTokenBalance

                tracker["transfers"].append({"sender": sender, "receiver": receiver, "blockTimeStamp": blockTimeStamp, "transactionHash": transactionHash, "value": value})
                tracker["uniqueHashes"].append(uniqueHash)

        tracker["brackets"] = {}
        balances = tracker["balances"].values()
        maxBalance = max(balances)
        numDigits = len(str(maxBalance)) - 1
        startingDigits = 4
        currDigits = startingDigits
        startingNum = int("1" + "0"*currDigits)
        endingNum = int("1" + "0"*numDigits)
        
        while currDigits <= numDigits:
            currNum = int("1" + "0"*currDigits)
            valRange = f"less than {currNum:,}" if currDigits == startingDigits else f"{currNum:,}+" if currDigits == numDigits else f"{currNum:,} - {int(str(currNum) + '0'):,}"
            tracker["brackets"][valRange] = 0
            currDigits += 1

        for balance in balances:
            if balance < startingNum and balance != 0:
                tracker["brackets"][f"less than {startingNum:,}"] += 1
            elif balance >= endingNum:
                tracker["brackets"][f"{endingNum:,}+"] += 1
            else:
                for bracket in [b for b in tracker["brackets"].keys() if b not in [f"less than {startingNum:,}", f"{endingNum:,}+"]]:
                    bottom = int(bracket.split(" - ")[0].replace(",", ""))
                    top = int(bracket.split(" - ")[1].replace(",", ""))

                    if balance >= bottom and balance < top:
                        tracker["brackets"][bracket] += 1
                        break

        with open("tracker.json", "w") as trackerFile:
            json.dump(tracker, trackerFile)

        print(f"Number of transactions: {len(tracker['uniqueHashes'])}")

        # time.sleep(5)

if __name__ == "__main__":
    main()