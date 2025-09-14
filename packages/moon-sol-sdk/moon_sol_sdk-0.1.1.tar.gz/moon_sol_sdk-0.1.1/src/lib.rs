use pyo3::prelude::*;
use std::sync::Arc;
use std::str::FromStr;

use sol_trade_sdk::{
    common::{PriorityFee, TradeConfig},
    swqos::{SwqosConfig, SwqosRegion},
    trading::{core::params::{PumpSwapParams, RaydiumCpmmParams}, factory::DexType},
    SolanaTrade,
};

// Import solana types directly
use solana_sdk::{
    commitment_config::CommitmentConfig,
    pubkey::Pubkey,
    signature::Keypair,
};
use solana_signer::Signer;

// ========================
// Configuration Structures
// ========================

/// Python binding for SWQOS configuration
#[pyclass]
#[derive(Clone)]
pub struct PySwqosConfig {
    pub inner: SwqosConfig,
}

#[pymethods]
impl PySwqosConfig {
    #[new]
    #[pyo3(signature = (config_type, token=None, region=None, url=None))]
    pub fn new(
        config_type: &str,
        token: Option<String>,
        region: Option<String>,
        url: Option<String>,
    ) -> PyResult<Self> {
        let swqos_region = match region.as_deref() {
            Some("frankfurt") => SwqosRegion::Frankfurt,
            Some("tokyo") => SwqosRegion::Tokyo,
            _ => SwqosRegion::Frankfurt,
        };

        let inner = match config_type {
            "default" => SwqosConfig::Default(url.unwrap_or_else(|| "https://api.mainnet-beta.solana.com".to_string())),
            "jito" => SwqosConfig::Jito(token.unwrap_or_default(), swqos_region, url),
            "nextblock" => SwqosConfig::NextBlock(token.unwrap_or_default(), swqos_region, url),
            "zeroslot" => SwqosConfig::ZeroSlot(token.unwrap_or_default(), swqos_region, url),
            "temporal" => SwqosConfig::Temporal(token.unwrap_or_default(), swqos_region, url),
            "bloxroute" => SwqosConfig::Bloxroute(token.unwrap_or_default(), swqos_region, url),
            "node1" => SwqosConfig::Node1(token.unwrap_or_default(), swqos_region, url),
            "flashblock" => SwqosConfig::FlashBlock(token.unwrap_or_default(), swqos_region, url),
            "blockrazor" => SwqosConfig::BlockRazor(token.unwrap_or_default(), swqos_region, url),
            "astralane" => SwqosConfig::Astralane(token.unwrap_or_default(), swqos_region, url),
            _ => return Err(pyo3::exceptions::PyValueError::new_err("Invalid SWQOS config type")),
        };

        Ok(PySwqosConfig { inner })
    }
}

/// Python binding for Priority Fee configuration
#[pyclass]
#[derive(Clone)]
pub struct PyPriorityFee {
    pub inner: PriorityFee,
}

#[pymethods]
impl PyPriorityFee {
    #[new]
    #[pyo3(signature = (rpc_unit_limit=None, buy_tip_fees=None, sell_tip_fees=None))]
    pub fn new(
        rpc_unit_limit: Option<u32>,
        buy_tip_fees: Option<Vec<f64>>,
        sell_tip_fees: Option<Vec<f64>>,
    ) -> Self {
        let mut priority_fee = PriorityFee::default();
        
        if let Some(limit) = rpc_unit_limit {
            priority_fee.rpc_unit_limit = limit;
        }
        
        if let Some(fees) = buy_tip_fees {
            priority_fee.buy_tip_fees = fees;
        }
        
        if let Some(fees) = sell_tip_fees {
            priority_fee.sell_tip_fees = fees;
        }

        PyPriorityFee { inner: priority_fee }
    }
}

/// Python binding for Trade Config
#[pyclass]
#[derive(Clone)]
pub struct PyTradeConfig {
    pub inner: TradeConfig,
}

