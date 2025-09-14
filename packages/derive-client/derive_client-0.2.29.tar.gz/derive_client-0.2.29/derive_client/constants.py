"""
Constants for Derive (formerly Lyra).
"""

from pathlib import Path

from pydantic import BaseModel

from derive_client.data_types import Currency, Environment, UnderlyingCurrency


class ContractAddresses(BaseModel, frozen=True):
    ETH_PERP: str
    BTC_PERP: str
    ETH_OPTION: str
    BTC_OPTION: str
    TRADE_MODULE: str
    RFQ_MODULE: str
    STANDARD_RISK_MANAGER: str
    BTC_PORTFOLIO_RISK_MANAGER: str
    ETH_PORTFOLIO_RISK_MANAGER: str
    CASH_ASSET: str
    USDC_ASSET: str
    DEPOSIT_MODULE: str
    WITHDRAWAL_MODULE: str
    TRANSFER_MODULE: str

    def __getitem__(self, key):
        return getattr(self, key)


class EnvConfig(BaseModel, frozen=True):
    base_url: str
    ws_address: str
    rpc_endpoint: str
    block_explorer: str
    ACTION_TYPEHASH: str
    DOMAIN_SEPARATOR: str
    contracts: ContractAddresses


PKG_ROOT = Path(__file__).parent
DATA_DIR = PKG_ROOT / "data"
ABI_DATA_DIR = DATA_DIR / "abi"

PUBLIC_HEADERS = {"accept": "application/json", "content-type": "application/json"}

TEST_PRIVATE_KEY = "0xc14f53ee466dd3fc5fa356897ab276acbef4f020486ec253a23b0d1c3f89d4f4"
DEFAULT_SPOT_QUOTE_TOKEN = "USDC"

CONFIGS: dict[Environment, EnvConfig] = {
    Environment.TEST: EnvConfig(
        base_url="https://api-demo.lyra.finance",
        ws_address="wss://api-demo.lyra.finance/ws",
        rpc_endpoint="https://testnet-rpc.derive.xyz",
        block_explorer="https://explorer-prod-testnet-0eakp60405.t.conduit.xyz",
        ACTION_TYPEHASH="0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17",
        DOMAIN_SEPARATOR="0x9bcf4dc06df5d8bf23af818d5716491b995020f377d3b7b64c29ed14e3dd1105",
        contracts=ContractAddresses(
            ETH_PERP="0x010e26422790C6Cb3872330980FAa7628FD20294",
            BTC_PERP="0xAFB6Bb95cd70D5367e2C39e9dbEb422B9815339D",
            ETH_OPTION="0xBcB494059969DAaB460E0B5d4f5c2366aab79aa1",
            BTC_OPTION="0xAeB81cbe6b19CeEB0dBE0d230CFFE35Bb40a13a7",
            TRADE_MODULE="0x87F2863866D85E3192a35A73b388BD625D83f2be",
            RFQ_MODULE="0x4E4DD8Be1e461913D9A5DBC4B830e67a8694ebCa",
            STANDARD_RISK_MANAGER="0x28bE681F7bEa6f465cbcA1D25A2125fe7533391C",
            BTC_PORTFOLIO_RISK_MANAGER="0xbaC0328cd4Af53d52F9266Cdbd5bf46720320A20",
            ETH_PORTFOLIO_RISK_MANAGER="0xDF448056d7bf3f9Ca13d713114e17f1B7470DeBF",
            CASH_ASSET="0x6caf294DaC985ff653d5aE75b4FF8E0A66025928",
            USDC_ASSET="0xe80F2a02398BBf1ab2C9cc52caD1978159c215BD",
            DEPOSIT_MODULE="0x43223Db33AdA0575D2E100829543f8B04A37a1ec",
            WITHDRAWAL_MODULE="0xe850641C5207dc5E9423fB15f89ae6031A05fd92",
            TRANSFER_MODULE="0x0CFC1a4a90741aB242cAfaCD798b409E12e68926",
        ),
    ),
    Environment.PROD: EnvConfig(
        base_url="https://api.lyra.finance",
        ws_address="wss://api.lyra.finance/ws",
        rpc_endpoint="https://957.rpc.thirdweb.com/",
        block_explorer="https://explorer.lyra.finance",
        ACTION_TYPEHASH="0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17",
        DOMAIN_SEPARATOR="0xd96e5f90797da7ec8dc4e276260c7f3f87fedf68775fbe1ef116e996fc60441b",
        contracts=ContractAddresses(
            ETH_PERP="0xAf65752C4643E25C02F693f9D4FE19cF23a095E3",
            BTC_PERP="0xDBa83C0C654DB1cd914FA2710bA743e925B53086",
            ETH_OPTION="0x4BB4C3CDc7562f08e9910A0C7D8bB7e108861eB4",
            BTC_OPTION="0xd0711b9eBE84b778483709CDe62BacFDBAE13623",
            TRADE_MODULE="0xB8D20c2B7a1Ad2EE33Bc50eF10876eD3035b5e7b",
            RFQ_MODULE="0x9371352CCef6f5b36EfDFE90942fFE622Ab77F1D",
            STANDARD_RISK_MANAGER="0x28c9ddF9A3B29c2E6a561c1BC520954e5A33de5D",
            BTC_PORTFOLIO_RISK_MANAGER="0x45DA02B9cCF384d7DbDD7b2b13e705BADB43Db0D",
            ETH_PORTFOLIO_RISK_MANAGER="0xe7cD9370CdE6C9b5eAbCe8f86d01822d3de205A0",
            CASH_ASSET="0x57B03E14d409ADC7fAb6CFc44b5886CAD2D5f02b",
            USDC_ASSET="0x6879287835A86F50f784313dBEd5E5cCC5bb8481",
            DEPOSIT_MODULE="0x9B3FE5E5a3bcEa5df4E08c41Ce89C4e3Ff01Ace3",
            WITHDRAWAL_MODULE="0x9d0E8f5b25384C7310CB8C6aE32C8fbeb645d083",
            TRANSFER_MODULE="0x01259207A40925b794C8ac320456F7F6c8FE2636",
        ),
    ),
}


