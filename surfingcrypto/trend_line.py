import pandas as pd
import trendln
import pickle
import datetime
import numpy as np
import matplotlib.pyplot as plt
import os
import dateutil


class trend_line:

    def __init__(self,ts,trendln_start="01-01-2021"):

        self.name=ts.coin
        self.df=ts.df
        self.trendln_start=dateutil.parser.parse(trendln_start,dayfirst=True)

    def build(self,compute=True,method=None,data_type=None,accuracy=None,window=125,save_output=False,execution_day=None):
        self.data_type=data_type
        self.accuracy=accuracy
        self.window=window

        if compute is False and execution_day is None:
            raise ValueError("Must specify day of execution to load.")

        if compute is False and method is None:
            raise ValueError("Must specify method of execution to load.")
        
        if method == None or method== "NSQUREDLOGN":
            self.method_name="NSQUREDLOGN"
            self.method=trendln.METHOD_NSQUREDLOGN

        elif method == "PROBHOUGH":
            self.method_name=method
            self.method=trendln.METHOD_PROBHOUGH

        elif method == "NCUBED":
            self.method_name=method
            self.method=trendln.METHOD_NCUBED

        elif method == "HOUGHLINES":
            self.method_name=method
            self.method=trendln.METHOD_HOUGHLINES 

        elif method == "HOUGHPOINTS":
            self.method_name=method
            self.method=trendln.METHOD_HOUGHPOINTS 

        else:
            raise ValueError("Method not known")


        start_str=str(self.trendln_start.strftime("%d-%m-%Y"))[:10]
        self.proj="data/trend_lines/"+self.name+"_"+str(start_str)[:10]+"/"+self.method_name+"/"
        picklename=self.proj+str(self.name)+"-trends"+"_"

        if save_output and not os.path.exists(self.proj):
            os.makedirs(self.proj)


        if compute:

            self.execution_day=datetime.date.today().strftime("%d-%m-%Y")
            self.compute()           
            if save_output:
                with open(picklename+self.execution_day+".pkl","wb") as f:
                    pickle.dump([self.support,self.resistance],f)
        else:
            self.execution_day=execution_day
            with open(picklename+self.execution_day+".pkl","rb") as f:
                pkl=pickle.load(f)
                self.support=pkl[0]
                self.resistance=pkl[1]       
        return 
            

    def compute(self):



        if self.data_type is not None and self.data_type.lower() == "low-high":
            h=(self.df.Low[self.trendln_start:], self.df.High[self.trendln_start:])
            self.skip_indexes=len(self.df.Low[:self.trendln_start])-1
        else:
            h=self.df.Close[self.trendln_start:]
            self.skip_indexes=len(self.df.Close[:self.trendln_start])-1
        

            
        self.support, self.resistance = trendln.calc_support_resistance(
            h,
            accuracy=self.accuracy,
            window=self.window,
            method=self.method,
            )
            ##SUPPORT
            # minimaIdxs - sorted list of indexes to the local minima
            # pmin - [slope, intercept] of average best fit line through all local minima points
            # mintrend - sorted list containing (points, result) for local minima trend lines
                # points - list of indexes to points in trend line
                # result - (slope, intercept, SSR, slopeErr, interceptErr, areaAvg)
                    # slope - slope of best fit trend line
                    # intercept - y-intercept of best fit trend line
                    # SSR - sum of squares due to regression
                    # slopeErr - standard error of slope
                    # interceptErr - standard error of intercept
                    # areaAvg - Reimann sum area of difference between best fit trend line
                    #   and actual data points averaged per time unit
            # minwindows - list of windows each containing mintrend for that window
            #RESISTANCE
            # maximaIdxs - sorted list of indexes to the local maxima
            # pmax - [slope, intercept] of average best fit line through all local maxima points
            # maxtrend - sorted list containing (points, result) for local maxima trend lines
                #see for mintrend above
            # maxwindows - list of windows each containing maxtrend for that window

    def obtain_correct_indexes(self,list):
        return [x+self.skip_indexes for x in list]


    def extend(self,periods=None):
        if periods is None:
            periods=10
        
        for col in self.df_trends.columns.tolist():
            self.df_trends.loc[self.df_trends[col].duplicated(keep="first"),col]=np.nan

        ordinal_index=self.df_trends.index.map(datetime.datetime.toordinal).to_numpy()

        ext=[]
        for column in self.df_trends.columns:
            mask = ~np.isnan(ordinal_index) & ~np.isnan(self.df_trends[column])
            slope, intercept, r_value, p_value, std_err = linregress(ordinal_index[mask], self.df_trends[column][mask])

            #firstday=self.df_trends[column].last_valid_index()
            firstday=self.df_trends[column].last_valid_index()

            firstday=firstday.toordinal()

            future=np.arange(firstday+1,firstday+periods,1)
            future=np.array(future)

            line = [slope*xi + intercept for xi in future]
            future=[datetime.datetime.fromordinal(i) for i in future]

            ext.append(pd.Series(line,index=future,name=column))

        ext=pd.concat(ext,axis=1)

        self.df_trends=pd.concat([self.df_trends,ext]).sort_index()
        self.df_trends=self.df_trends.groupby(self.df_trends.index).agg(nanmean)
        self.df_trends=self.df_trends.interpolate(how="index",limit_area="inside")



    def plot_trend(self,ax,nbest=2,extend=True,show_min_maxs=False):
        
        if extend:
            raise ValueError("Extend not implemented")
            # self.extend(periods=days)

        for i in range(len(self.support[3])):
            if len(self.support[3][i])!=0 :
                if len(self.support[3][i])<nbest:
                    nbest_sup=len(self.support[3])
                else:
                    nbest_sup=nbest

                for ii in range(nbest_sup):
                    self.df.iloc[self.obtain_correct_indexes(self.support[3][i][ii][0])].plot(y="Close",ax=ax,color="lightskyblue",linestyle="--",linewidth=0.5,legend=False,alpha=1)
        
        for i in range(len(self.resistance[3])):
            if len(self.resistance[3][i])!=0 :
                if len(self.resistance[3][i])<nbest:
                    nbest_res=len(self.support[3])
                else:
                    nbest_res=nbest
                    
                for ii in range(nbest_res):
                    self.df.iloc[self.obtain_correct_indexes(self.resistance[3][i][ii][0])].plot(y="Close",ax=ax,color="magenta",linestyle="--",linewidth=0.5,legend=False,alpha=1)
      
        #show points that are used for trendline computation
        if show_min_maxs:
            #mins
            self.df.iloc[self.obtain_correct_indexes(self.support[0])].reset_index().plot(ax=ax,x="Date",y="Close",kind="scatter",s=2,color="lightskyblue",zorder=10)
            #maxs
            self.df.iloc[self.obtain_correct_indexes(self.resistance[0])].reset_index().plot(ax=ax,x="Date",y="Close",kind="scatter",s=2,color="magenta",zorder=10)


        #annotation
        self.lastday=self.df.index.tolist()[-1].strftime("%d-%m-%Y")
        s="Trend lines computed on: "+self.execution_day+"\n"+"Last price on: "+str(self.lastday)
        ax.text(s=s,x=0.05,y=0.985,ha="left",color="white",va="top",transform=ax.transAxes,fontsize=4)
        
        #iax.legend(loc="lower right",fontsize=5)

        return