#[pymethods]
impl PyTradeConfig {
    #[new]
    #[pyo3(signature = (rpc_url, commitment=None, priority_fee=None, swqos_configs=None))]
    pub fn new(
        rpc_url: String,
        commitment: Option<String>,
        priority_fee: Option<&PyPriorityFee>,
        swqos_configs: Option<Vec<PySwqosConfig>>,
    ) -> PyResult<Self> {
        let commitment_config = match commitment.as_deref() {
            Some("processed") => CommitmentConfig::processed(),
            Some("confirmed") => CommitmentConfig::confirmed(),
            Some("finalized") => CommitmentConfig::finalized(),
            _ => CommitmentConfig::confirmed(),
        };

        let priority_fee = priority_fee
            .map(|pf| pf.inner.clone())
            .unwrap_or_else(PriorityFee::default);

        let swqos_configs = swqos_configs
            .map(|configs| configs.into_iter().map(|c| c.inner).collect())
            .unwrap_or_else(|| vec![SwqosConfig::Default(rpc_url.clone())]);

        let inner = TradeConfig {
            rpc_url,
            commitment: commitment_config,
            priority_fee,
            swqos_configs,
        };

        Ok(PyTradeConfig { inner })
    }
}

// ========================
// Parameter Structures
// ========================

/// Python binding for PumpSwap parameters
#[pyclass]
#[derive(Clone)]
pub struct PyPumpSwapParams {
    pub inner: PumpSwapParams,
}

#[pymethods]
impl PyPumpSwapParams {
    #[new]
    #[pyo3(signature = (pool, base_mint, quote_mint, pool_base_token_account, pool_quote_token_account, pool_base_token_reserves, pool_quote_token_reserves, coin_creator_vault_ata, coin_creator_vault_authority, base_token_program, quote_token_program))]
    pub fn new(
        pool: String,
        base_mint: String,
        quote_mint: String,
        pool_base_token_account: String,
        pool_quote_token_account: String,
        pool_base_token_reserves: u64,
        pool_quote_token_reserves: u64,
        coin_creator_vault_ata: String,
        coin_creator_vault_authority: String,
        base_token_program: String,
        quote_token_program: String,
    ) -> PyResult<Self> {
        let inner = PumpSwapParams {
            pool: Pubkey::from_str(&pool).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid pool pubkey: {}", e)))?,
            base_mint: Pubkey::from_str(&base_mint).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid base_mint pubkey: {}", e)))?,
            quote_mint: Pubkey::from_str(&quote_mint).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid quote_mint pubkey: {}", e)))?,
            pool_base_token_account: Pubkey::from_str(&pool_base_token_account).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid pool_base_token_account pubkey: {}", e)))?,
            pool_quote_token_account: Pubkey::from_str(&pool_quote_token_account).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid pool_quote_token_account pubkey: {}", e)))?,
            pool_base_token_reserves,
            pool_quote_token_reserves,
            coin_creator_vault_ata: Pubkey::from_str(&coin_creator_vault_ata).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid coin_creator_vault_ata pubkey: {}", e)))?,
            coin_creator_vault_authority: Pubkey::from_str(&coin_creator_vault_authority).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid coin_creator_vault_authority pubkey: {}", e)))?,
            base_token_program: Pubkey::from_str(&base_token_program).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid base_token_program pubkey: {}", e)))?,
            quote_token_program: Pubkey::from_str(&quote_token_program).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid quote_token_program pubkey: {}", e)))?,
        };

        Ok(PyPumpSwapParams { inner })
    }

    /// Create parameters from pool address using RPC
    #[staticmethod]
    #[pyo3(signature = (rpc_url, pool_address))]
    pub fn from_pool_address(rpc_url: String, pool_address: String) -> PyResult<Self> {
        let rt = tokio::runtime::Runtime::new().map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create tokio runtime: {}", e)))?;
        
        rt.block_on(async {
            let trade_config = TradeConfig {
                rpc_url: rpc_url.clone(),
                commitment: CommitmentConfig::confirmed(),
                priority_fee: PriorityFee::default(),
                swqos_configs: vec![SwqosConfig::Default(rpc_url)],
            };
            
            let keypair = Keypair::new();
            let client = SolanaTrade::new(Arc::new(keypair), trade_config).await;
            let pool_pubkey = Pubkey::from_str(&pool_address).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid pool address: {}", e)))?;
            
            let params = PumpSwapParams::from_pool_address_by_rpc(&client.rpc, &pool_pubkey)
                .await
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to fetch pool parameters: {}", e)))?;
                
            Ok(PyPumpSwapParams { inner: params })
        })
    }
}

