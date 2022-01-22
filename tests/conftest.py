import pytest
from brownie import config
from brownie import Contract, interface

# Function scoped isolation fixture to enable xdist.
# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass


@pytest.fixture
def gov(accounts):
    yield accounts.at("0xC0E2830724C946a6748dDFE09753613cd38f6767", force=True)


@pytest.fixture
def strat_ms(accounts):
    yield accounts.at("0x72a34AbafAB09b15E7191822A679f28E067C4a16", force=True)


@pytest.fixture
def user(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts[4]


@pytest.fixture
def keeper(accounts):
    yield accounts[5]


token_addresses = {
    "WFTM": "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83",  # WFTM
    
}

# TODO: uncomment those tokens you want to test as want
@pytest.fixture(
    params=[
        'WFTM', # WBTC
        # "YFI",  # YFI
        # "WETH",  # WETH
        # 'LINK', # LINK
        # 'USDT', # USDT
    ],
    scope="session",
    autouse=True,
)
def token(interface, request):
    yield interface.ERC20(token_addresses[request.param])


cToken_addresses = {
    "WFTM": "0xd528697008aC67A21818751A5e3c58C8daE54696"
}


@pytest.fixture(scope="function")
def cToken(token):
    yield interface.CErc20I(cToken_addresses[token.symbol()])


whale_addresses = {
    "WFTM": "0x39B3bd37208CBaDE74D0fcBDBb12D606295b430a" #geist
}


@pytest.fixture(scope="session", autouse=True)
def token_whale(token):
    yield whale_addresses[token.symbol()]

cToken_whale_addresses = {
    "WFTM": "0x431e81E5dfB5A24541b5Ff8762bDEF3f32F96354"
}


@pytest.fixture(scope="session", autouse=True)
def cToken_whale(token):
    yield cToken_whale_addresses[token.symbol()]

#@pytest.fixture(autouse=True)
#def withdraw_whale_liquidity(cToken_whale, cToken, token, strategy):
#    borrows = cToken.borrowBalanceCurrent(cToken_whale, {'from': cToken_whale}).return_value
#    supply = cToken.balanceOfUnderlying(cToken_whale, {'from': cToken_whale}).return_value
#    print(f"borrow: {borrows/ 10 ** token.decimals()}")
#    print(f"supply: {supply/ 10 ** token.decimals()}")
#    comptroller = Contract(cToken.comptroller())
#    l, collatFactor, c = comptroller.markets(cToken) 

#    amount = supply - borrows / collatFactor * 1e18

#    print(f"Withdrawing {amount/10**token.decimals()} {token.symbol()}")
#    print(f"Available liquidity: {cToken.getCash()/10**token.decimals()}")
#    cToken.redeemUnderlying(amount, {'from': cToken_whale})
#    print(f"Available liquidity: {cToken.getCash()/10**token.decimals()}")

token_prices = {
    "WFTM": 3
}


@pytest.fixture(autouse=True)
def amount(token, token_whale, user):
    # this will get the number of tokens (around $1m worth of token)
    amillion = round(10_000_000 / token_prices[token.symbol()])
    amount = amillion * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate a whale address
    if amount > token.balanceOf(token_whale):
        amount = token.balanceOf(token_whale)
    token.transfer(user, amount, {"from": token_whale})
    print(f"Amount: {amount / 10 ** token.decimals()}")
    yield amount


@pytest.fixture
def weth(interface):
    token_address = "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83"
    yield interface.ERC20(token_address)

@pytest.fixture
def ibComptroller(interface):
    token_address = "0x4250A6D3BD57455d7C6821eECb6206F507576cD2"
    yield interface.ComptrollerI(token_address)

@pytest.fixture
def ib(interface):
    token_address = "0x00a35FD824c717879BF370E70AC6868b95870Dfb"
    yield interface.ERC20(token_address)

@pytest.fixture
def spookyrouter(interface):
    token_address = "0xF491e7B69E4244ad4002BC14e878a34207E38c29"
    yield interface.IUniswapV2Router02(token_address)

#@pytest.fixture
#def weth_amount(user, weth):
#    weth_amount = 10 ** weth.decimals()
#    user.transfer(weth, weth_amount)
#    yield weth_amount


@pytest.fixture(scope="function", autouse=True)
def vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian, management)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})
    yield vault


@pytest.fixture(scope="session")
def registry():
    yield Contract("0x727fe1759430df13655ddb0731dE0D0FDE929b04")


@pytest.fixture(scope="session")
def live_vault(registry, token):
    yield registry.latestVault(token)


@pytest.fixture
def reentry_test(user, ReentryTest):
    reentry_test = user.deploy(ReentryTest)
    yield reentry_test


@pytest.fixture
def strategy(strategist, keeper, vault, Strategy, gov, cToken, spookyrouter, ib, ibComptroller, weth):
    strategy = strategist.deploy(Strategy, vault, cToken,spookyrouter, ib, ibComptroller, weth, 1)
    strategy.setKeeper(keeper)
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    yield strategy


@pytest.fixture
def factory(LevCompFactory, vault, cToken, strategist, gov, spookyrouter, ib, ibComptroller, weth):
    factory = strategist.deploy(LevCompFactory, vault, cToken,spookyrouter, ib, ibComptroller, weth, 1)
    yield factory


@pytest.fixture
def cloned_strategy(factory, vault, Strategy, strategy, cToken, strategist, gov):
    # TODO: customize clone method and arguments
    # TODO: use correct contract name (i.e. replace Strategy)
    cloned_strategy = factory.cloneLevComp(
        vault, cToken, {"from": strategist}
    ).return_value
    cloned_strategy = Strategy.at(cloned_strategy)
    vault.revokeStrategy(strategy)
    vault.addStrategy(cloned_strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    yield


#@pytest.fixture(autouse=True)
def withdraw_no_losses(vault, token, amount, user):
    yield
    if vault.totalSupply() == 0:
        return
    if vault.balanceOf(user) == 0:
        print(f"TotalSupplyVault: {vault.totalSupply()}")
        return
    vault.withdraw({"from": user})


@pytest.fixture(scope="session", autouse=True)
def RELATIVE_APPROX():
    yield 1e-5

