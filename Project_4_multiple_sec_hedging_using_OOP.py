# -*- coding: utf-8 -*-
"""
Created on Sat Jul 17 17:55:50 2021

@author: omar_
"""

# import useful libraries.
import pandas as pd
import numpy as np 
import yfinance as yf
from sklearn.linear_model import LinearRegression
import time
import datetime as dt

class multiple_sec_hedging(object):
    
    def __init__(self, tickers,long = int() ,short=int() ,start = dt.datetime.today() - dt.timedelta(days= 251*2 ),
                 end =  dt.datetime.today(), interval = '1d',theme_size = 20000, port_size=100000):
        
        
        # yahoo finance calc the 5 year beta with monthly data. i could work with 2Y with monthly data.
        self.tickers = tickers
        self.start = start
        self.end = end
        self.interval = interval
        self.long = long
        self.short = short
        self.port_size = port_size
        self.theme_size = float(theme_size)
        self.get_data()
        self.calc_beats()


    # in this 
    def get_data(self):
        # retrive data includoing the index
        self.data = yf.download(tickers = self.tickers, start = self.start, end = self.end, interval = self.interval)['Adj Close'];
        self.data = self.data.reindex(columns = self.tickers) # get this in the right order everytime.
        print('got the data')

    def calc_beats(self):
        col_names = []
        for i in range(1,len(self.tickers) + 1):
            col = f'return_{self.tickers[i-1]}'
            self.data[col] = self.data.iloc[:,i-1].pct_change()
            col_names.append(col) 
        self.data.dropna(inplace = True) 
        
        self.betas = {}
        for i in range(1,len(self.tickers)):
            model = LinearRegression(fit_intercept=True)#wrong beta must be arounf 1.2147
            model.fit(np.array(self.data[col_names[0]]).reshape(-1,1), np.array(self.data[col_names[i]])) #(x,y)
            self.betas[self.tickers[i]] = float(model.coef_)
        self.betas = pd.DataFrame(list(self.betas.items())) #betas in a dataframe now.



        #Create Now the portfolio with inital value with margin + theme size to get the complete picture.
        hedge_process = self.betas
        hedge_process.columns = ['Tickers', 'Betas']
        str_pos = "Long," * self.long + "Short," * self.short
        list_1 = list(str_pos.split(","))
        hedge_process['Long_Short'] = list_1[:-1] #adjustment to remove white columne
        hedge_process['Weighting'] = hedge_process['Betas'] / hedge_process['Betas'].sum()
        
        # get all the betas in one dataframe.
        beta_sums = pd.DataFrame(index = ['SUM_beta','L_beta','S_beta'],columns=['Betas'])
        beta_sums.loc['SUM_beta']= hedge_process['Betas'].sum()
        
        long_betas = hedge_process[hedge_process['Long_Short'] == 'Long']
        beta_sums.loc['L_beta'] = long_betas['Betas'].sum()
        
        short_betas = hedge_process[hedge_process['Long_Short'] == 'Short']
        beta_sums.loc['S_beta'] = short_betas['Betas'].sum()
        
        
        # now calc long short weights(hint, long shall = 100 and short shall =100%)
        
        #begin with long first
        weight_long_betas = long_betas['Betas']/ long_betas['Betas'].sum() 
        weight_short_betas = short_betas['Betas']/short_betas['Betas'].sum()
        
        perc1 = weight_long_betas * (1 - (beta_sums.loc['L_beta'][0]/beta_sums.loc['SUM_beta'][0]))
        perc2 = weight_short_betas * (1 - (beta_sums.loc['S_beta'][0]/beta_sums.loc['SUM_beta'][0]))
        
        position_perc_1 = (1-(perc1 / (1 - (beta_sums.loc['L_beta'][0]/beta_sums.loc['SUM_beta'][0])))) / (perc1.count()-1) * (1 - (beta_sums.loc['L_beta'][0]/beta_sums.loc['SUM_beta'][0]))
        position_perc_2 = (1-(perc2 / (1 - (beta_sums.loc['S_beta'][0]/beta_sums.loc['SUM_beta'][0])))) / (perc2.count()-1) * (1 - (beta_sums.loc['S_beta'][0]/beta_sums.loc['SUM_beta'][0]))
        
        #concattinate all 3 above and then add to summary.
        perc_vector= pd.concat([weight_long_betas,weight_short_betas])
        perc_2 = pd.concat([perc1,perc2])
        perc_3= pd.concat([position_perc_1,position_perc_2])
        hedge_process['L_S_Weighting'] = perc_vector
        hedge_process['percentage'] = perc_2
        hedge_process['Position_in_percentage'] = perc_3
        
        
        # now do position sizing
        hedge_process['dollar_pos_size'] = hedge_process['Position_in_percentage'] * self.theme_size
        
        df = self.data
        tick_names = self.tickers[1:]
        dict_prices = dict(df[tick_names].iloc[-1,:])
        hedge_process['stock_prices']=dict_prices.values()
        
        hedge_process['shares'] = (hedge_process['dollar_pos_size'] / hedge_process['stock_prices'])
        hedge_process['pos_in_percentage'] = hedge_process['dollar_pos_size'] / self.theme_size
        

                
       
        
        self.summary = hedge_process
        self.beta_sums = beta_sums
        summing = self.summary[['Weighting','L_S_Weighting','percentage','Position_in_percentage','dollar_pos_size']].sum()
 

        print('')
        print('')
        print(self.summary.to_markdown())
        print('')
        print('')
        print(self.beta_sums.to_markdown())
        print('')
        print('')
        print(summing.to_markdown())









# testing and study.                                                            
# x = multiple_sec_hedging(['^GSPC','JPM','GM','GS','AAPL','UFPI','SANM','CHGG'],long = 4,short=3,start = "2020-04-23",theme_size= 20000)
# y =  multiple_sec_hedging(['^GSPC','AAPL','UFPI','SANM','CHGG'],long = 3,short=1,start = "2020-04-23",theme_size= 20000)                      
# s =multiple_sec_hedging(['^GSPC','AAPL','FB','GE','KTB','TSLA'],long = 3,short =2,start = '2020-01-01',theme_size=34322)
