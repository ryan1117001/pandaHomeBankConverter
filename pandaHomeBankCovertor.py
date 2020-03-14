#! /user/bin/env python3

import argparse
import xlrd
from datetime import datetime
import pandas as pd
import numpy as np
import os
import shutil

unixFilesPath = os.getcwd() + "/files"
unixConvertedPath = os.getcwd() + "/convertedfiles"
windowsFilesPath = os.getcwd() + "\\files"
windowsConvertedPath = os.getcwd() + "\\convertedfiles"
user = "Ryan Hua"

def amexCCConversion(filename):
    inputDataDict = pd.read_csv(filename).to_dict("records")
    data = []
    # Date,Reference,Description,Card Member,Card Number,Amount,Category,Type
    for row in inputDataDict:
        if pd.notnull(row["Amount"]):
            data.append([row["Date"], None, None, row["Description"], None,
                         -1*row["Amount"],
                         None, None])
    if len(data) == 0:
        raise Exception()
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv(
        "convertedfiles/amexHomeBank.csv", index=False, sep=";")


def boaCAConversion(filename):
    inputDataDict = pd.read_csv(filename, skiprows=6).to_dict("records")
    data = []
    for row in inputDataDict:
        if pd.notnull(row["Running Bal."]):
            # Date,Description,Amount,Running Bal.
            data.append([row["Date"], None, None, row["Description"],
                         None, row["Amount"], None, None])
    if len(data) == 0:
        raise Exception()
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv(
        "convertedfiles/boaHomeBank.csv", index=False, sep=";")


def earnestConversion(filename):
    inputDataDict = pd.read_html(filename)[0].to_dict("records")
    data = []
    # Date,Loan,Description, Principal, Interest, Fees, Total, Unpaid Principal
    for row in inputDataDict:
        if row["Description"] == "PAYMENT" and pd.notnull(row["Total"]):
            # Just the loan
            data.append([row["Date"], None, None, user, None,
                         row["Total"][2:],
                         "Loan Payment", None])
            # Just the interest
            data.append([row["Date"], None, None, "Earnest", None,
                         "-" + row["Interest"][2:],
                         "Loan Interest", None])
    if len(data) == 0:
        raise Exception()
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv(
        "convertedfiles/earnestHomeBank.csv", index=False, sep=";")


def vanguardRothConversion(filename):
    inputDataDict = pd.read_csv(filename,
                                names=[
                                    "Account Number", "Trade Date", "Settlement Date", "Transaction Type", "Transaction Description",
                                    "Investment Name", "Symbol", "Shares", "Share Price", "Principal Amount", "Commission Fees",
                                    "Net Amount", "Accrued Interest", "Account Type"
                                ]).to_dict("records")
    data = []
    for row in inputDataDict:
        if (pd.notnull((row["Account Type"]) or row["Account Type"] == "Account Type")) and vanguardRothLogic(row["Transaction Type"]):
            data.append([row["Settlement Date"], 0, row["Transaction Description"], "Vanguard",
                         None, row["Principal Amount"], None, None])
    if len(data) == 0:
        raise Exception()
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv(
        "convertedfiles/vanguardRothHomeBank.csv", index=False, sep=";")


def vanguardRothLogic(rowType):
    if rowType == "Dividend":
        return True
    elif rowType == "Contribution":
        return True
    elif rowType == "Capital gain (LT)":
        return True
    elif rowType == "Capital gain (ST)":
        return True
    else:
        return False


def vanguard401KConversion(filename):
    inputDataDict = pd.read_csv(filename,
                                names=[
                                    "Account Number", "Trade Date", "Run Date", "Transaction Activity", "Transaction Description",
                                    "Investment Name", "Share Price", "Transaction Shares", "Dollar Amount"
                                ]).to_dict("records")
    data = []
    for row in inputDataDict:
        if pd.notnull(row["Dollar Amount"]) and vanguard401KLogic(row["Transaction Description"]):
            data.append([
                row["Run Date"], None, row["Transaction Description"], "Vanguard", None, row["Dollar Amount"], None, row["Investment Name"]
            ])
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    if len(data) == 0:
        raise Exception()
    outputDataFrame.to_csv(
        "convertedfiles/vanguard401KHomeBank.csv", index=False, sep=";")


def vanguard401KLogic(rowType):
    if rowType == "Plan Contribution":
        return True
    elif rowType == "Dividends on Equity Investments":
        return True
    else:
        return False


