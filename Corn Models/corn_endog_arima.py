import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.tsa.arima_model import ARIMA
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.graphics.api import qqplot
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

class ArimaModel(object):

    def __init__(self, df, arima_order, train_test=True, split_level=.67):
        self.df = df
        self.y = self.df['daily change'].values
        self.x = self.df.index
        self.order = arima_order
        self.train_test=train_test
        self.split_level = split_level
        self.train_df = None
        self.test_df = None
        self.model = None
        # self.model = ARIMA(self.df['daily change'], order=arima_order)
        self.fitted = None

    def fit_model(self):
        if self.train_test:
            self.train_test_split()
            self.model = ARIMA(self.train_df['daily change'], order=self.order)
        else:
            self.model = ARIMA(self.df['daily change'], order=self.order)

    def train_test_split(self):
        train_size = int(len(self.df) * self.split_level)
        test_size = len(self.df) - train_size
        self.train_df, self.test_df = self.df[(len(self.df)-train_size):len(self.df)], self.df[0:(len(self.df)-train_size)]

    # def acf_pacf_lineplot(self):
    #     lag_acf = acf(self.y, nlags=20)
    #     lag_pacf = pacf(self.y, nlags=20, method='ols')
    #
    #     fig = plt.figure(figsize=(14, 8))
    #     ax1 = fig.add_subplot(1,2,1)
    #     ax1.plot(lag_acf)
    #     plt.axhline(y=0,linestyle='--',color='gray')
    #     plt.axhline(y=-1.96/np.sqrt(len(self.y)),linestyle='--',color='gray')
    #     plt.axhline(y=1.96/np.sqrt(len(self.y)),linestyle='--',color='gray')
    #     plt.title('Autocorrelation Function')
    #
    #     ax2 = fig.add_subplot(1,2,2)
    #     ax2.plot(lag_pacf)
    #     plt.axhline(y=0,linestyle='--',color='gray')
    #     plt.axhline(y=-1.96/np.sqrt(len(self.y)),linestyle='--',color='gray')
    #     plt.axhline(y=1.96/np.sqrt(len(self.y)),linestyle='--',color='gray')
    #     plt.title('Partial Autocorrelation Function')
    #
    #     plt.show()

    def acf_pacf_barplot(self):
        fig = plt.figure(figsize=(14,8))
        ax1 = fig.add_subplot(2,1,1)
        fig = plot_acf(self.y, lags=28, ax=ax1)
        ax2 = fig.add_subplot(212)
        fig = plot_pacf(self.y, lags=28, ax=ax2)
        plt.show()

    def get_fitteds(self):
        results = self.model.fit(disp=-1)
        self.fitted = results
        results = self.convert_back_to_prices(results.fittedvalues)
        return results

    def get_insample_predictions(self, dynamic=True):
        if self.train_test:
            preds = self.fitted.predict(int(len(self.train_df)*.25), len(self.train_df), dynamic=True)
            preds = self.convert_back_to_prices(preds)
        else:
            preds = self.fitted.predict(int(len(self.df)*.25), len(self.df), dynamic=True)
            preds = self.convert_back_to_prices(preds)
        return preds

    def get_outsample_predictions(self):
        preds = self.fitted.forecast(steps=7000)
        conf = preds[2]
        conf_low = self.convert_back_to_prices(conf[:,0])
        conf_high = self.convert_back_to_prices(conf[:,1])
        preds = self.convert_back_to_prices(preds[0])
        return preds, conf_low, conf_high

    def plot_residuals(self):
        fig = plt.figure(figsize=(14,8))
        ax = fig.add_subplot(1,1,1)
        ax = self.fitted.resid.plot(ax=ax)
        plt.suptitle('Residuals of ARIMA Model Over Time')
        plt.xlabel('Date')
        plt.ylabel('Residual ($)')
        plt.show()
        print stats.normaltest(self.fitted.resid)

    def convert_back_to_prices(self, values):
        values_cumsum = values.cumsum()
        y = self.df['Inflation Adjusted Price'][0:len(values)].values
        return values_cumsum + y

    def plot_insample_preds(self, arima_values):
        fig = plt.figure(figsize=(14,8))
        ax = fig.add_subplot(1,1,1)
        if self.train_test:
            true_prices = self.train_df['Inflation Adjusted Price'].values
            dates = self.train_df.index
        else:
            true_prices = self.df['Inflation Adjusted Price'].values
            dates = self.df.index
        ax.plot(dates, true_prices, color='gray', label='Inflation Adjusted Price Movements')
        ax.plot(dates[:len(arima_values)], arima_values, color='k', label='ARIMA Predictions')
        plt.suptitle('ARIMA Model vs. Inflation Adjusted Price Movements')
        plt.legend()
        plt.show()

    def plot_outsample_preds(self, arima_preds):
        fig = plt.figure(figsize=(14,8))
        ax = fig.add_subplot(1,1,1)
        true_prices =  self.df['Inflation Adjusted Price'].values
        if self.train_test:
            dates = np.arange(self.train_df.index[0], self.train_df.index[0]+timedelta(days=7000), timedelta(days=1)).astype(datetime)
        else:
            dates = np.arange(self.df.index[0], self.df.index[0]+timedelta(days=7000), timedelta(days=1)).astype(datetime)
        ax.plot(self.df.index, true_prices, color='gray', label='Inflation Adjusted Price Movements')
        ax.plot(dates, arima_preds, color='k', label='ARIMA Predictions')
        plt.suptitle('ARIMA Model vs. Inflation Adjusted Price Movements')
        plt.legend()
        plt.show()


if __name__ == '__main__':
    df = pd.read_csv('../full_database.csv', index_col=0)
    df.index = df.index.map(lambda x: datetime.strptime(x, '%Y-%m-%d'))
    my_arima = ArimaModel(df, (1,0,1), train_test=False)
    my_arima.fit_model()
    train_df = my_arima.train_df

    my_arima.acf_pacf_barplot()
    results = my_arima.get_fitteds()
    my_arima.plot_residuals()
    in_preds = my_arima.get_insample_predictions()
    my_arima.plot_insample_preds(in_preds)
    out_preds, out_low, out_high = my_arima.get_outsample_predictions()
    my_arima.plot_outsample_preds(out_preds)
