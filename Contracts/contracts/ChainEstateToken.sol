// SPDX-License-Identifier: MIT
 
pragma solidity >=0.8.0 <0.9.0;
 
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/Uniswap.sol";

/**
 * @title Chain Estate DAO Token
 * @dev Main contract for Chain Estate DAO
 * TODO - Limit how many tokens users can purchase from PancakeSwap
 * TODO - Will possibly create the BNB to CHES token PankcakeSwap pair in the constructor.
 */
contract ChainEstateToken is ERC20, Ownable {

    // Mapping to exclude some contracts from fees. Transfers are excluded from fees if address in this mapping is recipient or sender.
    mapping (address => bool) public excludedFromFees;

    // Mapping to determine the timestamp of each address' investment. Earlier average investment = better air drop rewards.
    mapping (address => uint256) public airDropInvestTime;

    // Blacklist mapping to prevent addresses from trading if necessary (i.e. flagged for malicious activity).
    mapping (address => bool) public blacklist;

    // Address of the contract responsible for the air dropping mechanism.
    address public airDropContractAddress;

    // Address of the contract for burning CHES tokens.
    address public burnWalletAddress;

    // Real estate wallet address used to collect funds to purchase real estate.
    address payable public realEstateWalletAddress;

    // Liquidity wallet address used to hold the 30% of CHES tokens for the liquidity pool.
    // After these coins are moved to the DEX, this address will no longer be used.
    address public liquidityWalletAddress;

    // Marketing wallet address used for funding marketing.
    address payable public marketingWalletAddress;

    // Developer wallet address used for funding the team.
    address payable public developerWalletAddress;

    // The PancakeSwap router address for swapping CHES tokens for WBNB.
    address public uniswapRouterAddress;

    // The initial block timestamp of the token contract.
    uint256 public initialTimeStamp;

    // Real estate transaction fee - deployed at 3%.
    uint256 public realEstateTransactionFeePercent = 3;

    // Developer team transaction fee - deployed at 1%.
    uint256 public developerFeePercent = 1;

    // Marketing transaction fee - deployed at 1%.
    uint256 public marketingFeePercent = 1;

    // PancakeSwap router interface.
    IUniswapV2Router02 private uniswapRouter;

    // Address of the WBNB to CHES token pair on PancakeSwap.
    address public uniswapPair;

    // Determines how many CHES tokens this contract needs before it swaps for WBNB to pay fee wallets.
    uint256 public contractCHESDivisor = 1000;

    // Initial token distribution:
    // 35% - Air drop contract
    // 30% - Liquidity pool (6 month lockup period)
    // 20% - Burn
    // 10% - Developer coins (6 month lockup period)
    // 5% - Marketing
    constructor(
        uint256 initialSupply, 
        address _airDropContractAddress, 
        address _burnWalletAddress,
        address _liquidityWalletAddress,
        address payable _realEstateWalletAddress,
        address payable _marketingWalletAddress,
        address payable _developerWalletAddress,
        address _uniswapRouterAddress) ERC20("ChainEstateToken", "CHES") {
            initialTimeStamp = block.timestamp;
            airDropContractAddress = _airDropContractAddress;
            realEstateWalletAddress = _realEstateWalletAddress;
            burnWalletAddress = _burnWalletAddress;
            liquidityWalletAddress = _liquidityWalletAddress;
            marketingWalletAddress = _marketingWalletAddress;
            developerWalletAddress = _developerWalletAddress;
            uniswapRouterAddress = _uniswapRouterAddress;

            excludedFromFees[realEstateWalletAddress] = true;
            excludedFromFees[developerWalletAddress] = true;
            excludedFromFees[marketingWalletAddress] = true;
            excludedFromFees[liquidityWalletAddress] = true;
            excludedFromFees[airDropContractAddress] = true;    // No transaction fees for claiming air drop rewards

            _mint(airDropContractAddress, (initialSupply) * 35 / 100);
            _mint(liquidityWalletAddress, (initialSupply) * 3 / 10);
            _mint(burnWalletAddress, initialSupply / 5);
            _mint(marketingWalletAddress, initialSupply * 5 / 100);
            _mint(developerWalletAddress, initialSupply / 10);

            IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(uniswapRouterAddress);
            uniswapRouter = _uniswapV2Router;
            _approve(address(this), address(uniswapRouter), initialSupply);
            uniswapPair = IUniswapV2Factory(_uniswapV2Router.factory()).createPair(address(this), _uniswapV2Router.WETH());
            IERC20(uniswapPair).approve(address(uniswapRouter), type(uint256).max);
    }

    /**
     * @dev Returns the contract address
     * @return contract address
     */
    function getContractAddress() public view returns (address){
        return address(this);
    }

    /**
    * @dev Adds a user to be excluded from fees.
    * @param user address of the user to be excluded from fees.
     */
    function excludeUserFromFees(address user) public onlyOwner {
        excludedFromFees[user] = true;
    }

    /**
    * @dev Gets the current timestamp, used for testing + verification
    * @return the the timestamp of the current block
     */
    function getCurrentTimestamp() public view returns (uint256) {
        return block.timestamp;
    }

    /**
    * @dev Removes a user from the fee exclusion.
    * @param user address of the user than will now have to pay transaction fees.
     */
    function includeUsersInFees(address user) public onlyOwner {
        excludedFromFees[user] = false;
    }

    /**
     * @dev Overrides the BEP20 transfer function to include transaction fees.
     * @param recipient the recipient of the transfer
     * @param amount the amount to be transfered
     * @return bool representing if the transfer was successful
     */
    function transfer(address recipient, uint256 amount) public override returns (bool) {
        // Ensure the sender isn't blacklisted.
        require(!blacklist[_msgSender()], "You have been blacklisted from trading the CHES token. If you think this is an error, please contact the Chain Estate DAO team.");
        // Ensure the recipient isn't blacklisted.
        require(!blacklist[recipient], "The address you are trying to send CHES to has been blacklisted from trading the CHES token. If you think this is an error, please contact the Chain Estate DAO team.");

        // Stops investors from owning more than 2% of the total supply from purchasing CHES from PancakeSwap.
        if (_msgSender() == uniswapPair && !excludedFromFees[_msgSender()] && !excludedFromFees[recipient]) {
            require((balanceOf(recipient) + amount) < (totalSupply() / 166), "You can't have more than 2% of the total CHES supply after a PancakeSwap swap.");
        }

        // If the sender or recipient is excluded from fees, perform the default transfer.
        if (excludedFromFees[_msgSender()] || excludedFromFees[recipient]) {
            _transfer(_msgSender(), recipient, amount);
            return true;
        }

        // Real estate transaction fee.
        uint256 realEstateFee = (amount * realEstateTransactionFeePercent) / 100;
        // Marketing team transaction fee.
        uint256 marketingFee = (amount * marketingFeePercent) / 100;
        // Developer team transaction fee.
        uint256 developerFee = (amount * developerFeePercent) / 100;

        // The total fee to send to the contract address.
        uint256 totalFee = realEstateFee + marketingFee + developerFee;
 
        // Sends the transaction fees to the contract address
        _transfer(_msgSender(), address(this), totalFee);

        uint256 contractCHESBalance = balanceOf(address(this));

        if (_msgSender() != uniswapPair && contractCHESBalance > 0) {
            if (contractCHESBalance > 0) {
                if (contractCHESBalance > balanceOf(uniswapPair) / contractCHESDivisor) {
                    swapCHESForBNB(contractCHESBalance);
                }
                
            }
            uint256 contractBNBBalance = address(this).balance;
            if (contractBNBBalance > 0) {
                sendFeesToWallets(address(this).balance);
            }
        }
 
        // Sends [initial amount] - [fees] to the recipient
        uint256 valueAfterFees = amount - totalFee;
        _transfer(_msgSender(), recipient, valueAfterFees);
        return true;
    }

    /**
     * @dev Overrides the BEP20 transferFrom function to include transaction fees.
     * @param from the address from where the tokens are coming from
     * @param to the recipient of the transfer
     * @param amount the amount to be transfered
     * @return bool representing if the transfer was successful
     */
    function transferFrom(address from, address to, uint256 amount) public override returns (bool) {
        // If the from address or to address is excluded from fees, perform the default transferFrom.
        if (excludedFromFees[from] || excludedFromFees[to]) {
            _spendAllowance(from, _msgSender(), amount);
            _transfer(from, to, amount);
            return true;
        }

        // Real estate transaction fee.
        uint256 realEstateFee = (amount * realEstateTransactionFeePercent) / 100;
        // Marketing team transaction fee.
        uint256 marketingFee = (amount * marketingFeePercent) / 100;
        // Developer team transaction fee.
        uint256 developerFee = (amount * developerFeePercent) / 100;

        // The total fee to send to the contract address.
        uint256 totalFee = realEstateFee + marketingFee + developerFee;
 
        // Sends the transaction fees to the contract address
        _spendAllowance(from, _msgSender(), amount);
        _transfer(from, address(this), totalFee);

        uint256 contractCHESBalance = balanceOf(address(this));

        if (_msgSender() != uniswapPair && contractCHESBalance > 0) {
            if (contractCHESBalance > 0) {
                if (contractCHESBalance > balanceOf(uniswapPair) / contractCHESDivisor) {
                    swapCHESForBNB(contractCHESBalance);
                }
                
            }
            uint256 contractBNBBalance = address(this).balance;
            if (contractBNBBalance > 0) {
                sendFeesToWallets(address(this).balance);
            }
        }
 
        // Sends [initial amount] - [fees] to the recipient
        uint256 valueAfterFees = amount - totalFee;
        _transfer(from, to, valueAfterFees);
        return true;
    }

    /**
     * @dev Swaps CHES tokens from transaction fees to BNB.
     * @param amount the amount of CHES tokens to swap
     */
    function swapCHESForBNB(uint256 amount) private {
        address[] memory path = new address[](2);
        path[0] = address(this);
        path[1] = uniswapRouter.WETH();
        _approve(address(this), address(uniswapRouter), amount);
        uniswapRouter.swapExactTokensForETHSupportingFeeOnTransferTokens(
            amount,
            0,
            path,
            address(this),
            block.timestamp
        );
    }

    /**
     * @dev Sends BNB to transaction fee wallets after CHES swaps.
     * @param amount the amount to be transfered
     */
    function sendFeesToWallets(uint256 amount) private {
        uint256 totalFee = realEstateTransactionFeePercent + marketingFeePercent + developerFeePercent;
        realEstateWalletAddress.transfer((amount * realEstateTransactionFeePercent) / totalFee);
        marketingWalletAddress.transfer((amount * marketingFeePercent) / totalFee);
        developerWalletAddress.transfer((amount * developerFeePercent) / totalFee);
    }

    /**
     * @dev Sends BNB to transaction fee wallets manually as opposed to happening automatically after a certain level of volume
     */
    function disperseFeesManually() public onlyOwner {
        uint256 contractBNBBalance = address(this).balance;
        sendFeesToWallets(contractBNBBalance);
    }

    /**
     * @dev Swaps all CHES tokens in the contract for BNB and then disperses those funds to the transaction fee wallets.
     */
    function swapCHESForBNBManually() public onlyOwner {
        uint256 contractCHESBalance = balanceOf(address(this));
        swapCHESForBNB(contractCHESBalance);
        uint256 contractBNBBalance = address(this).balance;
        sendFeesToWallets(contractBNBBalance);
    }

    receive() external payable {}

    /**
     * @dev Sets the value that determines how many CHES tokens need to be in the contract before it's swapped for BNB.
     * @param newDivisor the new divisor value to determine the swap threshold
     */
    function setContractCHESDivisor(uint256 newDivisor) public onlyOwner {
        contractCHESDivisor = newDivisor;
    }

    /**
     * @dev After a token transfer, update the recipient address's air drop invest time since they have a later investment now.
     * @param from the sender's address
     * @param to the recipient's address
     * @param value the amount that was transferred
     */
    function _afterTokenTransfer(address from, address to, uint256 value) internal virtual override {
        uint256 userBalance = balanceOf(to);
        airDropInvestTime[to] = (value * block.timestamp + (userBalance - value) * airDropInvestTime[to]) / userBalance;
        super._afterTokenTransfer(from, to, value);
    }
}