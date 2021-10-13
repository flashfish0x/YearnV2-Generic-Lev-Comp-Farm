import brownie
from brownie import interface
from pytest import approx

# This file is reserved for standard checks
def check_vault_empty(vault):
    assert vault.totalAssets() == 0
    assert vault.totalSupply() == 0


def check_strategy_empty(strategy):
    assert strategy.estimatedTotalAssets() == 0
    vault = interface.VaultAPI(strategy.vault())
    assert vault.strategies(strategy).dict()["totalDebt"] == 0


def check_revoked_strategy(vault, strategy):
    status = vault.strategies(strategy).dict()
    assert status.debtRatio == 0
    assert status.totalDebt == 0
    return


def check_harvest_profit(tx, profit_amount):
    # profits are understimated so we need to be a lot more tolerant
    assert tx.events["Harvested"]["profit"] == approx(profit_amount, rel=1e-1)


def check_harvest_loss(tx, loss_amount):
    assert tx.events["Harvested"]["loss"] == approx(loss_amount, rel=1e-2)


def check_accounting(vault, strategy, totalGain, totalLoss, totalDebt):
    # inputs have to be manually calculated then checked
    status = vault.strategies(strategy).dict()
    assert status["totalGain"] == totalGain
    assert status["totalLoss"] == totalLoss
    assert status["totalDebt"] == totalDebt
    return
