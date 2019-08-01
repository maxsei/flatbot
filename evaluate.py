import os
import pandas as pd


csvs = os.listdir("episodes/first_training/")
csvs = list(map(lambda x: x, csvs))

hit_squences = pd.DataFrame()

for csv in csvs:
    # print(csv)
    df = pd.read_csv("episodes/first_training/%s" % csv)
    # print(df.loc[len(df) - 1]["p1.falls"])
    shifted = df.shift(-1, axis=0)
    # print(shifted.head())
    # print(df.head())
    percentage_changes = shifted.loc[
        df["p1.percentage"] != shifted["p1.percentage"]
    ].dropna()
    hit_squences = pd.concat([hit_squences, percentage_changes])

hit_squences.to_csv("hit_squences.csv")
