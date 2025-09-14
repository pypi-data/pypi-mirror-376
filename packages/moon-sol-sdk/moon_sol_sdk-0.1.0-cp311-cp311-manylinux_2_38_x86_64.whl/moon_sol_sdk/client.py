import moon_sol_sdk_rust

class SolClient:
    def __init__(self, private_key: str, rpc_url: str, commitment: str, priority_fee: int, is_jito: bool = False):
        swqos_config = moon_sol_sdk_rust.PySwqosConfig("default", None, None, rpc_url)
        priority_fee = moon_sol_sdk_rust.PyPriorityFee(priority_fee, [0.001], [0.001])
        self.rpc_url = rpc_url
        self.is_jito = is_jito
        if is_jito:
            swqos_config = moon_sol_sdk_rust.PySwqosConfig(
                "jito",
                "",
                "frankfurt",
                "https://frankfurt.mainnet.block-engine.jito.wtf"
            )
            
        self.trade_config = moon_sol_sdk_rust.PyTradeConfig(
            rpc_url,
            commitment,
            priority_fee,
            [swqos_config]
        )
        self.client = moon_sol_sdk_rust.PySolanaTrade(private_key, self.trade_config)

    def get_public_key(self) -> str:
        return self.client.get_public_key()
    
    # side "buy" or "sell"
    def pump_swap(self, side: str, pool_address: str, mint_address: str, amount: int, slippage: float = 0.005):
        try:
            params = moon_sol_sdk_rust.PyPumpSwapParams.from_pool_address(
            self.rpc_url,
                pool_address
                )
            result = moon_sol_sdk_rust.pump_swap(
                action=side,
                client=self.client,
                mint_address=mint_address,
                amount=amount,
                slippage_bps=int(slippage * 10000),  # Convert to basis points
                params=params,
                with_tip=self.is_jito  # 关闭tip以简化测试
            )
            return result
        except Exception as e:
            raise Exception("Failed to fetch pool parameters or execute swap", e)
    
    # side "buy" or "sell"
    def raydium_cpmm_swap(self, side: str, pool_address: str, mint_address: str, amount: int, slippage: float = 0.005):
        try:
            params = moon_sol_sdk_rust.PyRaydiumCpmmSwapParams.from_pool_address(
                self.rpc_url,
                pool_address
            )
            result = moon_sol_sdk_rust.raydium_cpmm_swap(
                action=side,
                client=self.client,
                mint_address=mint_address,
                amount=amount,
                slippage_bps=int(slippage * 100),  # Convert to basis points
                params=params,
                with_tip=self.is_jito  # 关闭tip以简化测试
            )
            return result
        except Exception as e:
            raise Exception("Failed to fetch pool parameters or execute swap", e)
        