# -*- coding: utf-8 -*-
"""
Created on Tue Aug 24 13:33:16 2021

@author: omar_
"""
''' The goal is to have this script to monitor our ticker pos with a partial stoploss 
    - After initial buy you set a stop limit for max loss of x sum
    - but have a partial stop loss to stay in the trade by selling partial at x and
        if the pos still against us we stop out by selling partial y'''

#import modules
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.execution import *
import pandas as pd
import time
import threading

#Create an application class(followed the tws api documentation)

class TradeApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        
        self.pos_df = pd.DataFrame(columns=['Account', 'Symbol', 'SecType',
                                            'Currency', 'Position', 'Avg cost'])
        
        self.order_df = pd.DataFrame(columns=['PermId', 'ClientId', 'OrderId',
                                  'Account', 'Symbol', 'SecType',
                                  'Exchange', 'Action', 'OrderType',
                                  'TotalQty', 'CashQty', 'LmtPrice',
                                  'AuxPrice', 'Status'])
        
        self.execution_df = pd.DataFrame(columns=['ReqId', 'PermId', 'Symbol',
                                          'SecType', 'Currency', 'ExecId',
                                          'Time', 'Account', 'Exchange',
                                          'Side', 'Shares', 'Price',
                                          'AvPrice', 'cumQty', 'OrderRef'])  
        self.order_ls = []
        self.last_price = {}
        self.contract_id = {}
        
##### wrapper function for reqMktData. this function handles streaming market data  (last current price)
    def tickPrice(self, reqId, tickType, price, attrib):    
        super().tickPrice(reqId, tickType, price, attrib)
        #print("TickPrice. TickerId:", reqId, "tickType:", tickType, "Price:", price)
        if tickType == 4:
            self.last_price[reqId] = price
            
####  wrapper function for reqIds. this function manages the Order ID.
    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)

        
        
#####   wrapper function for reqContractDetails. this function gives the contract ID for a given contract to be used in requesting PnL.
    def contractDetails(self, reqId, contractDetails):
        string = str(contractDetails.contract).split(",")
        if string[1] not in self.contract_id:
            self.contract_id[string[1]] = string[0]

#####   wrapper function for reqPositions.   this function gives the current positions
    def position(self, account, contract, position, avgCost):
            super().position(account, contract, position, avgCost)
            dictionary = {"Account":account, "Symbol": contract.symbol, "SecType": contract.secType,
                          "Currency": contract.currency, "Position": position, "Avg cost": avgCost}
            if self.pos_df["Symbol"].str.contains(contract.symbol).any():
                self.pos_df.loc[self.pos_df["Symbol"]==contract.symbol,"Position"]= dictionary["Position"]
                self.pos_df.loc[self.pos_df["Symbol"]==contract.symbol,"Avg cost"]= dictionary["Avg cost"]
            else:
                self.pos_df = self.pos_df.append(dictionary, ignore_index=True)

#####   wrapper function for reqExecutions.   this function gives the executed orders                
    def execDetails(self, reqId, contract, execution):
        super().execDetails(reqId, contract, execution)
        #print("ExecDetails. ReqId:", reqId, "Symbol:", contract.symbol, "SecType:", contract.secType, "Currency:", contract.currency, execution)
        dictionary = {"ReqId":reqId, "PermId":execution.permId, "Symbol":contract.symbol, "SecType":contract.secType, "Currency":contract.currency, 
                      "ExecId":execution.execId, "Time":execution.time, "Account":execution.acctNumber, "Exchange":execution.exchange,
                      "Side":execution.side, "Shares":execution.shares, "Price":execution.price,
                      "AvPrice":execution.avgPrice, "cumQty":execution.cumQty, "OrderRef":execution.orderRef}
        self.execution_df = self.execution_df.append(dictionary, ignore_index=True)
        
#### wrapper function for reqOpenOrders. this function gives the open orders
    def openOrder(self, orderId, contract, order, orderState):
        super().openOrder(orderId, contract, order, orderState)
        dictionary = {"PermId":order.permId, "ClientId": order.clientId, "OrderId": orderId, 
                      "Account": order.account, "Symbol": contract.symbol, "SecType": contract.secType,
                      "Exchange": contract.exchange, "Action": order.action, "OrderType": order.orderType,
                      "TotalQty": order.totalQuantity, "CashQty": order.cashQty, 
                      "LmtPrice": order.lmtPrice, "AuxPrice": order.auxPrice, "Status": orderState.status}
        self.order_df = self.order_df.append(dictionary, ignore_index=True)
        
def inExec(self,ticker):
    if len(self.execution_df[self.execution_df["Symbol"]==ticker]) == 0:
        return 0
    else:
        return -1 # -1 mean the order is executed

