from web3 import Web3
import solcx, os

CONTRACT_SOURCE_CODE = '''
pragma solidity ^0.8.0;

import "./node_modules/@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "./node_modules/@openzeppelin/contracts/utils/Counters.sol";
import "./node_modules/@openzeppelin/contracts/access/Ownable.sol";
import "./node_modules/@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

contract GameItem is ERC721URIStorage, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    constructor() ERC721("GameItem", "ITM") {}

    function awardItem(address player, string memory tokenURI)
        public onlyOwner
        returns (uint256)
    {
        _tokenIds.increment();

        uint256 newItemId = _tokenIds.current();
        _mint(player, newItemId);
        _setTokenURI(newItemId, tokenURI);

        return newItemId;
    }
}
'''

EVMOS_TESTNET_RPC_URL = 'https://eth.bd.evmos.dev:8545'

SENDER_PRIVATE_KEY = "8d18540517b9943727b325fd5e5a2a04707640607cd76737b9e36887dd2ae124"
SENDER_ADDRESS = "0xCb7d5FDEe94Ac56fc758eE60C6F25564e7010144"

RECIPIENT_ADDRESS = "0x0d70E1D117fc9135812657dE01EC8237E8204190"

class GameItem:
    def __init__(self, pubKey, privKey):
        self.pubKey = pubKey
        self.privKey = privKey
        if len(solcx.get_installed_solc_versions()) == 0:
            print("Installing solc 0.8.14...")
            solcx.install_solc(version='0.8.14')
            solcx.set_solc_version('0.8.14')
        compiled_sol = solcx.compile_source(
            CONTRACT_SOURCE_CODE,
            base_path=os.getcwd(),
            output_values=['abi', 'bin'])
        contract_interface = compiled_sol['<stdin>:GameItem']
        self.w3 = Web3(Web3.HTTPProvider(EVMOS_TESTNET_RPC_URL))
        GameItem = self.w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
        tx_data = GameItem.constructor()
        tx_receipt = self._send_tx(tx_data, self.pubKey, self.privKey)
        self.game_item = self.w3.eth.contract(
            address=tx_receipt.contractAddress,
            abi=contract_interface['abi'],
        )
        print("GameItem contract address: ", tx_receipt.contractAddress)

    def _send_tx(self, tx_data, fromAddress, fromPrivKey):
        tx = tx_data.buildTransaction(
            {
                'from': fromAddress,
                'nonce': self.w3.eth.get_transaction_count(fromAddress),
            }
        )
        signed_tx = self.w3.eth.account.sign_transaction(tx, fromPrivKey)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def award_item(self, playerAddress, tokenURI):
        tx_data = self.game_item.functions.awardItem(playerAddress, tokenURI)
        tx_receipt = self._send_tx(tx_data, self.pubKey, self.privKey)
        return self.game_item.events.Transfer().processReceipt(tx_receipt)[0].args.tokenId

    def transfer_from(self, fromAddress, fromPrivKey, toAddress, tokenID):
        tx_data = self.game_item.functions.transferFrom(fromAddress, toAddress, tokenID)
        self._send_tx(tx_data, fromAddress, fromPrivKey)

    def owner_of(self, tokenID):
        return self.game_item.functions.ownerOf(tokenID).call()


if __name__ == "__main__":
    game_item = GameItem(SENDER_ADDRESS, SENDER_PRIVATE_KEY)

    tokenID = game_item.award_item(SENDER_ADDRESS, "https://example.com/example-token")
    assert game_item.owner_of(tokenID) == SENDER_ADDRESS

    game_item.transfer_from(SENDER_ADDRESS, SENDER_PRIVATE_KEY, RECIPIENT_ADDRESS, tokenID)
    assert game_item.owner_of(tokenID) == RECIPIENT_ADDRESS
