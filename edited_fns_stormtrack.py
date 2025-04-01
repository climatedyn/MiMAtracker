import pandas as pd
import numpy as np
import xarray as xr


###############################################################################################
def StitchYears(fn,fnp1,return_data='stitched',verbose=0):
    '''Stitch tracking years together. Removes duplicates from two files which both include December data.
       
       INPUTS:
           fn         :   pd.Dataframe from year n
           fnp1       : pd.Dataframe from year n+1
           return_data: what exactly to return after removing all duplicate tracks:
                            'stitched': the concatenated pd.Dataframe containing fn and fnp1 minus duplicates
                            'first'   : fn minus duplicates
                            'last'    : fnp1 minus duplicates
           verbose    : level of verbosity
    '''
    # check whether there is actual overlap
    if fn['Date_Time'].iloc[-1] < fnp1['Date_Time'].iloc[0]:
        print('OBS: THERE IS NO TEMPORAL OVERLAP BETWEEN FILES: {0} vs. {1}'.format(fn['Date_Time'].iloc[-1],fnp1['Date_Time'].iloc[0]))
        return pd.concat([fn,fnp1])
    first_date = fnp1['Date_Time'].iloc[0]
    stitched = pd.concat([fn,fnp1])
    ninit = len(stitched)
    #
    ## first, remove all tracks in fnp1 which started on or before the first day in the file and are therefore covered by fn
    #
    # (vog) : .dt accessor is only available for Pandas Series. first_date is a single value (Timestamp object, not a series)
    #         which doesn't have .dt attribute. Do .month/.day instead.
    dec_first = (stitched['Date_Time'].dt.month == first_date.month) & (stitched['Date_Time'].dt.day == first_date.day)
    filtered = stitched[dec_first]
    # we want to filter out the tracks in fnp1 to be removed
    #  note: keep='first' means the first instance is False, the second is True
    #         because the label is according to whether it's a duplicate or not
    seconds = filtered.duplicated(subset=['Date_Time','Lon','Lat'],keep='first')
    tracks = np.unique(filtered[seconds]['Track_ID'])
    fnp1_out = fnp1.copy()
    for t in tracks:
        filtr = fnp1_out['Track_ID'] == t
        fnp1_out = fnp1_out.drop(fnp1_out[filtr].index)
    stitched = pd.concat([fn,fnp1_out])
    nfirst = len(stitched)
    if verbose > 0:
        print('removed {0} overlaps from Dec 1st.'.format(ninit-nfirst))
    #
    ## second, remove all subsequent duplicates from fn, as they are also covered by fnp1
    #
    # now we want to remove all the duplicates from fn
    #  keep='last' means the first instance is True, which is what we want to drop
    stitched = stitched.drop_duplicates(subset=['Date_Time','Lon','Lat'],keep='last')
    nsec = len(stitched)
    if verbose > 0:
        print('removed {0} overlaps during all of December.'.format(nfirst-nsec))
    if return_data == 'stitched':
        return stitched
    elif return_data == 'both':
        filtr_n  = (stitched['Date_Time'] >= fn  ['Date_Time'].iloc[0]) & (stitched['Date_Time'] <= fn  ['Date_Time'].iloc[-1])
        filtr_np1= (stitched['Date_Time'] >= fnp1['Date_Time'].iloc[0]) & (stitched['Date_Time'] <= fnp1['Date_Time'].iloc[-1])
        return stitched[filtr_n],stitched[filtr_np1]
    else:
        if return_data == 'first':
            fnsel = fn
        elif return_data == 'last':
            fnsel = fnp1
        filtr = (stitched['Date_Time'] >= fnsel['Date_Time'].iloc[0]) & (stitched['Date_Time'] <= fnsel['Date_Time'].iloc[-1])
        return stitched[filtr]

###############################################################################################
def AdjustTrackID(df,filename,dtype=None):
    year = filename.split('.'+dtype)[0].split('_')[-1]
    df['Track_ID'] = df['Track_ID']+int(year)*100000
    return df

