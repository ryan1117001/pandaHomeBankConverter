#! /user/bin/env python3

import argparse
import xlrd
from datetime import datetime
import pandas as pd
import os
import shutil
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

unixFilesPath = os.getcwd() + config["FilePaths"]["unixFilesPath"]
unixConvertedPath = os.getcwd() + config["FilePaths"]["unixConvertedPath"]
windowsFilesPath = os.getcwd() + config["FilePaths"]["windowsFilesPath"]
windowsConvertedPath = os.getcwd() + config["FilePaths"]["windowsConvertedPath"]
user = config["User"]["username"]
homeBankCols = config["HomeBank"]["homeBankCols"].split(sep=",")
amexHeaders = config["CSVHeaders"]["amexHeaders"].split(sep=",")
boaHeaders = config["CSVHeaders"]["boaHeaders"].split(sep=",")
earnestHeaders = config["CSVHeaders"]["earnestHeaders"].split(sep=",")
vanguardRothHeaders = config["CSVHeaders"]["vanguardRothHeaders"].split(sep=",")
vanguard401KHeaders = config["CSVHeaders"]["vanguard401KHeaders"].split(sep=",")
venmoHeaders = config["CSVHeaders"]["venmoHeaders"].split(sep=",")
paypalHeaders = config["CSVHeaders"]["paypalHeaders"].split(sep=",")

def amexCCConversion(filename):
    try:
        inputDataDict = pd.read_csv(filepath_or_buffer=filename, header=0)
        if all(inputDataDict.columns == amexHeaders):
            inputDataDict = inputDataDict.to_dict("records")
    except:
        raise Exception
    data = []
    for row in inputDataDict:
        if pd.notna:
            data.append([row["Date"], None, None, row["Description"], None,
                         -1*row["Amount"],
                         None, None])
    outputDataFrame = pd.DataFrame(data=data, columns=homeBankCols)
    outputDataFrame.to_csv(
        "convertedfiles/amexHomeBank.csv", index=False, sep=";")


def boaCAConversion(filename):
    try:
        inputDataDict = pd.read_csv(filepath_or_buffer=filename, header=5)
        if all(inputDataDict.columns == boaHeaders):
            inputDataDict = inputDataDict.to_dict("records")
    except:
        raise Exception
    data = []
    for row in inputDataDict:
        data.append([row["Date"], None, None, row["Description"],
                        None, row["Amount"], None, None])
    outputDataFrame = pd.DataFrame(data=data, columns=homeBankCols)
    outputDataFrame.to_csv(
        "convertedfiles/boaHomeBank.csv", index=False, sep=";")


def earnestConversion(filename):
    inputDataDict = pd.read_html(io=filename)[0]
    try:
        if all(inputDataDict.columns == earnestHeaders):
            inputDataDict = pd.read_html(io=filename)[0].to_dict("records")
    except:
        raise Exception
    data = []
    for row in inputDataDict:
        # Just the loan
        data.append([row["Date"], None, None, user, None,
                        row["Total"][2:],
                        "Loan Payment", None])
        # Just the interest
        data.append([row["Date"], None, None, "Earnest", None,
                        "-" + row["Interest"][2:],
                        "Loan Interest", None])
    outputDataFrame = pd.DataFrame(data=data, columns=homeBankCols)
    outputDataFrame.to_csv(
        "convertedfiles/earnestHomeBank.csv", index=False, sep=";")