/// Python binding for Raydium CPMM parameters
#[pyclass]
#[derive(Clone)]
pub struct PyRaydiumCpmmParams {
    pub inner: RaydiumCpmmParams,
}

#[pymethods]
impl PyRaydiumCpmmParams {
    #[new]
    #[pyo3(signature = (pool_state, amm_config, base_mint, quote_mint, base_reserve, quote_reserve, base_vault, quote_vault, base_token_program, quote_token_program, observation_state))]
    pub fn new(
        pool_state: String,
        amm_config: String,
        base_mint: String,
        quote_mint: String,
        base_reserve: u64,
        quote_reserve: u64,
        base_vault: String,
        quote_vault: String,
        base_token_program: String,
        quote_token_program: String,
        observation_state: String,
    ) -> PyResult<Self> {
        let inner = RaydiumCpmmParams {
            pool_state: Pubkey::from_str(&pool_state).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid pool_state pubkey: {}", e)))?,
            amm_config: Pubkey::from_str(&amm_config).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid amm_config pubkey: {}", e)))?,
            base_mint: Pubkey::from_str(&base_mint).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid base_mint pubkey: {}", e)))?,
            quote_mint: Pubkey::from_str(&quote_mint).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid quote_mint pubkey: {}", e)))?,
            base_reserve,
            quote_reserve,
            base_vault: Pubkey::from_str(&base_vault).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid base_vault pubkey: {}", e)))?,
            quote_vault: Pubkey::from_str(&quote_vault).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid quote_vault pubkey: {}", e)))?,
            base_token_program: Pubkey::from_str(&base_token_program).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid base_token_program pubkey: {}", e)))?,
            quote_token_program: Pubkey::from_str(&quote_token_program).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid quote_token_program pubkey: {}", e)))?,
            observation_state: Pubkey::from_str(&observation_state).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid observation_state pubkey: {}", e)))?,
        };

        Ok(PyRaydiumCpmmParams { inner })
    }

    /// Create parameters from pool address using RPC
    #[staticmethod]
    #[pyo3(signature = (rpc_url, pool_address))]
    pub fn from_pool_address(rpc_url: String, pool_address: String) -> PyResult<Self> {
        let rt = tokio::runtime::Runtime::new().map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create tokio runtime: {}", e)))?;
        
        rt.block_on(async {
            let trade_config = TradeConfig {
                rpc_url: rpc_url.clone(),
                commitment: CommitmentConfig::confirmed(),
                priority_fee: PriorityFee::default(),
                swqos_configs: vec![SwqosConfig::Default(rpc_url)],
            };
            
            let keypair = Keypair::new();
            let client = SolanaTrade::new(Arc::new(keypair), trade_config).await;
            let pool_pubkey = Pubkey::from_str(&pool_address).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid pool address: {}", e)))?;
            
            let params = RaydiumCpmmParams::from_pool_address_by_rpc(&client.rpc, &pool_pubkey)
                .await
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to fetch pool parameters: {}", e)))?;
                
            Ok(PyRaydiumCpmmParams { inner: params })
        })
    }
}

// ========================
// Main Trading Client
// ========================

/// Python binding for SolanaTrade client
#[pyclass]
pub struct PySolanaTrade {
    client: SolanaTrade,
    rt: tokio::runtime::Runtime,
}

#[pymethods]
impl PySolanaTrade {
    #[new]
    pub fn new(private_key_base58: String, config: &PyTradeConfig) -> PyResult<Self> {
        let rt = tokio::runtime::Runtime::new().map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create tokio runtime: {}", e)))?;
        
        // 验证私钥长度（除非是特殊的测试密钥）
        if private_key_base58 != "TEST_KEY" && (private_key_base58.len() < 80 || private_key_base58.len() > 90) {
            return Err(pyo3::exceptions::PyValueError::new_err(
                format!("Invalid private key length: {}. Expected 80-90 characters for base58 encoded Solana private key.", private_key_base58.len())
            ));
        }
        
        let client = rt.block_on(async {
            // 使用更安全的方式处理私钥
            let keypair = match private_key_base58.as_str() {
                // 提供一个特殊的测试私钥用于开发
                "TEST_KEY" => {
                    // 生成一个确定性的测试密钥对
                    let seed = [1u8; 32]; // 固定的测试种子
                    Keypair::new_from_array(seed)
                },
                _ => {
                    // 尝试解析实际的私钥
                    Keypair::from_base58_string(&private_key_base58)
                    // 注意：如果这里失败，会panic，我们需要处理这个
                }
            };
            
            Ok(SolanaTrade::new(Arc::new(keypair), config.inner.clone()).await)
        });

        match client {
            Ok(c) => Ok(PySolanaTrade { client: c, rt }),
            Err(e) => Err(e),
        }
    }