DEFAULT_REFERER = "0x9135BA0f495244dc0A5F029b25CDE95157Db89AD"

GAS_FEE_BUFFER = 1.1  # buffer multiplier to pad maxFeePerGas
GAS_LIMIT_BUFFER = 1.1  # buffer multiplier to pad gas limit
MSG_GAS_LIMIT = 200_000
ASSUMED_BRIDGE_GAS_LIMIT = 1_000_000
MIN_PRIORITY_FEE = 10_000
PAYLOAD_SIZE = 161
TARGET_SPEED = "FAST"

DEFAULT_GAS_FUNDING_AMOUNT = int(0.0001 * 1e18)  # 0.0001 ETH

TOKEN_DECIMALS = {
    UnderlyingCurrency.ETH: 18,
    UnderlyingCurrency.BTC: 8,
    UnderlyingCurrency.USDC: 6,
    UnderlyingCurrency.LBTC: 8,
    UnderlyingCurrency.WEETH: 18,
    UnderlyingCurrency.OP: 18,
    UnderlyingCurrency.DRV: 18,
    UnderlyingCurrency.rswETH: 18,
    UnderlyingCurrency.rsETH: 18,
    UnderlyingCurrency.DAI: 18,
    UnderlyingCurrency.USDT: 6,
    UnderlyingCurrency.OLAS: 18,
    UnderlyingCurrency.DRV: 18,
}

CURRENCY_DECIMALS = {
    Currency.ETH: 18,
    Currency.weETH: 18,
    Currency.rswETH: 18,
    Currency.rsETH: 18,
    Currency.USDe: 18,
    Currency.deUSD: 18,
    Currency.PYUSD: 6,
    Currency.sUSDe: 18,
    Currency.SolvBTC: 18,
    Currency.SolvBTCBBN: 18,
    Currency.LBTC: 8,
    Currency.OP: 18,
    Currency.DAI: 18,
    Currency.sDAI: 18,
    Currency.cbBTC: 8,
    Currency.eBTC: 8,
    Currency.AAVE: 18,
    Currency.OLAS: 18,
    Currency.DRV: 18,
    Currency.WBTC: 8,
    Currency.WETH: 18,
    Currency.USDC: 6,
    Currency.USDT: 6,
    Currency.wstETH: 18,
    Currency.USDCe: 6,
    Currency.SNX: 18,
}