def AdjustTrackYear(df,filename,dtype=None):
    # (vog)
    if dtype == 'txt':
        df['Date'] = df['Date'].astype(int)
        # check if dates are in year < 1000, meaning they need shifting
        if df['Date'].max() < 10000000:
            df['Date'] += int(2e7)  # add 20,000,000 if needed
    # (gov)
    # vog: what's the best approach below: add an 'else'?
    if df['Date'][0] < 1e6:
        year = filename.split('.dat')[0].split('_')[-1]
        century = int(year[:2])
        decade = int(year[3])
        if int(decade) == 0:
            prev_cent = century-1
            new_date = []
            for d in df['Date']:
                # the tracker produces 19 and 20 no matter what the actual century
                if d//1e4 == 19:
                    new_num = (d-19*1e4)+prev_cent*1e6+99*1e4
                else:
                    new_num = (d-20*1e4)+century*1e6
                new_date.append(int(new_num))
        else:
            new_date = [int(d+century*1e6) for d in df['Date']]
        df['Date'] = new_date
    datetime = df['Date'].astype(str)+'-'+df['Time'].astype(str)
    df['Date_Time'] = pd.to_datetime(datetime)
    del df['Date']
    del df['Time']
    return df

###############################################################################################
def AddInstance(df):
    def GenerateInstance(df):
        df['Instance'] = np.arange(len(df))+1
        return df
    return df.groupby('Track_ID').apply(GenerateInstance)

###############################################################################################
def ReadFiles(files,verbose=0):
    dtype = files[0].split('.')[-1]
    if dtype == 'dat': # cyclone tracker
        readArgs = {'sep':"\s+",'header':None,
                        'names':['Track_ID', 
                                 'Instance', 
                                 'Date', 
                                 'Time', 
                                 'Open_closed', 
                                 'Lon', 
                                 'Lat', 
                                 'CentralValue', 
                                 'Laplacian', 
                                 'Depth', 
                                 'Radius_deg', 
                                 'U', 
                                 'V'],
                        #'parse_dates':[['Date', 'Time']],
                       }
    elif dtype == 'csv': # rainfall tracker
        readArgs = {'sep':',','parse_dates':['Date_Time']}
        
    # vog: if tracks output files (e.g., run on MiMA simulations) have 1-digit years (e.g. your simulation
    # startet at year 0001), i.e., 'Date' could look something like '10101'. Then, use parse_dates and 
    # date_format args to make it '00010101'. Although this might not be even necessary for the operations
    # in AdjustTrackYear() to work. 
    elif dtype == 'txt':
        print('dtype=',dtype)
        readArgs = {'sep':"\s+",'header':None, 'names':['Track_ID', 'Instance', 'Date', 
                                                        'Time', 'Open_closed', 'Lon', 'Lat', 
                                                        'CentralValue', 'Laplacian', 'Depth', 
                                                        'Radius_deg', 'U', 'V'], 
                   'parse_dates':['Date'], 'date_format':"%Y/%m/%d"}
    
    nfiles = len(files)
    for n,f in enumerate(files):
        if verbose > 0:
            update_progress(n/nfiles,info='ReadFiles')
        if n == 0:
            fn = pd.read_table(f,**readArgs)
            if dtype == 'dat':
                fn = AdjustTrackID(fn,f)
                fn = AdjustTrackYear(fn,f)
            elif dtype == 'csv':
                fn = AddInstance(fn)
            # (vog)
            elif dtype == 'txt':
                fn = AdjustTrackID(fn,f,dtype)
                fn = AdjustTrackYear(fn,f,dtype)
            # (gov)
            continue
            
        fnp1 = pd.read_table(f,**readArgs)
        if dtype == 'dat':
            fnp1 = AdjustTrackID(fnp1,f)
            fnp1 = AdjustTrackYear(fnp1,f)
        elif dtype == 'csv':
            fnp1 = AddInstance(fnp1)
        # (vog)
        # note there is nothing different here so could be added above
        # together with dtype='.dat'
        elif dtype == 'txt':
            fnp1 = AdjustTrackID(fnp1,f,dtype)
            fnp1 = AdjustTrackYear(fnp1,f,dtype)
        # (gov)
        if fnp1.empty:
            print('OBS: FILE {0} IS EMPTY. IGNORING THIS FILE.'.format(f))
            continue
        # make sure we are stitching in chronological order
        if fn['Date_Time'].iloc[0] > fnp1['Date_Time'].iloc[0]:
            raise ValueError('OBS: FILES ARE NOT IN CHRONOLOGICAL ORDER: {0}, {1}'.format(fn['Date_Time'].iloc[0],fnp1['Date_Time'].iloc[0]))
        fn = StitchYears(fn,fnp1,return_data='stitched')
    if dtype == 'csv':
        fn = fn.reset_index(drop=True)
    if verbose > 0:
        update_progress(n+1/nfiles,info='ReadFiles')
    return fn