import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import csv

interbankExposure = pd.read_csv('interbankExposures.csv', header=None)
bankEquities = pd.read_csv('bankEquities.csv', header=None)
bank_asset_weighted_network = pd.read_csv(
    'bankAssetWeightedNetwork.csv', header=None)

G = nx.DiGraph(interbankExposure.values)
nnodes = G.number_of_nodes()  # 145
out_degrees = [G.out_degree(n) for n in G.nodes()]
in_degrees = [G.in_degree(n) for n in G.nodes()]

in_Degree = pd.DataFrame(G.in_degree(weight='weight'))
in_Degree = in_Degree.T

out_Degree = pd.DataFrame(G.out_degree(weight='weight'))
out_Degree = out_Degree.T

external_liability = pd.DataFrame(index=range(1), columns=range(145))
external_liability = external_liability.add(in_Degree.loc[1], axis=1)
external_liability = external_liability.sub(out_Degree.loc[1], axis=1)
external_liability = external_liability.sub(bankEquities.loc[0], axis=1)
external_liability = external_liability.T

notdefaulted_external_liability = external_liability[external_liability[:] > 0].dropna(
    axis=1)
defaulted_external_liability = external_liability[external_liability[:] <= 0].dropna(
    axis=1)

initial_bank_equities = bankEquities.copy()
shock = 1000000
for i in bankEquities:
    bankEquities[i] = bankEquities[i] - shock

notdefaulters = bankEquities[bankEquities.iloc[0:] > 0]
notdefaulters = notdefaulters.dropna(axis=1)
defaulters = bankEquities[bankEquities.iloc[0:] <= 0]
defaulters = defaulters.dropna(axis=1)

notdefaulted_external_asset = bank_asset_weighted_network.reindex(
    notdefaulters.columns, axis=1)
defaulter_external_assets = bank_asset_weighted_network.reindex(
    defaulters.columns, axis=1)
ratio = 1 - (defaulter_external_assets.sum(axis=1) /
             bank_asset_weighted_network.sum(axis=1))

newBankEquity = pd.DataFrame(index=range(1), columns=range(145))
newbanklist = pd.DataFrame(index=range(1), columns=range(145))
defaulteroutDegree = pd.DataFrame(index=range(1), columns=range(145))
notdefaulted_external_asset = pd.DataFrame(index=range(1), columns=range(145))

notdefaulted_external_asset = bank_asset_weighted_network.reindex(
    notdefaulters.columns, axis=1)
newBankEquity = newBankEquity.sub(
    notdefaulted_external_liability, fill_value=0)
newBankEquity = newBankEquity.add(notdefaulted_external_asset, fill_value=0)

recovery_rate = 0.5  # 0.5 = 50% recovery rate


def furfine(defaulters, notdefaulters, newBankEquity, newbanklist, defaulteroutDegree, interbankExposure, bank_asset_weighted_network, external_liability, in_Degree, out_Degree, recovery_rate):
    notdefaulters_inDegree = in_Degree.reindex(notdefaulters.columns, axis=1)
    notdefaulters_outDegree = out_Degree.reindex(notdefaulters.columns, axis=1)

    for i in defaulters:
        sumDebt = sum(interbankExposure.loc[i, 0:]) * (1 - recovery_rate)
        defaulteroutDegree[i] = sumDebt

    newBankEquity = newBankEquity.sub(defaulteroutDegree, fill_value=0)
    newBankEquity = pd.DataFrame(
        notdefaulters_inDegree.loc[1] + newBankEquity.loc[0])
    newBankEquity = pd.DataFrame(
        newBankEquity[0] - notdefaulters_outDegree.loc[1]).T
    newbanklist = newBankEquity[newBankEquity[:] > 0].dropna(axis=1)

    lenDefaulter = len(newBankEquity[newBankEquity[:] <= 0].dropna(axis=1))
    if len(defaulters) == lenDefaulter:
        return notdefaulters
    else:
        newBankEquity = newbanklist
        defaulters = newBankEquity[newBankEquity[:] <= 0].dropna(axis=0)
        notdefaulters = newBankEquity[newBankEquity[:] > 0].dropna(axis=0)
        return furfine(defaulters, notdefaulters, newBankEquity, newbanklist, defaulteroutDegree, interbankExposure, bank_asset_weighted_network, external_liability, in_Degree, out_Degree)


x = furfine(defaulters, notdefaulters, newBankEquity, newbanklist, defaulteroutDegree, interbankExposure,
            bank_asset_weighted_network, external_liability, in_Degree, out_Degree, recovery_rate)

print(x)

# print the number of banks that are not defaulted
print(len(x.columns))

final_bank_equities = pd.DataFrame(index=range(1), columns=range(145))

final_bank_equities.update(x)
final_bank_equities.fillna(0, inplace=True)

bank_losses = initial_bank_equities - final_bank_equities

print("Initial Bank Equities: ")
print(initial_bank_equities)
print("Bank Losses:")
print(bank_losses)