DEFAULT_RPC_ENDPOINTS = DATA_DIR / "rpc_endpoints.yaml"

NEW_VAULT_ABI_PATH = ABI_DATA_DIR / "socket_superbridge_vault.json"
OLD_VAULT_ABI_PATH = ABI_DATA_DIR / "socket_superbridge_vault_old.json"
DEPOSIT_HELPER_ABI_PATH = ABI_DATA_DIR / "deposit_helper.json"
CONTROLLER_ABI_PATH = ABI_DATA_DIR / "controller.json"
CONTROLLER_V0_ABI_PATH = ABI_DATA_DIR / "controller_v0.json"
DEPOSIT_HOOK_ABI_PATH = ABI_DATA_DIR / "deposit_hook.json"
LIGHT_ACCOUNT_ABI_PATH = ABI_DATA_DIR / "light_account.json"
L1_CHUG_SPLASH_PROXY_ABI_PATH = ABI_DATA_DIR / "l1_chug_splash_proxy.json"
L1_STANDARD_BRIDGE_ABI_PATH = ABI_DATA_DIR / "l1_standard_bridge.json"
L1_CROSS_DOMAIN_MESSENGER_ABI_PATH = ABI_DATA_DIR / "l1_cross_domain_messenger.json"
L2_STANDARD_BRIDGE_ABI_PATH = ABI_DATA_DIR / "l2_standard_bridge.json"
L2_CROSS_DOMAIN_MESSENGER_ABI_PATH = ABI_DATA_DIR / "l2_cross_domain_messenger.json"
WITHDRAW_WRAPPER_V2_ABI_PATH = ABI_DATA_DIR / "withdraw_wrapper_v2.json"
DERIVE_ABI_PATH = ABI_DATA_DIR / "Derive.json"
DERIVE_L2_ABI_PATH = ABI_DATA_DIR / "DeriveL2.json"
LYRA_OFT_WITHDRAW_WRAPPER_ABI_PATH = ABI_DATA_DIR / "LyraOFTWithdrawWrapper.json"
ERC20_ABI_PATH = ABI_DATA_DIR / "erc20.json"
SOCKET_ABI_PATH = ABI_DATA_DIR / "Socket.json"
CONNECTOR_PLUG = ABI_DATA_DIR / "ConnectorPlug.json"


# Contracts used in bridging module
LYRA_OFT_WITHDRAW_WRAPPER_ADDRESS = "0x9400cc156dad38a716047a67c897973A29A06710"
L1_CHUG_SPLASH_PROXY = "0x61e44dc0dae6888b5a301887732217d5725b0bff"
RESOLVED_DELEGATE_PROXY = "0x5456f02c08e9A018E42C39b351328E5AA864174A"
L2_STANDARD_BRIDGE_PROXY = "0x4200000000000000000000000000000000000010"
L2_CROSS_DOMAIN_MESSENGER_PROXY = "0x4200000000000000000000000000000000000007"
WITHDRAW_WRAPPER_V2 = "0xea8E683D8C46ff05B871822a00461995F93df800"
ETH_DEPOSIT_WRAPPER = "0x46e75B6983126896227a5717f2484efb04A0c151"
BASE_DEPOSIT_WRAPPER = "0x9628bba16db41ea7fe1fd84f9ce53bc27c63f59b"
ARBITRUM_DEPOSIT_WRAPPER = "0x076BB6117750e80AD570D98891B68da86C203A88"
OPTIMISM_DEPOSIT_WRAPPER = "0xC65005131Cfdf06622b99E8E17f72Cf694b586cC"
