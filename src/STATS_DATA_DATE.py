"""STATS DATA DATE extension command"""

#Licensed Materials - Property of IBM
#IBM SPSS Products: Statistics General
#(c) Copyright IBM Corp. 2014
#US Government Users Restricted Rights - Use, duplication or disclosure 
#restricted by GSA ADP Schedule Contract with IBM Corp.


helptext = r"""STATS DATA DATE SPSSDATE=varname DATESTRUCTURE = list of periodicities
[WEEKPERIOD=periodicity] [BY=increment]
[/HELP].

Execute an SPSS DATE command taking the starting date from the data.

Example:
STATS DATA DATE SPSSDATE = datevar DATESTRUCTURE=YM.
constructs the starting date from variable datevar and assigns a period of 12.

SPSSDATE specifies an SPSS date variable.

DATESTRUCTURE specifies the date/time structure  as a string of letters drawn from Y Q M W H I S with no spaces
inbetween.  The abbreviations are the same as for the DATE command except that MI (minute) is I, but
CYCLE and OBS are not supported.

WEEKPERIOD applies only to W (week).  The other periods are assumed to have
their natural periodicity.  W defaults to 7 but might usefully be set to 5.  However,
the starting week is calculated from the first date value  based on a 7-day week
where week 1 begins on January 1.

BY specifies the increment between observations and defaults to 1.  With
DATESTRUCTURE=YM, for example, BY = 2 would mean that the data are monthly but
only observed every other month.

/HELP displays this text and does nothing else.
"""

__author__ =  'jkp, IBM'
__version__=  '1.0.1'
# history
#08-10-2012 original version

# for recent versions of Statistics
from extension import Template, Syntax, processcmd
import spss, spssdata, datetime

#map datestructure values to DATE command parameters and datetime components
datestructdict = dict([('y',('y', 'year')),('q',('q',None)),('m',('m', 'month')),('w',('w', None)),
    ('d',('d', 'day')),('h',('h','hour')),('i',('mi','minute')),('s',('s','second'))])
longperiod = set(['y','m','q'])
shortperiod = set(['w','d','h','i','s'])

def definedate(spssdate, datestructure, 
    weekperiod=None, by=1):
    
    # debugging
    # makes debug apply only to the current thread
    #try:
        #import wingdbstub
        #if wingdbstub.debugger != None:
            #import time
            #wingdbstub.debugger.StopDebug()
            #time.sleep(2)
            #wingdbstub.debugger.StartDebug()
        #import thread
        #wingdbstub.debugger.SetDebugThreads({thread.get_ident(): 1}, default_policy=0)
        ## for V19 use
        ##    ###SpssClient._heartBeat(False)
    #except:
        #pass
     
    datestruct = list(datestructure)
    datestructset = set(datestruct)
    if len(datestructset) != len(datestructure):
        raise ValueError(_("""The date structure parameter contains a duplicate entry: %s""") % datestructure)
    baditems = [v for v in datestruct if not v in datestructdict.keys()]
    if baditems:
        raise ValueError(_("""Invalid date structure parameter(s): %s""") % " ".join(baditems))
    if datestructset.intersection(longperiod) and datestructset.intersection(shortperiod):
        raise ValueError(_("""Long time periods cannot be mixed with short time periods: %s""") % 
            " ".join([item[1] for item in [datestructdict[k] for k in datestruct]]))
    
    #data will be used to construct the starting date
    
    curs = spssdata.Spssdata(spssdate, names=False, cvtDates="ALL")
    case = curs.fetchone()
    curs.CClose()
    if case[0] is None:
        raise ValueError(_("""Error:The first date value is missing: %s""") % spssdate)
    
    cmd = ["DATE"]
    for term in datestruct:
        kwd, dtattr = datestructdict[term]
        if not dtattr is None:
            cmd.append(kwd + " " + str(getattr(case[0], dtattr)))
        elif kwd == 'q':
            cmd.append(kwd + " " + str(case[0].month // 4 + 1))
        elif kwd == 'w':
            #Gregorian day number starting with year 1 - day number of current year
            wk = (case[0].toordinal() - datetime.date(case[0].year, 1,1).toordinal() + 1) // 7 + 1
            cmd.append(kwd + " " + str(wk))
            if weekperiod:
                cmd.append(" " + str(weekperiod))
    cmd.append("by " + str(by))
    spss.Submit(" ".join(cmd))
    # DATE command should do this
    if 'y' in datestruct:
        spss.Submit('FORMAT YEAR_ (N4)')
        

def Run(args):
    """Execute the STATS DATA DATE extension command"""

    args = args[args.keys()[0]]

    oobj = Syntax([
        Template("SPSSDATE", subc="",  ktype="existingvarlist", var="spssdate"),
        Template("DATESTRUCTURE", subc="", ktype="str", var="datestructure"),
        Template("WEEKPERIOD", subc="",  ktype="int", var="weekperiod", islist=False),
        Template("BY", subc="", ktype="int", var="by"),
        Template("HELP", subc="", ktype="bool")])
        
    #enable localization
    global _
    try:
        _("---")
    except:
        def _(msg):
            return msg
    # A HELP subcommand overrides all else
    if args.has_key("HELP"):
        #print helptext
        helper()
    else:
        processcmd(oobj, args, definedate)

def helper():
    """open html help in default browser window
    
    The location is computed from the current module name"""
    
    import webbrowser, os.path
    
    path = os.path.splitext(__file__)[0]
    helpspec = "file://" + path + os.path.sep + \
         "markdown.html"
    
    # webbrowser.open seems not to work well
    browser = webbrowser.get()
    if not browser.open_new(helpspec):
        print("Help file not found:" + helpspec)
try:    #override
    from extension import helper
except:
    pass