def usStk(symbol,sec_type="STK",currency="USD",exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract

def limitOrder(direction,quantity,lmt_price):
    order = Order()
    order.action = direction
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = lmt_price
    return order

def stoplimitOrder(direction,quantity,lmt_price,stp_price):
    order = Order()
    order.action = direction
    order.orderType = "STP LMT"
    order.totalQuantity = quantity
    order.lmtPrice = lmt_price
    order.auxPrice = stp_price
    return order

def stopMkt(direction,quantity,stp_price):
    order = Order()
    order.action = direction
    order.orderType = "STP"
    order.totalQuantity = quantity
    order.auxPrice = stp_price
    return order



####  this function starts the streaming data of current ticker.
def streamSnapshotData(req_num,contract):
    """stream tick leve data"""
    app.reqMktData(reqId=req_num, 
                   contract=contract,
                   genericTickList="",
                   snapshot=False,
                   regulatorySnapshot=False,
                   mktDataOptions=[])

####  this function refreshes the order dataframe				   
def OrderRefresh(app):
    app.order_df = pd.DataFrame(columns=['PermId', 'ClientId', 'OrderId',
                                      'Account', 'Symbol', 'SecType',
                                      'Exchange', 'Action', 'OrderType',
                                      'TotalQty', 'CashQty', 'LmtPrice',
                                      'AuxPrice', 'Status'])
    app.reqOpenOrders()
    time.sleep(2)


def execRefresh(app):
    app.execution_df = pd.DataFrame(columns=['ReqId', 'PermId', 'Symbol',
                                      'SecType', 'Currency', 'ExecId',
                                      'Time', 'Account', 'Exchange',
                                      'Side', 'Shares', 'Price',
                                      'AvPrice', 'cumQty', 'OrderRef'])  
    time.sleep(4)
    app.reqExecutions(23, ExecutionFilter())
    time.sleep(2)
    
    
############# function to establish the websocket connection to TWS ##########
def connection():
    app.run()

app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=23) #port 4002 for ib gateway paper trading/7497 for TWS paper trading

ConThread = threading.Thread(target=connection)
ConThread.start()

#### the algorithm.
#### Pre disposition is that we have done our qualitative & quantitative analysis
#### and are now ready to place a trade since the fundamental + techinicals lines up

ticker = 'AAPL' #manual input

#get info about the stock
app.reqContractDetails(ticker.index(ticker),usStk(ticker))
time.sleep(2)
# app.contract_id  


#get the streaming last price of the stock      
streamSnapshotData(ticker.index(ticker),usStk(ticker))
time.sleep(2)
# app.last_price  / app.last_price[0] This gives a loat / app.last_price.get(0)

limit_price = 147 # can change this to float num of your liking
pos_size = 10000
loss_1,loss_2 = 250,250
def cal_partial_sl(limit_price,pos_size,loss_1,loss_2):
    quantity = int(pos_size/limit_price)
    sl_1 = round((pos_size - loss_1) / quantity,2)
    sell_half = int(quantity/2)
    pos_val_lef = round((pos_size-loss_1)/2,2)
    sl_2 = round((pos_val_lef - loss_2) / sell_half,2)
    return quantity,sl_1,sl_2

quantity , stop_loss_1,stop_loss_2 = cal_partial_sl(limit_price, pos_size, loss_1, loss_2) 
    
    
    
    

order_id = app.nextValidOrderId
time.sleep(2)
app.placeOrder(order_id,usStk(ticker),limitOrder("BUY",quantity,limit_price)) # Buy limit --> input
time.sleep(5)

#max loss on this is 500$ so we have to create a algorithm(look at cal_partial_sl func
# we had two block of -250 when creating bioth stoplosses of pos_size).

    
while True:
    if inExec(app,ticker) == -1:
        
        time.sleep(5)
        bought_price = app.execution_df['Price'][0]
        app.reqIds(-1)
        time.sleep(2)
        order_id = app.nextValidOrderId
        time.sleep(2)
        app.placeOrder(order_id,usStk(ticker),stopMkt('SELL',int(quantity/2),stop_loss_1)) # Stop price half of the pos.
        break
time.sleep(2)
app.execution_df = pd.DataFrame(columns=['ReqId', 'PermId', 'Symbol',
                                  'SecType', 'Currency', 'ExecId',
                                  'Time', 'Account', 'Exchange',
                                  'Side', 'Shares', 'Price',
                                  'AvPrice', 'cumQty', 'OrderRef']) 
time.sleep(2)
inExec(app,ticker)

#we have refreshed it now.
while True:
    if inExec(app,ticker) == -1:
        time.sleep(3)
        time.sleep(1)
        app.reqPositions()
        time.sleep(1)
        rem_quant = int(app.pos_df[app.pos_df['Symbol'] == ticker]['Position'])
        app.reqIds(-1)
        time.sleep(2)
        order_id = app.nextValidOrderId
        time.sleep(2)
        app.placeOrder(order_id,usStk(ticker),stopMkt('SELL',rem_quant,stop_loss_2))# find out the remaining shares.
        
        break

        
print('The Script is done')
time.sleep(2)
        
        
        
    



