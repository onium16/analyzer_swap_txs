import json
import os

# Получаем путь к текущей директории abis/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Функция для загрузки ABI из JSON-файла
def load_abi(file_name: str):
    file_path = os.path.join(BASE_DIR, file_name)
    with open(file_path, 'r') as f:
        return json.load(f)

# Загрузка всех ABI
uniswap_v2_factory_abi = load_abi('uniswap_v2_factory_abi.json')
uniswap_v3_factory_abi = load_abi('uniswap_v3_factory_abi.json')
sushiswap_factory_abi = load_abi('sushiswap_factory_abi.json')
pancakeswap_factory_abi = load_abi('pancakeswap_factory_abi.json')
universal_uniswap_v2_factory_abi = load_abi('universal_uniswap_v2_factory_abi.json')
pancake_pair_abi = load_abi('pancake_pair_abi.json')
uniswap_v3_pool_abi = load_abi('uniswap_v3_pool_abi.json')
erc20_abi = load_abi('erc20_abi.json')
uniswap_v2_router_abi = load_abi('uniswap_v2_router_abi.json')
uniswap_v2_pair_abi = load_abi('uniswap_v2_pair_abi.json')
uniswap_v3_router_abi = load_abi('uniswap_v3_router_abi.json')
uniswap_v3_quoter_abi = load_abi('uniswap_v3_quoter_abi.json')

# Экспорт всех ABI для использования в других модулях
__all__ = [
    'uniswap_v2_factory_abi',
    'uniswap_v3_factory_abi',
    'sushiswap_factory_abi',
    'pancakeswap_factory_abi',
    'universal_uniswap_v2_factory_abi',
    'pancake_pair_abi',
    'uniswap_v3_pool_abi',
    'erc20_abi',
    'uniswap_v2_router_abi',
    'uniswap_v2_pair_abi',
    'uniswap_v3_router_abi',
    'uniswap_v3_quoter_abi'
]