#! /user/bin/env python3

import argparse
import xlrd
from datetime import datetime
import pandas as pd
import numpy as np


def amexCCConversion(filename):
    inputDataFrame = pd.read_csv(filename)
    data = []
    # Date,Reference,Description,Card Member,Card Number,Amount,Category,Type
    for row in inputDataFrame.values:
        data.append([row[0], 1, None, row[2], None,
                     -1*row[5],
                     None, None])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('amexHomeBank.csv', index=False, sep=";")

def boaCAConversion(filename):
    inputDataFrame = pd.read_csv(filename, skiprows=6)
    data = []
    for row in inputDataFrame.values:
        if pd.notnull(row[2]):
            # Date,Description,Amount,Running Bal.
            data.append([row[0], 0, None, row[1], None, row[2], None, None])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('boaHomeBank.csv', index=False, sep=";")

def earnestConversion(filename):
    inputDataFrame = pd.read_html(filename)
    data = []
    # Date,Loan,Description, Principal, Interest, Fees, Total, Unpaid Principal
    for row in inputDataFrame[0].values:
        if row[2] == "PAYMENT":
            # Just the loan
            data.append([row[0], 10, None, "Ryan Hua", None,
                         row[6][2:],
                         "Loan Payment", None])
            # Just the interest
            data.append([row[0], 10, None, "Earnest", None,
                         "-" + row[4][2:],
                         "Loan Interest", None])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('earnestHomeBank.csv', index=False, sep=";")

def vanguardRothConversion(filename):
    inputDataFrame = pd.read_csv(filename, 
    names=[
        "Account Number", "Trade Date", "Settlement Date", "Transaction Type", "Transaction Description", 
        "Investment Name", "Symbol", "Shares", "Share Price", "Principal Amount", "Commission Fees", 
        "Net Amount", "Accrued Interest", "Account Type"
        ])
    data = []
    for row in inputDataFrame.values:
        if pd.notnull((row[13]) or row[13] == "Account Type"):
            data.append([row[2], 0, row[4], "Vanguard", None,row[9],None,None])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('vanguardRothHomeBank.csv', index=False, sep=";")

def vanguard401KConversion(filename):
    inputDataFrame = pd.read_csv(filename,
    names=[
        "Account Number", "Trade Date", "Run Date", "Transaction Activity", "Transaction Description", 
        "Investment Name", "Share Price", "Transaction Shares", "Dollar Amount"
    ])
    data = []
    for row in inputDataFrame.values:
        if pd.notnull(row[8]):
            data.append([
                row[2], None, row[4], "Vanguard", None, row[8], None, row[5]
            ])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('vanguard401KHomeBank.csv', index=False, sep=";")

def venmoConversion(filename):
    inputDataFrame = pd.read_csv(filename)
    data = []
    # print(inputDataFrame)
    for row in inputDataFrame.values:
        # Username,ID,Datetime,Type,Status,Note,From,To,Amount (total),
        # Amount (fee),Funding Source,Destination,Beginning Balance,
        # Ending Balance,Statement Period Venmo Fees,Year to Date Venmo Fees,Disclaimer
        if pd.notnull(row[8]):
            dateobj = datetime.strptime(row[2], "%Y-%m-%dT%H:%M:%S")
            data.append([
                dateobj.strftime("%m/%d/%Y"),
                None, row[5], 
                venmoLogic(row),
                "Venmo " + row[3],
                row[8], None, None])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('venmoHomeBank.csv', index=False, sep=";")

def venmoLogic(row):
    if row[3] == "Charge":
        return row[7]
    elif row[3] == "Standard Transfer":
        return "Ryan Hua"
    elif row[3] == "Payment":
        return row[6]
    else:
        return None
def main():
    parser = argparse.ArgumentParser(
        description="Convert data files from online banking sites to Homebank compatible CSV formats")
    parser.add_argument("filename", help="The file to convert.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--amex", action="store_true",
                       help="convert an American Express credit card account CSV file")
    group.add_argument("--boa", action="store_true",
                       help="convert a Bank of America checking account CSV file")
    group.add_argument("--earnest", action="store_true",
                       help="convert an Earnest xlsx file")
    group.add_argument("--venmo", action="store_true",
                       help="convert an Venmo csv file")
    group.add_argument("--vanguardRoth", action="store_true",
                       help="convert an Vanguard csv file")
    group.add_argument("--vanguard401K", action="store_true",
                       help="convert an Vanguard csv file")

    args = parser.parse_args()

    if args.amex:
        amexCCConversion(args.filename)
        print("AMEX file converted. Output file: 'amexHomeBank.csv'")
    elif args.boa:
        boaCAConversion(args.filename)
        print("BOA CA file converted. Output file 'boaHomeBank.csv'")
    elif args.earnest:
        earnestConversion(args.filename)
        print("Earnest file converted. Output file 'earnestHomeBank.csv'")
    elif args.venmo:
        venmoConversion(args.filename)
        print("Venmo file converted. Output file 'venmoHomeBank.csv'")
    elif args.vanguardRoth:
        vanguardRothConversion(args.filename)
        print("Vanguard Roth file converted. Output file 'vanguardRothHomeBank.csv'")
    elif args.vanguard401K:
        vanguard401KConversion(args.filename)
        print("Vanguard 401k file converted. Output file 'vanguard401kHomeBank.csv")
    else:
        print("You must provide the arg for which banking site the csv file comes from")


if __name__ == '__main__':
    main()
