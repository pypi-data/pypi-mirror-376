import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import pyplot as plt, patches
from scipy import stats
import sys 

#############  PLOT SET UP ##################

def spines(ax,ap,aw,lrot):
    plt.setp(ax.spines.values(), linewidth=aw)
    ax.tick_params(direction='in', pad = ap,length=6,width=1.5,
                   which='major',right=True,top=True, labelrotation=lrot)
    ax.tick_params(direction='in', pad = ap,length=3, width=1.5,
                   which='minor',right=True,top=True)

###############  NICE p_value LABEL #################

def p_nice(p_in,label):
    if p_in <= sys.float_info.min:
       p_in = sys.float_info.min
       qual = "<"
    else:
        p_in = p_in
        qual = "="
    
    p_string = "%1.3e" %(p_in); #print(p_string,p_in)
    p1 = p_string[:4]; 
    p2,p3, = p_string.split('e'); 
    if p_in < 0.01:
        if p3[1] == "0":
            p3 = "-"+p3[2:]
        p_text = r"$p(\%s) %s %s \times 10^{%s}$" %(label,qual,p1,p3);
    else:
        p_text = r"$p(\%s) = %1.3f$" %(label,p_in);
    
    return p_text


#############  SCATTERBIN  ##################
    
def plot(data,
         two_panel = False,
         width = 7,
         height = 5,
         height_ratios = [1,0.5],
         fs = 12,
         aw = 2, 
         ap = 7,
         point_sym = 'o',
         point_s = 20,
         point_ec = 'r',
         point_fc = 'r',
         point_top = False,
         alpha = 1, 
         lrot = 0, 
         min_space = 5,
         xlabel_off = False,
         ylabel_off = False,
         xlabel = "x",
         ylabel = "y",
         pvalue = False,
         leg_scale = 0.8,
         leg_loc = 'upper left',
         nbins = 5,
         equal_span = 'x', 
         inc_strays = False, 
         SE = False,
         blw = 2,
         bcol = 'k',
         capsize=5,
         hc = False,
         export = False,
         plot_form = 'png', 
         plot_name = 'scatterbin'         
):

    """
    Bins scatter plot data

     Requires
             import numpy as np
             import pandas as pd
             import matplotlib.pyplot as plt
             import matplotlib.ticker as ticker

    Basic usage
             import scatterbin
             scatterbin.scatterbin(data)
    where data is a 2D array of the x and y data

    Parameters
    ----------

    data : obj

        The data in the form of a 2D array

    two_panel : bool   (default : False)

        The default is to plot the binned data in the scatter plot. If set to
        True this will plot these in a panel below.

    width : float  (default : 7)

        The width of the plot. 

    height : float   (default : 5)

        The height of the plot. 

    height_ratios : [float, float]    (default : [1,0.5])

        When two_panel = True, the height ratios of the two panels.
       
    fs : float   (default : 12)

        The font size used in the plot.

    aw : float    (default : 2)

        Axis widths

    aw : float    (default : 7)

        Axis padding

    point_sym : MarkerStyle  (default : 'o')

        The scatter plot marker

    point_s : float   (default : 20)

        Point size in scatter plots

    point_ec : str    (default :'r')

        The edge colour of the points

    point_cc : str    (default :'r')

        The face colour of the points

    point_top : bool   (default : False) 

        If True plots the scatter plots over the binned data
        in the single panel plot.

    alpha : float  (default : 1)

        The transparency of the points

    lrot : float   (default : 0)

        Axis label rotation angle

     min_space : int  (default : 5)

        Number of minor ticks per major tick interval

     xlabel_off : bool  (default : True)

        If True this removes the x-axis labels

    ylabel_off : bool   (default : True)

        If True this removes the y-axis labels

    xlabel : str (default : 'x')

        The x-axis label

    ylabel : str (default : 'x')

        The y-axis label

    pvalue : bool (default : False)

        If True this will show the p-value of the distribution
        according to Kendall's tau

    leg_scale: float (default : 0.8)

         The scaling of the legend text in relation to fs

    leg_loc : str    (default: 'upper left')

         The location of the legend

    nbins : int  (default : 5)

         The number of bins for the binning

    equal_span : str (default : 'x')

         The type of binning
         equal_span = 'x'  : each bin spans the same x-range
         equal_span = 'n'  : quantile binning - each bin
                             contains an equal number of
                             points and the x-error bars
                             show the standard deviation
         equal_span = 'nx' : shows the mean of the quantile
                             binning, but the x-error bars show
                             the range of the binning

    inc_strays : bool (default : False)

         The quantile binning will have some stray points
         left over if the number of points is not divisible
         by the number of bins. Setting this to True includes
         these stray points in the last bin

    SE : bool  (default : False)

         If True the error bars show the standard error rather
         than the default standard deviation

    blw : float (default : 2)

         The line width of the error bars

    bcol : str (default : 'k')

         The colour of the error bars

    capsize : float (default : 5)

         The cap size of the error bars

    hc : bool  (default : False)

      hc = True saves a hard copy

    plot_form : str (default : 'png')

      The format of the hard copy

    plot_name : str (default : 'scatterbin')

      The name of the hard copy

    """
    
    df = pd.DataFrame(data)
    df.columns=['x','y']
    df = df.sort_values(by=['x'])
    
    x1 = min(df['x']); x2 = max(df['x'])
    #bins = nbins # int((x2-x1)/nbins);
    spacing = (x2-x1)/nbins
    start = int(x1)
    #print(x1,x2,nbins,spacing)

    inc = 1
    binned = []
    df_bin = pd.DataFrame() 
    if equal_span == 'x':
        for i in range (0,nbins):
            
            s = start + float(i)*spacing
            e = start + float(i+1)*spacing
                     
            tmp = df[(df['x'] >= s) & (df['x'] < e)].reset_index();
            if len(tmp) > 0:
                xmax = max(tmp['x']); xmin = min(tmp['x'])
            else:
                xmax = 0; xmin =0
                            
            x_mean = start + float(i+0.5)*spacing; dx = 0.5*spacing
            y_mean = np.mean(tmp['y']); dy = np.std(tmp['y'],ddof = 1)
            if SE == True:
                dy = dy/float(len(tmp))**0.5 # STANDARD ERROR
         
            binned.append(x_mean); binned.append(dx);binned.append(y_mean);
            binned.append(dy);binned.append(xmin);binned.append(xmax);

    else:
        dbs = int(len(df)/nbins); rem = len(df) - (nbins*dbs)
        print("--------------------------------------------------------")
        print("%d entries over %d bins - %d per bin with remainder %s"
              %(len(df), nbins, dbs, rem))
        print("--------------------------------------------------------")
        df = df.reset_index(); df.index += 1;
        spare = df[df.index > nbins*dbs]
                
        for i in range(0,nbins):
            start = i*(dbs)+1; end = (i+1)*(dbs)
            tmp = df.loc[start:end:1]; #print(tmp)
            
            if inc_strays == True: # INCLUDING THE STRAYS
                if rem > 0:
                    if i == nbins-1:
                        tmp = pd.concat([tmp,spare], ignore_index=True)
                    
            xmax = max(tmp['x']); xmin = min(tmp['x'])
            x_mean = np.mean(tmp['x']); dx = np.std(tmp['x'],ddof = 1)
            y_mean = np.mean(tmp['y']); dy = np.std(tmp['y'],ddof = 1)
            if SE == True:
                dx = dx/float(len(tmp))**0.5
                dy = dy/float(len(tmp))**0.5
                
            binned.append(x_mean); binned.append(dx);binned.append(y_mean);
            binned.append(dy); binned.append(xmin);binned.append(xmax)
            
    binned = np.reshape(binned,(-1,6))
    df_bin = pd.DataFrame(binned, columns=['x','dx','y','dy','xmin','xmax']);
    df_bin = df_bin.dropna(); #print(df_bin)
    left = df_bin['x'] -  df_bin['xmin']; right = df_bin['xmax'] - df_bin['x']

    if export == True:
        df_bin.to_csv('scatter_bin.csv')
      
    x = data[0]; y = data[1]

    ### PLOTS ###
    font = fs
    plt.rcParams.update({'font.size': font})
        
    if two_panel == True:
        fig, axs = plt.subplots(2,1,figsize=(width,height),gridspec_kw={'height_ratios': height_ratios})
        spines(axs[0],ap,aw,lrot)
        spines(axs[1],ap,aw,lrot)
        axs[0].axes.xaxis.set_ticklabels([])

        if pvalue == True:
            tau, p_value = stats.kendalltau(y, x)

            axs[0].scatter(x,y, marker=point_sym,fc=point_fc,ec = point_ec,s=point_s,
                       alpha = alpha,label = p_nice(p_value,'tau'))
            axs[0].legend(fontsize = leg_scale*fs,loc=leg_loc)

        else:
            axs[0].scatter(x,y, marker=point_sym, fc=point_fc, ec = point_ec, s=point_s,
                       alpha = alpha)
            
        if equal_span != "nx":
            xerr = df_bin['dx']

        else:
            xerr= (left,right) 

        axs[1].errorbar(df_bin['x'],df_bin['y'], xerr=xerr, yerr=df_bin['dy'],lw = blw,
                    fmt='.', c = bcol, capsize=capsize, zorder = 1)


        x_maj = axs[1].get_xticks(); x_min = (x_maj[1] -  x_maj[0])/min_space
        axs[0].xaxis.set_minor_locator(ticker.MultipleLocator(x_min))
        axs[1].xaxis.set_minor_locator(ticker.MultipleLocator(x_min))

        y_maj0 = axs[0].get_yticks(); y_min0 = (y_maj0[1] -  y_maj0[0])/min_space
        axs[0].yaxis.set_minor_locator(ticker.MultipleLocator(y_min0))

        y_maj1 = axs[1].get_yticks(); y_min1 = (y_maj1[1] -  y_maj1[0])/min_space
        axs[1].yaxis.set_minor_locator(ticker.MultipleLocator(y_min1))
        

        axs[1].set_xlabel(xlabel);  axs[0].set_ylabel(ylabel); 
                
    else:
        pad = 0
        plt.figure(figsize = (width,height))
        ax = plt.gca();
        spines(ax,ap,aw,lrot)
        
        if point_top == True:
            zorder = 2
        else:
            zorder = 0

        if pvalue == True:
            tau, p_value = stats.kendalltau(y, x)

            ax.scatter(x,y, marker=point_sym, fc=point_fc, ec = point_ec, s=point_s,
                       alpha = alpha, zorder = zorder,label = p_nice(p_value,'tau'))
            ax.legend(fontsize = leg_scale*fs,loc=leg_loc)

        else:
            ax.scatter(x,y, marker=point_sym, fc=point_fc, ec = point_ec, s=point_s,
                       alpha = alpha, zorder = zorder)

        if equal_span != "nx":
            xerr = df_bin['dx']

        else:
            xerr= (left,right) 

        ax.errorbar(df_bin['x'],df_bin['y'], xerr=xerr, yerr=df_bin['dy'],lw = blw,
                    fmt='.', c = bcol, capsize=capsize, zorder = 1)


        x_maj = ax.get_xticks(); x_min = (x_maj[1] -  x_maj[0])/min_space
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(x_min))

        y_maj = ax.get_yticks(); y_min = (y_maj[1] -  y_maj[0])/min_space
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(y_min))

        ax.set_xlabel(xlabel);  ax.set_ylabel(ylabel)
    plt.tight_layout()
        
    if hc == True:
         plot = "%s_test.%s" %(plot_name,plot_form)
         plt.savefig(plot, format = "%s" %(plot_form));
         print("Plot written to", plot)
    plt.show()