def venmoConversion(filename):
    inputDataDict = pd.read_csv(filename).to_dict("records")
    data = []
    for row in inputDataDict:
        # Username,ID,Datetime,Type,Status,Note,From,To,Amount (total),
        # Amount (fee),Funding Source,Destination,Beginning Balance,
        # Ending Balance,Statement Period Venmo Fees,Year to Date Venmo Fees,Disclaimer
        if pd.notnull(row["Amount (total)"]):
            dateobj = datetime.strptime(row["Datetime"], "%Y-%m-%dT%H:%M:%S")
            data.append([
                dateobj.strftime("%m/%d/%Y"),
                None, row["Note"],
                venmoLogic(row),
                "Venmo " + row["Type"],
                row["Amount (total)"], None, None])
    if len(data) == 0:
        raise Exception()
    outputDataFrame = pd.DataFrame(data=data, columns=[
                                   "date", "payment", "info", "payee",
                                   "memo", "amount", "category", "tags"])
    outputDataFrame.to_csv(
        "convertedfiles/venmoHomeBank.csv", index=False, sep=";")


def init():
    try:
        os.mkdir("files")
        os.mkdir("convertedfiles")
        print("Init success")
    except:
        print("Init failed")


def runAll():
    print("running all")
    cwd = ""
    if os.name == "nt":
        fileList = os.listdir(windowsFilesPath)
        cwd = windowsFilesPath + "\\"
    else:
        fileList = os.listdir(unixFilesPath)
        cwd = unixFilesPath + "/"
    for file in fileList:
        filePath = cwd + file
        try:
            amexCCConversion(filePath)
            print(file + " is amexCC")
        except:
            print(file + " is not amexCC")
        try:
            boaCAConversion(filePath)
            print(file + " is boaCA")
        except:
            print(file + " is not boaCA")
        try:
            earnestConversion(filePath)
            print(file + " is earnest")
        except:
            print(file + " is not earnest")
        try:
            vanguardRothConversion(filePath)
            print(file + " is vanguardRoth")
        except:
            print(file + " is not vanguardRoth")
        try:
            vanguard401KConversion(filePath)
            print(file + " is vanguard401k")
        except:
            print(file + " is not vanguard401k")
        try:
            venmoConversion(filePath)
            print(file + " is venmo")
        except:
            print(file + " is not venmo")


def clean():
    try:
        if os.name == "nt":
            shutil.rmtree(windowsFilePath)
            shutil.rmtree(windowsConvertedPath)
        else:
            shutil.rmtree(unixFilesPath)
            shutil.rmtree(unixConvertedPath)
        print("Directories have been removed")
    except:
        print("Directories were not cleaned")


def venmoLogic(row):
    if row["Type"] == "Charge":
        return row["To"]
    elif row["Type"] == "Standard Transfer":
        return user
    elif row["Type"] == "Payment":
        return row["From"]
    else:
        return None


def main():
    parser1 = argparse.ArgumentParser(add_help=False,
                                      description="Convert data files from online banking sites to Homebank compatible CSV formats")
    parser1.add_argument("--clean", action="store_true",
                         help="clean the directory")
    parser1.add_argument("--init", action="store_true",
                         help="init the directory")
    parser2 = argparse.ArgumentParser(parents=[parser1])
    group = parser2.add_mutually_exclusive_group()
    group.add_argument("--amex", nargs=1,
                       help="convert an American Express credit card account CSV file",)
    group.add_argument("--boa", nargs=1,
                       help="convert a Bank of America checking account CSV file")
    group.add_argument("--earnest", nargs=1,
                       help="convert an Earnest xlsx file")
    group.add_argument("--venmo", nargs=1,
                       help="convert an Venmo csv file")
    group.add_argument("--vRoth", nargs=1,
                       help="convert an Vanguard Roth csv file")
    group.add_argument("--v401k", nargs=1,
                       help="convert an Vanguard 401K csv file")

    args = parser2.parse_args()
    if args.clean:
        clean()
    elif args.init:
        init()
    elif args.amex:
        amexCCConversion(args.amex[0])
        print("AMEX file converted. Output file: amexHomeBank.csv")
    elif args.boa:
        print(args.boa)
        boaCAConversion(args.boa[0])
        print("BOA CA file converted. Output file: boaHomeBank.csv")
    elif args.earnest:
        earnestConversion(args.earnest[0])
        print("Earnest file converted. Output file: earnestHomeBank.csv")
    elif args.venmo:
        venmoConversion(args.venmo[0])
        print("Venmo file converted. Output file: venmoHomeBank.csv")
    elif args.vRoth:
        vanguardRothConversion(args.vRoth[0])
        print("Vanguard Roth file converted. Output file: vanguardRothHomeBank.csv")
    elif args.v401k:
        vanguard401KConversion(args.v401k[0])
        print("Vanguard 401k file converted. Output file: vanguard401kHomeBank.csv")
    else:
        runAll()
        print("All files have been converted")


if __name__ == "__main__":
    main()