def vanguardRothConversion(filename):
    try:
        inputDataDict = pd.read_csv(filepath_or_buffer=filename,header=3)
        inputDataDict = inputDataDict.loc[:, ~inputDataDict.columns.str.contains('^Unnamed')]
        if all(inputDataDict.columns == vanguardRothHeaders):
            inputDataDict = inputDataDict.to_dict("records")
    except:
        raise Exception
    data = []
    for row in inputDataDict:
        if vanguardRothLogic(row["Transaction Type"]):
            data.append([row["Settlement Date"], 0, row["Transaction Description"], "Vanguard",
                         None, row["Principal Amount"], None, None])
    outputDataFrame = pd.DataFrame(data=data, columns=homeBankCols)
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
    try:
        inputDataDict = pd.read_csv(filepath_or_buffer=filename,header=13)
        inputDataDict = inputDataDict.loc[:, ~inputDataDict.columns.str.contains('^Unnamed')]
        if all(inputDataDict.columns == vanguard401KHeaders):
            inputDataDict = inputDataDict.to_dict("records") 
    except:
        raise Exception
    data = []
    for row in inputDataDict:
        if vanguard401KLogic(row["Transaction Description"]):
            data.append([
                row["Run Date"], None, row["Transaction Description"], 
                "Vanguard", None, row["Dollar Amount"], None, row["Investment Name"]
            ])
    outputDataFrame = pd.DataFrame(data=data, columns=homeBankCols)
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
    try:
        dateParser = lambda x: pd.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
        inputDataDict = pd.read_csv(filepath_or_buffer=filename,header=0)
        inputDataDict["Datetime"] = pd.to_datetime(inputDataDict["Datetime"],format="%Y-%m-%dT%H:%M:%S")
        if all(inputDataDict.columns == venmoHeaders):
            inputDataDict = inputDataDict.to_dict("records")
    except:
        raise Exception
    data = []
    for row in inputDataDict:
        if pd.notnull(row["Amount (total)"]):
            data.append([
                row["Datetime"].strftime("%m/%d/%Y"),
                None, row["Note"],
                venmoLogic(row),
                "Venmo " + row["Type"],
                row["Amount (total)"], None, None])
    outputDataFrame = pd.DataFrame(data=data, columns=homeBankCols)
    outputDataFrame.to_csv(
        "convertedfiles/venmoHomeBank.csv", index=False, sep=";")


def paypalConversion(filename):
    try:
        inputDataDict = pd.read_csv(filepath_or_buffer=filename, header=0)
        if all(inputDataDict.columns == paypalHeaders):
            inputDataDict = inputDataDict.to_dict("records")
    except:
        raise Exception
    data = []
    for row in inputDataDict:
        if pd.notnull(row["Amount"]):
            data.append([
                row["Date"],
                None, row["Type"],
                row["Name"] if pd.notnull(
                    row["Name"]) else paypalLogic(row["Type"]),
                None, row["Amount"], None, None])
    if len(data) == 0:
        raise Exception()
    outputDataFrame = pd.DataFrame(data=data, columns=homeBankCols)
    outputDataFrame.to_csv(
        "convertedfiles/paypalHomeBank.csv", index=False, sep=";")


def paypalLogic(type_name):
    if type_name == "General Credit Card Deposit":
        return "Paypal"
    else:
        return None


def init():
    try:
        os.mkdir("files")
        os.mkdir("convertedfiles")
        print("Init success")
    except:
        print("Init failed")


def runAll():
    print("Running all possible conversions")
    cwd = ""
    try:
        if os.name == "nt":
            fileList = os.listdir(windowsFilesPath)
            cwd = windowsFilesPath + "\\"
        else:
            fileList = os.listdir(unixFilesPath)
            cwd = unixFilesPath + "/"
    except:
        raise Exception

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
        try:
            paypalConversion(filePath)
            print(file + " is paypal")
        except:
            print(file + " is not paypal")


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
                                      description="Convert data files from online banking sites to Homebank compatible CSV formats. Default is to run all")
    parser1.add_argument("--clean", action="store_true",
                         help="deletes the \'convertedfiles\' and \'files\' directories and its contents")
    parser1.add_argument("--init", action="store_true",
                         help="initialize the directories by creating the \'convertedfiles\' and \'files\' directories ")
    parser2 = argparse.ArgumentParser(parents=[parser1])
    group = parser2.add_mutually_exclusive_group()
    group.add_argument("--amex", nargs=1,
                       help="convert an American Express credit card account CSV file",)
    group.add_argument("--boa", nargs=1,
                       help="convert a Bank of America checking account CSV file")
    group.add_argument("--earnest", nargs=1,
                       help="convert an Earnest xlsx file")
    group.add_argument("--venmo", nargs=1,
                       help="convert a Venmo csv file")
    group.add_argument("--vRoth", nargs=1,
                       help="convert a Vanguard Roth csv file")
    group.add_argument("--v401k", nargs=1,
                       help="convert a Vanguard 401K csv file")
    group.add_argument("--paypal", nargs=1,
                       help="convert a Paypal csv file")

    args = parser2.parse_args()

    if args.clean:
        clean()
    elif args.init:
        init()
    elif args.amex:
        amexCCConversion(args.amex[0])
        print("AMEX file converted. Output file: amexHomeBank.csv")
    elif args.boa:
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
    elif args.paypal:
        paypalConversion(args.paypal[0])
        print("Paypal file converted. Output file: paypalHomeBank.csv")
    else:
        runAll()


if __name__ == "__main__":
    main()
