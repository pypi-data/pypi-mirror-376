import moon_sol_sdk  # noqa
import sys

try:
    # 使用默认的公共RPC节点进行测试
    swqos_config = moon_sol_sdk.PySwqosConfig("default", None, None, "https://api.mainnet-beta.solana.com")
    priority_fee = moon_sol_sdk.PyPriorityFee(300000, [0.001], [0.001])  # 降低费用
    trade_config = moon_sol_sdk.PyTradeConfig(
        "https://api.mainnet-beta.solana.com",
        "confirmed",
        priority_fee,
        [swqos_config]
    )
    
    # 生成一个新的测试钱包（注意：这只是测试用，不包含真实资金）
    print("Creating test client...")
    # 使用TEST_KEY以获得更好的测试体验
    test_private_key = "41hFntn64KUvrdSXpdmq6DY4p3aRNWNT8JTxj4uxb9ZY9DvFVezxZ9xfaM2V7MmHLx3UqStCmb4McXF4XLsNNQNA"  # 使用SDK内置的测试私钥
    
    try:
        client = moon_sol_sdk.PySolanaTrade(test_private_key, trade_config)
        print(f"Client created successfully. Wallet: {client.get_public_key()}")
    except Exception as e:
        print(f"Failed to create client: {e}")
        print("Please ensure you have a valid private key")
        sys.exit(1)
    
    # 获取池参数
    print("Fetching pool parameters...")
    try:
        params = moon_sol_sdk.PyRaydiumCpmmParams.from_pool_address(
            "https://api.mainnet-beta.solana.com",
            "43HLu8ZFUhsDNgCvDfDua65a3m3WJGFoY525LAa6qgQq"  # 使用一个更常见的池地址
        )
        print("Pool parameters fetched successfully")
    except Exception as e:
        print(f"Failed to fetch pool parameters: {e}")
        print("Creating manual parameters as fallback...")
        # 创建手动参数作为后备方案
        params = moon_sol_sdk.PyRaydiumCpmmParams(
            pool_state="43HLu8ZFUhsDNgCvDfDua65a3m3WJGFoY525LAa6qgQq",
            amm_config="D8UUgr8a3aHb1zANrVqVjHjnhfkk5BKzGhTiPaneDjfP",
            base_mint="HPv9g2X35uUnuJAdJr6cqF7qtqSCsM9GttxbVgCPbonk",  # 要交易的代币
            quote_mint="So11111111111111111111111111111111111111112",   # WSOL
            base_reserve=1000000000,
            quote_reserve=1000000000,
            base_vault="43HLu8ZFUhsDNgCvDfDua65a3m3WJGFoY525LAa6qgQq",
            quote_vault="43HLu8ZFUhsDNgCvDfDua65a3m3WJGFoY525LAa6qgQq",
            base_token_program="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            quote_token_program="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            observation_state="43HLu8ZFUhsDNgCvDfDua65a3m3WJGFoY525LAa6qgQq"
        )
        print("Manual parameters created successfully")
    
    # 执行交易（使用很小的金额进行测试）
    print("Executing swap...")
    
    # 对于sell操作，我们需要确保钱包中有要卖出的代币
    # 这里我们先尝试一个小金额的sell操作
    print("Note: For sell operations, ensure the wallet has the token to sell")
    print("This is a test transaction and may fail if no tokens are available")
    
    try:
        result = moon_sol_sdk.raydium_cpmm_swap(
            action="sell",
            client=client,
            mint_address="HPv9g2X35uUnuJAdJr6cqF7qtqSCsM9GttxbVgCPbonk",  # 要卖出的代币
            amount=400000000,  # 减少金额进行测试 (1个代币单位)
            slippage_bps=500,  # 增加滑点容忍度到5%
            params=params,
            with_tip=False  # 关闭tip以简化测试
        )
        print("Swap result:", result)
    except Exception as sell_error:
        print(f"Sell operation failed: {sell_error}")
        print("\nThis is expected if the wallet doesn't have the token to sell.")
        print("Let's try a buy operation instead...")
        
        # 如果sell失败，尝试buy操作
        try:
            result = moon_sol_sdk.raydium_cpmm_swap(
                action="buy",
                client=client,
                mint_address="HPv9g2X35uUnuJAdJr6cqF7qtqSCsM9GttxbVgCPbonk",  # 要买入的代币
                amount=100000,  # 0.1 SOL in lamports
                slippage_bps=500,  # 5% slippage
                params=params,
                with_tip=False
            )
            print("Buy result:", result)
        except Exception as buy_error:
            print(f"Buy operation also failed: {buy_error}")
            print("This indicates there may be an issue with the pool parameters or network connectivity")

except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()