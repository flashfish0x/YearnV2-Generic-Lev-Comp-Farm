from itertools import count
from brownie import Wei, reverts
from utils import actions, checks, utils
from useful_methods import (
    stateOfStrat,
    stateOfVault,
    genericStateOfStrat,
    genericStateOfVault
)
import pytest



def test_apr_wftm(
    chain,
    accounts,
    token,
    vault,
    strategy,
    interface,
    user,
    strategist,
    gov,
    amount,
    RELATIVE_APPROX,
):
    
    # Deposit to the vault
    #gov = accounts.at(vault.governance(), force=True)
    comp = interface.ERC20(strategy.comp())
    user_balance_before = token.balanceOf(user)
    actions.user_deposit(user, vault, token, amount)

    # harvest
    chain.sleep(1)
    strategy.harvest({"from": strategist})

    strategy.setProfitFactor(1, {"from": gov})
    #assert enormousrunningstrategy.profitFactor() == 1
    vault.setManagementFee(0, {"from": gov}) # set management fee to 0 so that time works
    

    strategy.setMinCompToSell(0, {"from": gov})
    #enormousrunningstrategy.setMinWant(0, {"from": gov})
    #assert enormousrunningstrategy.minCompToSell() == 1
    strategy.harvest({"from": gov})
    start_time = chain.time()
    chain.sleep(25)

    print("mgm fee: ", vault.managementFee())
    print("perf fee: ", vault.performanceFee())

    startingBalance = vault.totalAssets()

    for i in range(6):

        waitBlock = 25
        print(f"\n----wait {waitBlock} blocks----")
        #wait(waitBlock, chain)
        chain.mine(waitBlock)
        ppsBefore = vault.pricePerShare()
        

        strategy.harvest({"from": gov})
        end_time = chain.time()
        #wait 6 hours. shouldnt mess up next round as compound uses blocks
        print("Locked: ", vault.lockedProfit())
        assert vault.lockedProfit() > 0 # some profit should be unlocked
        chain.sleep(21600)
        chain.mine(1)
        
        ppsAfter = vault.pricePerShare()

        #stateOfStrat(enormousrunningstrategy, dai, comp)
        # stateOfVault(vault, enormousrunningstrategy)

        profit = (vault.totalAssets() - startingBalance).to("ether")
        strState = vault.strategies(strategy)
        totalReturns = strState.dict()['totalGain']
        totaleth = totalReturns.to("ether")
        print(f"Real Profit: {profit:.5f}")
        difff = profit - totaleth
        print(f"Diff: {difff}")
        print(f"PPS: {ppsAfter}")

        print(f"PPS Diff: {ppsAfter - ppsBefore}")
        assert ppsAfter - ppsBefore > 0 # pps should have risen

        blocks_per_year = 3.154e+7
        assert startingBalance != 0
        time = (i + 1) * waitBlock
        assert time != 0
        ppsProfit = (ppsAfter - ppsBefore) / 1e18 / waitBlock * blocks_per_year
        apr = (totalReturns / startingBalance) * (blocks_per_year / time)
        time_apr = (totalReturns/startingBalance) * ((365*3600*24)/(end_time-start_time))
        print(f"implied apr assets: {apr:.8%}")
        print(f"implied apr pps: {ppsProfit:.8%}")
        print(f"implied apr time: {time_apr:.8%}")


    print(strategy.minWant()/1e18)
    stateOfStrat(strategy, token, comp)