    /// Get the public key of the payer
    pub fn get_public_key(&self) -> String {
        self.client.payer.pubkey().to_string()
    }

    /// Get latest blockhash
    pub fn get_latest_blockhash(&self) -> PyResult<String> {
        self.rt.block_on(async {
            self.client.rpc.get_latest_blockhash()
                .await
                .map(|hash| hash.to_string())
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to get latest blockhash: {}", e)))
        })
    }
}

// ========================
// Helper Functions
// ========================

/// 处理交易结果，提供更好的错误信息
fn handle_transaction_result<T: std::fmt::Display, E: std::fmt::Display>(result: Result<T, E>, transaction_type: &str) -> PyResult<String> {
    match result {
        Ok(signature) => {
            println!("✓ {} transaction submitted successfully with signature: {}", transaction_type, signature);
            Ok(format!("Transaction successful: {}", signature))
        },
        Err(e) => {
            let error_msg = format!("{}", e);
            println!("{} Error details: {}", transaction_type, error_msg);

            Err(pyo3::exceptions::PyRuntimeError::new_err(format!("Transaction failed: {}", error_msg)))
        }
    }
}

// ========================
// Trading Functions
// ========================

/// PumpSwap trading with buy and sell functionality
#[pyfunction]
#[pyo3(signature = (action, client, mint_address, amount, slippage_bps=None, params=None, create_wsol_ata=true, close_wsol_ata=true, with_tip=true))]
pub fn pump_swap(
    action: &str,
    client: &PySolanaTrade,
    mint_address: String,
    amount: u64,
    slippage_bps: Option<u64>,
    params: Option<&PyPumpSwapParams>,
    create_wsol_ata: Option<bool>,
    close_wsol_ata: Option<bool>,
    with_tip: Option<bool>,
) -> PyResult<String> {
    let mint_pubkey = Pubkey::from_str(&mint_address)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid mint address: {}", e)))?;

    let slippage_basis_points = slippage_bps.map(|bps| bps);
    let create_wsol = create_wsol_ata.unwrap_or(true);
    let close_wsol = close_wsol_ata.unwrap_or(true);
    let with_tip_flag = with_tip.unwrap_or(true);

    client.rt.block_on(async {
        let recent_blockhash = client.client.rpc.get_latest_blockhash().await
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to get latest blockhash: {}", e)))?;

        let result = match action {
            "buy" => {
                let protocol_params = if let Some(p) = params {
                    Box::new(p.inner.clone())
                } else {
                    return Err(pyo3::exceptions::PyValueError::new_err("PumpSwap parameters are required for buy"));
                };

                // Add debug information
                println!("Executing PumpSwap buy:");
                println!("  Mint: {}", mint_pubkey);
                println!("  Amount: {} lamports", amount);
                println!("  Slippage: {:?} bps", slippage_basis_points);
                println!("  Wallet: {}", client.client.payer.pubkey());

                client.client.buy(
                    DexType::PumpSwap,
                    mint_pubkey,
                    amount,
                    slippage_basis_points,
                    recent_blockhash,
                    None,
                    protocol_params,
                    None,
                    with_tip_flag,
                    create_wsol,
                    close_wsol,
                    true,
                    false,
                ).await
            },
            "sell" => {
                let protocol_params = if let Some(p) = params {
                    Box::new(p.inner.clone())
                } else {
                    return Err(pyo3::exceptions::PyValueError::new_err("PumpSwap parameters are required for sell"));
                };

                // Add debug information
                println!("Executing PumpSwap sell:");
                println!("  Mint: {}", mint_pubkey);
                println!("  Amount: {} tokens", amount);
                println!("  Slippage: {:?} bps", slippage_basis_points);
                println!("  Wallet: {}", client.client.payer.pubkey());

                client.client.sell(
                    DexType::PumpSwap,
                    mint_pubkey,
                    amount,
                    slippage_basis_points,
                    recent_blockhash,
                    None,
                    false,
                    protocol_params,
                    None,
                    with_tip_flag,
                    create_wsol,
                    close_wsol,
                    false,
                ).await
            },
            _ => return Err(pyo3::exceptions::PyValueError::new_err("Action must be 'buy' or 'sell'")),
        };

        handle_transaction_result(result, "PumpSwap")
    })
}

