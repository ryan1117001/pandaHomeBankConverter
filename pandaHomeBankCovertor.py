#! /user/bin/env python3

import argparse
import xlrd
from datetime import datetime
import pandas as pd
import numpy as np


def amexCCConversion(filename):
    inputDataDict = pd.read_csv(filename).to_dict('records')
    data = []
    # Date,Reference,Description,Card Member,Card Number,Amount,Category,Type
    for row in inputDataDict:
        data.append([row['Date'], None, None, row['Description'], None,
                     -1*row['Amount'],
                     None, None])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('convertedfiles/amexHomeBank.csv', index=False, sep=";")

def boaCAConversion(filename):
    inputDataDict = pd.read_csv(filename, skiprows=6).to_dict('records')
    data = []
    for row in inputDataDict:
        if pd.notnull(row[2]):
            # Date,Description,Amount,Running Bal.
            data.append([row['Date'], None, None, row['Description'], None, row['Amount'], None, None])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('convertedfiles/boaHomeBank.csv', index=False, sep=";")

def earnestConversion(filename):
    inputDataDict = pd.read_html(filename)[0].to_dict('records')
    data = []
    # Date,Loan,Description, Principal, Interest, Fees, Total, Unpaid Principal
    for row in inputDataDict:
        if row['Description'] == "PAYMENT":
            # Just the loan
            data.append([row['Date'], None, None, "Ryan Hua", None,
                         row['Total'][2:],
                         "Loan Payment", None])
            # Just the interest
            data.append([row['Date'], None, None, "Earnest", None,
                         "-" + row['Interest'][2:],
                         "Loan Interest", None])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('convertedfiles/earnestHomeBank.csv', index=False, sep=";")

def vanguardRothConversion(filename):
    inputDataDict = pd.read_csv(filename, 
    names=[
        "Account Number", "Trade Date", "Settlement Date", "Transaction Type", "Transaction Description", 
        "Investment Name", "Symbol", "Shares", "Share Price", "Principal Amount", "Commission Fees", 
        "Net Amount", "Accrued Interest", "Account Type"
    ]).to_dict('records')
    data = []
    for row in inputDataDict:
        if (pd.notnull((row["Account Type"]) or row["Account Type"] == "Account Type")) and vanguardRothLogic(row['Transaction Type']):
                data.append([row["Settlement Date"], 0, row["Transaction Description"], "Vanguard", 
                                None,row["Principal Amount"],None,None])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('convertedfiles/vanguardRothHomeBank.csv', index=False, sep=";")

def vanguardRothLogic(rowType):
    if rowType== 'Dividend':
        return True
    elif rowType== 'Contribution':
        return True
    elif rowType== 'Capital gain (LT)':
        return True
    elif rowType== 'Capital gain (ST)':
        return True
    else:
        return False

def vanguard401KConversion(filename):
    inputDataDict = pd.read_csv(filename,
    names=[
        "Account Number", "Trade Date", "Run Date", "Transaction Activity", "Transaction Description", 
        "Investment Name", "Share Price", "Transaction Shares", "Dollar Amount"
    ]).to_dict('records')
    data = []
    for row in inputDataDict:
        if pd.notnull(row['Dollar Amount']) and vanguard401KLogic(row['Transaction Description']):
            data.append([
                row['Run Date'], None, row['Transaction Description'], 'Vanguard', None, row['Dollar Amount'], None, row['Investment Name']
            ])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('convertedfiles/vanguard401KHomeBank.csv', index=False, sep=";")

def vanguard401KLogic(rowType):
    if rowType == 'Plan Contribution':
        return True
    elif rowType == 'Dividends on Equity Investments':
        return True
    else:
        return False

def venmoConversion(filename):
    inputDataDict = pd.read_csv(filename).to_dict('records')
    data = []
    for row in inputDataDict:
        # Username,ID,Datetime,Type,Status,Note,From,To,Amount (total),
        # Amount (fee),Funding Source,Destination,Beginning Balance,
        # Ending Balance,Statement Period Venmo Fees,Year to Date Venmo Fees,Disclaimer
        if pd.notnull(row['Amount (total)']):
            dateobj = datetime.strptime(row['Datetime'], "%Y-%m-%dT%H:%M:%S")
            data.append([
                dateobj.strftime("%m/%d/%Y"),
                None, row['Note'], 
                venmoLogic(row),
                "Venmo " + row['Type'],
                row['Amount (total)'], None, None])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv('convertedfiles/venmoHomeBank.csv', index=False, sep=";")

def venmoLogic(row):
    if row['Type'] == "Charge":
        return row['To']
    elif row['Type'] == "Standard Transfer":
        return "Ryan Hua"
    elif row['Type'] == "Payment":
        return row['From']
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
