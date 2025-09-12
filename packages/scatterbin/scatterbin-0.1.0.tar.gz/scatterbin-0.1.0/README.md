 # scatterbin
Adjustable binning of scatter plot data

`pip install scatterbin`

`import scatterbin`
`scatterbin.plot(data)`  

where data is an array 2D array of the x and y data.  

See src/scatterbin/demos.ipynb for examples

![](https://raw.githubusercontent.com/steviecurran/scatterbin/refs/heads/main/hw_123_test.png)

![](https://raw.githubusercontent.com/steviecurran/scatterbin/refs/heads/main/hw_all_test.png)

    
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
