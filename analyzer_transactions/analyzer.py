import json
import sys
import os
from typing import List, Dict, Any, Optional, AsyncGenerator

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from web3 import Web3, AsyncWeb3, AsyncHTTPProvider
from web3.types import HexBytes
from eth_abi import decode
from eth_utils import decode_hex
from abis import uniswap_v3_router_abi, uniswap_v2_router_abi
from redis.asyncio import Redis
import redis.asyncio as aioredis
from analyzer_transactions import logger
from analyzer_transactions.node_limiter import NodeRateLimiter
from dotenv import load_dotenv

load_dotenv()


class AnalyzerTransactions:
    # List of methods considered swap operations or related to liquidity
    SWAP_METHODS: List[str] = [
        # Uniswap V2
        "swapExactETHForTokens",
        "swapExactTokensForETH",
        "swapExactTokensForTokens",
        # "addLiquidity",
        # "addLiquidityETH",
        # "removeLiquidity",
        # "removeLiquidityETHWithPermit",
        # Uniswap V3
        "exactInputSingle",
        "exactInput",
        "exactOutputSingle",
        "exactOutput",
        # "multicall"
    ]

    def __init__(self, rpc_url: str) -> None:
        logger.warning(rpc_url)
        """Initialize the AnalyzerTransactions with Web3 and ABI configurations."""
        self.w3_async: AsyncWeb3 = AsyncWeb3(AsyncHTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
        self.w3: Web3 = Web3()  # Synchronous Web3 for Keccak computation
        self.logger: Any = logger  # Logger instance (type not specified due to external module)
        self.ABI_SWAP: List[List[Dict[str, Any]]] = [uniswap_v2_router_abi, uniswap_v3_router_abi]
        if not any(self.ABI_SWAP):
            self.logger.error("ABI_SWAP is empty, cannot generate signatures")
            raise ValueError("ABI_SWAP is empty")
        self.SIGNATURES_SWAP: List[Dict[str, Any]] = self._generate_swap_signatures()
        self.REDIS_URL = os.getenv('REDIS_URL')
        if self.REDIS_URL is None:
            raise ValueError("REDIS_URL is not set")
        self.TRANSACTION_TTL = os.getenv('TRANSACTION_TTL', 3600)

    def _generate_swap_signatures(self) -> List[Dict[str, Any]]:
        """Generate method signatures for swap and liquidity operations from ABI.

        Returns:
            List of dictionaries containing signature and corresponding ABI item.
        """
        signatures: List[Dict[str, Any]] = []
        for abi in self.ABI_SWAP:  # Iterate over each ABI (V2 and V3)
            for item in abi:  # Iterate over ABI items
                if not isinstance(item, dict):  # Skip non-dictionary items
                    continue
                if item.get("type") == "function" and item.get("name") in self.SWAP_METHODS:
                    # Form the signature string: method_name(type1,type2,...)
                    inputs: List[Dict[str, str]] = item.get("inputs", [])
                    param_types: str = ",".join([param["type"] for param in inputs])
                    signature: str = f"{item['name']}({param_types})"
                    
                    # Compute Keccak-256 hash and take the first 4 bytes
                    keccak_hash: bytes = self.w3.keccak(text=signature)
                    signature_hex: str = "0x" + keccak_hash.hex()[:8]
                    signatures.append({
                        "signature": signature_hex,
                        "abi_item": item
                    })
                    # self.logger.debug(f"Signature for {signature}: {signature_hex}")
        
        if not signatures:
            self.logger.warning("Failed to generate signatures: SIGNATURES_SWAP is empty")
        return signatures

    def _find_and_decode_method(self, input_tx: str) -> Optional[Dict[str, Any]]:
        """Find method by input_tx signature and decode its data.

        Args:
            input_tx: Transaction input data (hex string).

        Returns:
            Dictionary with method name and decoded parameters, or None if not found.
        """
        if input_tx == "0x" or len(input_tx) < 10:
            self.logger.debug("Empty or too short input_tx")
            return None

        signature: str = input_tx[:10]
        data: str = input_tx[10:]

        for item in self.SIGNATURES_SWAP:
            if item["signature"] == signature:
                abi_item: Dict[str, Any] = item["abi_item"]
                try:
                    decoded_params: tuple = decode(
                        [param["type"] for param in abi_item["inputs"]],
                        decode_hex(data)
                    )
                    decoded_dict: Dict[str, Any] = {
                        param["name"]: value for param, value in zip(abi_item["inputs"], decoded_params)
                    }
                    return {
                        "method": abi_item["name"],
                        "params": decoded_dict
                    }
                except Exception as e:
                    self.logger.error(f"Error decoding input for method {abi_item['name']}: {e}")
                    return None
        
        self.logger.debug(f"Method with signature {signature} not found")
        return None

    async def initialize(self) -> None:
        """Initialize connection to Ethereum node."""
        if await self.w3_async.is_connected():
            chain_id: int = await self.w3_async.eth.chain_id
            self.logger.info(f"Connected to Ethereum node, chain ID: {chain_id}")
        else:
            self.logger.error("Failed to connect to Ethereum node")
            sys.exit(1)
    
    async def close(self) -> None:
        """Close the HTTP session."""
        session: Optional[Any] = getattr(self.w3_async.provider, "_session", None)
        if session and not session.closed:
            await session.close()
            self.logger.info("HTTP session closed successfully")

    async def __aenter__(self) -> 'AnalyzerTransactions':
        """Enter the async context manager."""
        await self.initialize()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit the async context manager."""
        await self.close()

    async def _get_block_limited(self, block_number: int) -> Dict[str, Any]:
        """Fetch a block with limited retries.

        Args:
            block_number: Block number to fetch.

        Returns:
            Block data as a dictionary.
        """
        return await self._get_block(block_number)

    async def _get_block(self, block_number: int) -> Dict[str, Any]:
        """Fetch a block with full transactions.

        Args:
            block_number: Block number to fetch.

        Returns:
            Block data as a dictionary.
        """
        return await self.w3_async.eth.get_block(block_number, full_transactions=True)

    async def get_last_n_blocks(self, depth_blocks: int) -> List[Dict[str, Any]]:
        """Fetch the last N blocks.

        Args:
            depth_blocks: Number of blocks to fetch.

        Returns:
            List of block data dictionaries.
        """
        try:
            if not isinstance(depth_blocks, int) or depth_blocks <= 0:
                self.logger.error("depth_blocks must be a positive integer")
                raise ValueError("depth_blocks must be a positive integer")

            MAX_BLOCKS_PER_REQUEST: int = 100
            if depth_blocks > MAX_BLOCKS_PER_REQUEST:
                self.logger.warning(f"depth_blocks exceeds {MAX_BLOCKS_PER_REQUEST}, limiting to {MAX_BLOCKS_PER_REQUEST}")
                depth_blocks = MAX_BLOCKS_PER_REQUEST

            latest_block: int = await self.w3_async.eth.block_number
            start_block: int = latest_block - depth_blocks + 1
            block_numbers: List[int] = list(range(start_block, latest_block + 1))

            self.logger.info(f"Fetching blocks: {block_numbers[0]} — {block_numbers[-1]}")

            tasks: List[Any] = [self._get_block_limited(num) for num in block_numbers]
            data_blocks: List[Dict[str, Any]] = await asyncio.gather(*tasks)

            return data_blocks

        except Exception as e:
            self.logger.error(f"Error fetching blocks: {e}")
            return []

    async def get_slice_blocks(self, start_block: int, latest_block: int) -> List[Dict[str, Any]]:
        """Fetch the last N blocks.

        Args:
            depth_blocks: Number of blocks to fetch.

        Returns:
            List of block data dictionaries.
        """
        try:


            if not isinstance(start_block, int) or start_block <= 0:
                self.logger.error("start_block must be a positive integer")
            if not isinstance(latest_block, int) or start_block <= 0:
                self.logger.error("latest_block must be a positive integer")
                raise ValueError("latest_block must be a positive integer")
            if start_block > latest_block:
                self.logger.error("start_block must be less than or equal to latest_block")
                raise ValueError("start_block must be less than or equal to latest_block")

            len_blocks: int = latest_block - start_block

            MAX_BLOCKS_PER_REQUEST: int = 100
            if len_blocks > MAX_BLOCKS_PER_REQUEST:
                self.logger.warning(f"len_blocks exceeds {MAX_BLOCKS_PER_REQUEST}, limiting to {MAX_BLOCKS_PER_REQUEST}")
                len_blocks = MAX_BLOCKS_PER_REQUEST

            block_numbers: List[int] = list(range(start_block, latest_block + 1))

            self.logger.info(f"Fetching blocks: {block_numbers[0]} — {block_numbers[-1]}")

            tasks: List[Any] = [self._get_block_limited(num) for num in block_numbers]
            data_blocks: List[Dict[str, Any]] = await asyncio.gather(*tasks)

            return data_blocks

        except Exception as e:
            self.logger.error(f"Error fetching blocks: {e}")
            return []

    async def extract_transactions(self, data_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract all transactions from a list of blocks.

        Args:
            data_blocks: List of block data dictionaries.

        Returns:
            List of transaction dictionaries.
        """
        transactions: List[Dict[str, Any]] = []
        for block in data_blocks:
            transactions.extend(block["transactions"])
            self.logger.debug(f"Extracted {len(block['transactions'])} transactions from block {block['number']}")
        return transactions

    async def _extract_inputs(self, tx: Dict[str, Any]) -> str:
        """Extract the input field from a transaction.

        Args:
            tx: Transaction dictionary.

        Returns:
            Input data as a hex string.
        """
        if "input" not in tx or not tx["input"]:
            return "0x"
        return "0x" + tx["input"].hex()

    async def detect_swap_tx(self, input_tx: str) -> bool:
        """Check if a transaction is a swap operation.

        Args:
            input_tx: Transaction input data (hex string).

        Returns:
            True if the transaction is a swap operation, False otherwise.
        """
        if input_tx == "0x" or len(input_tx) < 10:
            return False
        return any(item["signature"] == input_tx[:10] for item in self.SIGNATURES_SWAP)

    async def filter_transactions(self, txs: List[Dict[str, Any]]) -> AsyncGenerator[Dict[str, Any], None]:
        """Filter transactions, keeping only swap operations.

        Args:
            txs: List of transaction dictionaries.

        Yields:
            Transaction dictionaries that are swap operations.
        """
        for tx in txs:
            tx_hash = "0x" + tx["hash"].hex()
            if tx.get("to") == "0x0000000000000000000000000000000000000000":
                self.logger.debug(f"Skipped transaction {tx_hash}: to=0x0")
                continue
            
            input_tx: str = await self._extract_inputs(tx)
            if not await self.detect_swap_tx(input_tx):
                # self.logger.debug(f"Skipped transaction {tx_hash}: not a swap operation")
                continue

            self.logger.debug(f"Transaction {tx_hash} passed filtering (swap)")
            yield tx

    async def decode_input_data(self, input_tx: str) -> Optional[Dict[str, Any]]:
        """Decode transaction input data.

        Args:
            input_tx: Transaction input data (hex string).

        Returns:
            Decoded input data as a dictionary, or None if decoding fails.
        """
        return self._find_and_decode_method(input_tx)

    async def save_to_redis(self, tx_data: Dict[str, Any]) -> None:
        try:
            redis = aioredis.from_url(self.REDIS_URL)
            
            def serialize_value(value):
                if isinstance(value, bytes):
                    return value.hex()
                elif hasattr(value, 'hex'):  
                    return value.hex()
                return str(value)
            
            def deep_serialize(obj):
                if isinstance(obj, dict):
                    return {k: deep_serialize(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [deep_serialize(item) for item in obj]
                return serialize_value(obj)
            
            serializable_tx = deep_serialize(tx_data)
            
            # Улучшенное извлечение хеша с приоритетом
            hash_candidates = [
                serializable_tx.get('hash'),
                serializable_tx.get('transactionHash'),
                serializable_tx.get('tx_hash')
            ]
            
            tx_hash = next((h for h in hash_candidates if h), 'unknown_hash')
            
            # Гарантированное добавление '0x'
            tx_hash = tx_hash if tx_hash.startswith('0x') else f'0x{tx_hash}'
            
            redis_key = f"tx:{tx_hash}"
            
            serialized_data = json.dumps(
                serializable_tx, 
                ensure_ascii=False, 
            )
            serializable_tx
            # Сохранение с возможностью настройки TTL
            await redis.setex(
                redis_key, 
                self.TRANSACTION_TTL,  # Вынести TTL в константу класса
                serialized_data
            )
            
            # Расширенное логирование
            logger.info(
                f"Транзакция сохранена: {redis_key}, "
                f"Размер: {len(serialized_data)} байт"
            )
            
            # Опциональная проверка сохранения
            if not await redis.exists(redis_key):
                logger.warning(f"Возможная проблема сохранения: {redis_key}")

        except Exception as e:
            logger.error(
                f"Ошибка сохранения транзакции: {e}", 
                extra={
                    'tx_hash': tx_hash,
                    'data_size': len(serialized_data) if 'serialized_data' in locals() else 0
                }
            )
            # Вывод трассировки только в DEBUG режиме
            if logger.getEffectiveLevel() == logger.DEBUG:
                import traceback
                traceback.print_exc()


    async def get_transaction_data(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Add decoded input data to a transaction.

        Args:
            tx: Transaction dictionary.

        Returns:
            Transaction dictionary with decoded input data.
        """
        tx_data: Dict[str, Any] = dict(tx)  # Create a copy to avoid modifying the original
        input_tx: str = await self._extract_inputs(tx)
        tx_data["decoded_input"] = await self.decode_input_data(input_tx)
        logger.debug(tx_data)

        # Сохранение в Redis для db_worker
        try:
            redis = aioredis.from_url(self.REDIS_URL)
            await redis.ping()
            logger.debug(f"Успешное подключение к Redis по адресу {self.REDIS_URL}")
        except Exception as e:
            logger.error(f"Ошибка подключения к Redis: {e}")
            raise

        await self.save_to_redis(tx_data)

        return tx_data
    
    async def convert_to_dict(self, txs: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """Convert a list of transactions to a dictionary with 1-based indices.

        Args:
            txs: List of transaction dictionaries.

        Returns:
            Dictionary mapping indices (starting from 1) to transactions.
        """
        result_dict: Dict[int, Dict[str, Any]] = {index + 1: tx for index, tx in enumerate(txs)}
        return result_dict

async def analyzer_main(depth_blocks: int, redis_url: str = os.getenv('REDIS_URL', 'redis://redis:6379/0')) -> list[Dict[str, Any]]:
    """Main function to analyze transactions using NodeRateLimiter."""
    logger.debug(f"Using redis_url: {redis_url}")
    node_url = await NodeRateLimiter(redis_url).get_available_node()
    logger.info(f"NodeRateLimiter initialized. Using {node_url}")

    async with AnalyzerTransactions(node_url) as analyzer:
        logger.debug(f"Generated swap signatures: {[item['signature'] for item in analyzer.SIGNATURES_SWAP]}")
        data_blocks = await analyzer.get_last_n_blocks(depth_blocks)
        logger.success(f"Received data for {len(data_blocks)} blocks")
        txs = await analyzer.extract_transactions(data_blocks)
        logger.debug(f"Count of transactions: {len(txs)} in {depth_blocks} blocks")
        filtered_txs = [tx async for tx in analyzer.filter_transactions(txs)]
        logger.warning(f"Count of filtered transactions (SWAP): {len(filtered_txs)}")
        result_list_txs = await asyncio.gather(
            *[analyzer.get_transaction_data(tx) for tx in filtered_txs],
            return_exceptions=True
        )
        list_decode_txs = [tx for tx in result_list_txs if not isinstance(tx, Exception)]
        logger.warning(f"Decoded {len(list_decode_txs)} transactions")
        return list_decode_txs

async def analyzer_main(depth_blocks: int, redis_url: str = os.getenv('REDIS_URL', 'redis://redis:6379/0')) -> list[Dict[str, Any]]:
    """Main function to analyze transactions using NodeRateLimiter."""
    logger.debug(f"Using redis_url: {redis_url}")
    node_url = await NodeRateLimiter(redis_url).get_available_node()
    logger.info(f"NodeRateLimiter initialized. Using {node_url}")

    async with AnalyzerTransactions(node_url) as analyzer:
        logger.debug(f"Generated swap signatures: {[item['signature'] for item in analyzer.SIGNATURES_SWAP]}")
        data_blocks = await analyzer.get_last_n_blocks(depth_blocks)
        logger.success(f"Received data for {len(data_blocks)} blocks")
        txs = await analyzer.extract_transactions(data_blocks)
        logger.debug(f"Count of transactions: {len(txs)} in {depth_blocks} blocks")
        filtered_txs = [tx async for tx in analyzer.filter_transactions(txs)]
        logger.warning(f"Count of filtered transactions (SWAP): {len(filtered_txs)}")
        result_list_txs = await asyncio.gather(
            *[analyzer.get_transaction_data(tx) for tx in filtered_txs],
            return_exceptions=True
        )
        list_decode_txs = [tx for tx in result_list_txs if not isinstance(tx, Exception)]
        logger.warning(f"Decoded {len(list_decode_txs)} transactions")
        return list_decode_txs

async def analyzer_slice_main(start_block: int, last_block: int, redis_url: str = os.getenv('REDIS_URL', 'redis://redis:6379/0')) -> list[Dict[str, Any]]:
    """Main function to analyze transactions using NodeRateLimiter."""
    logger.debug(f"Using redis_url: {redis_url}")
    node_url = await NodeRateLimiter(redis_url).get_available_node()
    logger.info(f"NodeRateLimiter initialized. Using {node_url}")

    async with AnalyzerTransactions(node_url) as analyzer:
        logger.debug(f"Generated swap signatures: {[item['signature'] for item in analyzer.SIGNATURES_SWAP]}")
        data_blocks = await analyzer.get_slice_blocks(start_block, last_block)
        logger.success(f"Received data for {len(data_blocks)} blocks")
        txs = await analyzer.extract_transactions(data_blocks)
        len_blocks = len(data_blocks)
        logger.debug(f"Count of transactions: {len(txs)} in {len_blocks} blocks")
        filtered_txs = [tx async for tx in analyzer.filter_transactions(txs)]
        logger.warning(f"Count of filtered transactions (SWAP): {len(filtered_txs)}")
        result_list_txs = await asyncio.gather(
            *[analyzer.get_transaction_data(tx) for tx in filtered_txs],
            return_exceptions=True
        )
        list_decode_txs = [tx for tx in result_list_txs if not isinstance(tx, Exception)]
        logger.warning(f"Decoded {len(list_decode_txs)} transactions")
        return list_decode_txs

if __name__ == "__main__":
    # Note: Calling 'main' but function is named 'analyzermain'; kept as is per instruction
    # asyncio.run(analyzer_main(3))
    asyncio.run(analyzer_slice_main(22324710, 22324715))