# Moon Sol SDK

A Python binding for Solana trading operations, specifically designed for PumpSwap and Raydium CPMM trading. This SDK is based on the [sol-trade-sdk](https://github.com/0xfnzero/sol-trade-sdk) Rust library.

## Features

- **PumpSwap Trading**: Support for buying and selling tokens on PumpSwap pools
- **Raydium CPMM Trading**: Support for Raydium Concentrated Pool Market Maker operations
- **MEV Protection**: Support for multiple SWQOS services (Jito, FlashBlock, BlockRazor, etc.)
- **Flexible Configuration**: Comprehensive configuration options for trading parameters
- **Async Operations**: Built on Tokio for efficient async operations

## Installation

### Prerequisites

- Python 3.8+
- Rust toolchain (for building from source)

### Building from Source

1. Clone the repository:
```bash
git clone <repository-url>
cd moon_sol_sdk
```

2. Install Python dependencies:
```bash
pip install maturin
```

3. Build and install the package:
```bash
# Development build
maturin develop

# Or production build
maturin build --release
pip install target/wheels/*.whl
```

## Quick Start

### Basic Configuration

```python
import moon_sol_sdk

# Create SWQOS configuration for MEV protection
swqos_config = moon_sol_sdk.PySwqosConfig("jito", "your_uuid", "frankfurt", None)

# Create priority fee configuration
priority_fee = moon_sol_sdk.PyPriorityFee(
    rpc_unit_limit=150000,
    buy_tip_fees=[0.001, 0.002],
    sell_tip_fees=[0.001]
)

# Create trade configuration
trade_config = moon_sol_sdk.PyTradeConfig(
    rpc_url="https://api.mainnet-beta.solana.com",
    commitment="confirmed",
    priority_fee=priority_fee,
    swqos_configs=[swqos_config]
)

# Create trading client
client = moon_sol_sdk.PySolanaTrade("your_private_key_base58", trade_config)
```

### PumpSwap Trading

```python
# Fetch pool parameters automatically
params = moon_sol_sdk.PyPumpSwapParams.from_pool_address(
    "https://api.mainnet-beta.solana.com",
    "pool_address_here"
)

# Buy tokens
result = moon_sol_sdk.pump_swap(
    action="buy",
    client=client,
    mint_address="token_mint_address",
    amount=100000,  # in lamports
    slippage_bps=500,  # 5% slippage
    params=params,
    with_tip=True
)

# Sell tokens
result = moon_sol_sdk.pump_swap(
    action="sell",
    client=client,
    mint_address="token_mint_address",
    amount=1000000,  # token amount
    slippage_bps=500,
    params=params,
    with_tip=True
)
```

### Raydium CPMM Trading

```python
# Fetch pool parameters automatically
params = moon_sol_sdk.PyRaydiumCpmmParams.from_pool_address(
    "https://api.mainnet-beta.solana.com",
    "pool_address_here"
)

# Buy tokens
result = moon_sol_sdk.raydium_cpmm_swap(
    action="buy",
    client=client,
    mint_address="token_mint_address",
    amount=100000,  # in lamports
    slippage_bps=100,  # 1% slippage
    params=params,
    with_tip=True
)

# Sell tokens
result = moon_sol_sdk.raydium_cpmm_swap(
    action="sell",
    client=client,
    mint_address="token_mint_address",
    amount=1000000,  # token amount
    slippage_bps=100,
    params=params,
    with_tip=True
)
```

## Configuration Options

### SWQOS Services

The SDK supports multiple MEV protection services:

- `"default"`: Standard RPC (no MEV protection)
- `"jito"`: Jito MEV protection
- `"nextblock"`: NextBlock service
- `"flashblock"`: FlashBlock service
- `"blockrazor"`: BlockRazor service
- `"astralane"`: Astralane service
- `"bloxroute"`: Bloxroute service
- `"node1"`: Node1 service
- `"zeroslot"`: ZeroSlot service
- `"temporal"`: Temporal service

### Priority Fee Configuration

```python
priority_fee = moon_sol_sdk.PyPriorityFee(
    rpc_unit_limit=150000,  # Compute unit limit
    buy_tip_fees=[0.001, 0.002, 0.005],  # SOL amounts for buy tips
    sell_tip_fees=[0.001, 0.002]         # SOL amounts for sell tips
)
```

### Trade Configuration

```python
trade_config = moon_sol_sdk.PyTradeConfig(
    rpc_url="https://api.mainnet-beta.solana.com",
    commitment="confirmed",  # "processed", "confirmed", or "finalized"
    priority_fee=priority_fee,
    swqos_configs=[swqos_config1, swqos_config2]
)
```

## API Reference

### Classes

#### `PySwqosConfig`
Configuration for SWQOS MEV protection services.

**Parameters:**
- `config_type`: Service type ("jito", "flashblock", etc.)
- `token`: API token (if required)
- `region`: Service region ("frankfurt", "virginia", etc.)
- `url`: Custom URL (optional)

#### `PyPriorityFee`
Configuration for transaction priority fees.

**Parameters:**
- `rpc_unit_limit`: Compute unit limit
- `buy_tip_fees`: List of tip fees for buy transactions
- `sell_tip_fees`: List of tip fees for sell transactions

#### `PyTradeConfig`
Main trading configuration.

**Parameters:**
- `rpc_url`: Solana RPC endpoint
- `commitment`: Transaction commitment level
- `priority_fee`: Priority fee configuration
- `swqos_configs`: List of SWQOS configurations

#### `PySolanaTrade`
Main trading client.

**Parameters:**
- `private_key_base58`: Base58 encoded private key
- `config`: Trade configuration

**Methods:**
- `get_public_key()`: Get the public key of the trading account
- `get_latest_blockhash()`: Get the latest blockhash from RPC

#### `PyPumpSwapParams`
Parameters for PumpSwap trading.

**Static Methods:**
- `from_pool_address(rpc_url, pool_address)`: Fetch parameters from pool address

#### `PyRaydiumCpmmParams`
Parameters for Raydium CPMM trading.

**Static Methods:**
- `from_pool_address(rpc_url, pool_address)`: Fetch parameters from pool address

### Functions

#### `pump_swap(action, client, mint_address, amount, ...)`
Execute PumpSwap trading operations.

**Parameters:**
- `action`: "buy" or "sell"
- `client`: Trading client instance
- `mint_address`: Token mint address
- `amount`: Amount to trade (lamports for buy, tokens for sell)
- `slippage_bps`: Slippage in basis points (optional)
- `params`: PumpSwap parameters (optional)
- `create_wsol_ata`: Create WSOL ATA if needed (default: True)
- `close_wsol_ata`: Close WSOL ATA after transaction (default: True)
- `with_tip`: Use MEV protection (default: True)

#### `raydium_cpmm_swap(action, client, mint_address, amount, ...)`
Execute Raydium CPMM trading operations.

**Parameters:** Same as `pump_swap` but with `PyRaydiumCpmmParams`

## Examples

See `examples/trading_example.py` for comprehensive examples of:
- Basic configuration setup
- PumpSwap trading operations
- Raydium CPMM trading operations
- MEV protection configuration

## Security Notes

- **Never commit private keys to version control**
- **Test with small amounts first**
- **Use MEV protection in production**
- **Validate all addresses before trading**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This SDK is built on top of the excellent [sol-trade-sdk](https://github.com/0xfnzero/sol-trade-sdk) by 0xfnzero. Special thanks to the Sol Trade SDK team for their comprehensive Solana trading library.

## Disclaimer

This software is for educational and development purposes. Trading cryptocurrencies involves substantial risk. The authors are not responsible for any financial losses incurred through the use of this software.