/// Raydium CPMM trading with buy and sell functionality
#[pyfunction]
#[pyo3(signature = (action, client, mint_address, amount, slippage_bps=None, params=None, create_wsol_ata=true, close_wsol_ata=true, with_tip=true))]
pub fn raydium_cpmm_swap(
    action: &str,
    client: &PySolanaTrade,
    mint_address: String,
    amount: u64,
    slippage_bps: Option<u64>,
    params: Option<&PyRaydiumCpmmParams>,
    create_wsol_ata: Option<bool>,
    close_wsol_ata: Option<bool>,
    with_tip: Option<bool>,
) -> PyResult<String> {
    let mint_pubkey = Pubkey::from_str(&mint_address)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid mint address: {}", e)))?;

    let slippage_basis_points = slippage_bps.map(|bps| bps);
    let create_wsol = create_wsol_ata.unwrap_or(true);
    let close_wsol = close_wsol_ata.unwrap_or(true);
    let with_tip_flag = with_tip.unwrap_or(true);

    client.rt.block_on(async {
        let recent_blockhash = client.client.rpc.get_latest_blockhash().await
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to get latest blockhash: {}", e)))?;

        let result = match action {
            "buy" => {
                let protocol_params = if let Some(p) = params {
                    Box::new(p.inner.clone())
                } else {
                    return Err(pyo3::exceptions::PyValueError::new_err("Raydium CPMM parameters are required for buy"));
                };

                // Add debug information for buy
                println!("Executing Raydium CPMM buy:");
                println!("  Mint: {}", mint_pubkey);
                println!("  Amount: {} lamports", amount);
                println!("  Slippage: {:?} bps", slippage_basis_points);
                println!("  Wallet: {}", client.client.payer.pubkey());

                client.client.buy(
                    DexType::RaydiumCpmm,
                    mint_pubkey,
                    amount,
                    slippage_basis_points,
                    recent_blockhash,
                    None,
                    protocol_params,
                    None,
                    with_tip_flag,
                    create_wsol,
                    close_wsol,
                    true,
                    false,
                ).await
            },
            "sell" => {
                let protocol_params = if let Some(p) = params {
                    Box::new(p.inner.clone())
                } else {
                    return Err(pyo3::exceptions::PyValueError::new_err("Raydium CPMM parameters are required for sell"));
                };

                client.client.sell(
                    DexType::RaydiumCpmm,
                    mint_pubkey,
                    amount,
                    slippage_basis_points,
                    recent_blockhash,
                    None,
                    false,
                    protocol_params,
                    None,
                    with_tip_flag,
                    create_wsol,
                    close_wsol,
                    false,
                ).await
            },
            _ => return Err(pyo3::exceptions::PyValueError::new_err("Action must be 'buy' or 'sell'")),
        };

        handle_transaction_result(result, "Raydium CPMM")
    })
}


/// A Python module implemented in Rust.
#[pymodule]
fn moon_sol_sdk_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Add trading functions
    m.add_function(wrap_pyfunction!(pump_swap, m)?)?;
    m.add_function(wrap_pyfunction!(raydium_cpmm_swap, m)?)?;
    
    // Add configuration classes
    m.add_class::<PySwqosConfig>()?;
    m.add_class::<PyPriorityFee>()?;
    m.add_class::<PyTradeConfig>()?;
    
    // Add parameter classes
    m.add_class::<PyPumpSwapParams>()?;
    m.add_class::<PyRaydiumCpmmParams>()?;
    
    // Add trading client
    m.add_class::<PySolanaTrade>()?;
    
    Ok(())
}
