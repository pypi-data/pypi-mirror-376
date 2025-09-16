#!/usr/bin/env python
import sys, glob, os
import numpy as np
import matplotlib.pyplot as plt
from seiscod import Stream, Trace, FFTTrace
# from seiscod.read import readseiscodstream, readmseed
# from seiscod.readseg2withobspy import readseg2_using_obspy as readseg2
# from seiscod.picker import set_picker
from tempoo.timetick import timetick, microtimetick, millitimetick
import matplotlib.pyplot as plt
from collections import OrderedDict
import warnings


# ===== defaults
options = OrderedDict(
    {"-v": False,
     "-m": 1,
     "-g": 0.1,
     "-pg": 0.8,
     "-tk": 0,
     "prepro": [],
     "postpro": [],
     "select": []})

# =====
HELP = """viz
-h            help message
-v            verbose
# ====== display options
-m  i         mode 
              trace modes :    0=basic
              stream modes :   
                1  = show
                2  = shade 
                11 = show with obspy like decimation 
                12 = modes 1 and 2
                123  = same as 1 and 2 + pick mode
                3  = show, vertical axis corresponds to distance, not trace number
-tr           display the traces in relative time
-g   f        gain (for mode 0)
-pg  f        powergain (for mode 1)
-tk  i        tick mode
                0 = seconds/Hz
                1 = Dates
                2 = millisec (x1e3)
                3 = microsec (x1e6)
-grp          group the traces of all files into one stream
                if combined with selection, grouping can be done before or after selection
                example:
                    -grp -s I ::10  # group first then keep 1 trace over 10 in the result
                    -s I ::10 -grp  # opposite
-reg          regularize the sampling
-s   s        select traces, provide selection mode and value
              available modes are 
                select by index, from 0, value must be start:end:step, 
                     e.g.  viz -s ::100 means one over 100                     
# ====== preprocessing options (ordered)
-d            detrend
-tap f        taper width (s)
-ns           norm by std
-nm           norm by max
-na           norm by absolute max
-bp f f f     bandpass fmin(Hz), fmax(Hz), order(e.g. 4.)
-lp f f
-hp f f
-dc i         decimate by i (antialias at 95% of nyquist)
-der i        derivate n times
-gbp f f      Gaussian bandpass fcenter(Hz), alpha(e.g. 15.)
-trim         trim waveforms
-f            move to fourier domain
-cwp i f f b   correlate with the pilot, pretrig (>0, s), maxlag(>0, s), minphase(True/False)
"""


def get_slice(arg):
    """convert slice string into slice object
    e.g. ::-1 => slice(None, None, -1)
    """
    class GetSlice:
        def __getitem__(self, item):
            """GetSlice()[::-1] => slice(None, None, -1)"""
            return item


    try:
        return eval(f'GetSlice()[{arg}]')
    except Exception:
        raise ValueError(f'slicing command "{arg}" not understood')

    raise ValueError


def read_arguments():
    global options
    argv = sys.argv[1:]

    if len(argv) == 0 or "-h" in argv:
        print(HELP)
        exit(0)

    datafiles = []
    while len(argv):
        arg = argv.pop(0)
        if arg.startswith('--'):
            # some options
            raise NotImplementedError(arg)

        elif arg.startswith('-'):
            # ============= 1 x bool
            if arg in ["-v", "-grp", "-mrg"]:
                options[arg] = True

            # ============= 1 x int
            elif arg in ["-m"]:
                options[arg] = int(argv.pop(0))

            # ============= 1 x float
            elif arg in ["-g", "-pg"]:
                options[arg] = float(argv.pop(0))
                
            # ============= 1 x float
            elif arg in ["-tk"]:
                # 0: None(seconds/Hz), 1: dates, 2: millisec, 3: microsec
                options[arg] = int(argv.pop(0)) 

            # ============= select
            elif arg == "-s":
                select_before_grouping = "-grp" not in options.keys()
                select_slice = get_slice(argv.pop(0))
                options[arg] = (select_before_grouping, select_slice)

            # ============= prepro
            elif arg == "-reg":
                options['prepro'].append(('-reg', ))

            elif arg == "-tr":
                options['prepro'].append(('-tr', ))

            elif arg in ["-fl32", "-fl64"]:
                options['prepro'].append((arg, ))

            elif arg == "-trim":
                start, end = np.asarray([argv.pop(0), argv.pop(0)], float)
                options['prepro'].append(('-trim', start, end))

            elif arg == "-d":
                options['prepro'].append(('-d', ))

            elif arg == "-tap":
                width = float(argv.pop(0))
                options['prepro'].append(('-tap', width))

            elif arg in ("-ns", "-nm", "-na"):
                options['prepro'].append((arg, ))

            elif arg == "-bp":
                fmin = float(argv.pop(0))
                fmax = float(argv.pop(0))
                order = float(argv.pop(0))
                zerophase = {"True": True, "False": False}[argv.pop(0)]
                options['prepro'].append(('-bp', fmin, fmax, order, zerophase))

            elif arg == "-lp":
                fmax = float(argv.pop(0))
                order = float(argv.pop(0))
                zerophase = {"True": True, "False": False}[argv.pop(0)]                
                options['prepro'].append(('-lp', fmax, order, zerophase))

            elif arg == "-hp":
                fmin = float(argv.pop(0))
                order = float(argv.pop(0))
                zerophase = {"True": True, "False": False}[argv.pop(0)]                                
                options['prepro'].append(('-hp', fmin, order, zerophase))

            elif arg == "-dc":
                decim_rate = int(argv.pop(0))               
                options['prepro'].append(('-dc', decim_rate))

            elif arg == "-der":
                nder = int(argv.pop(0))
                options['prepro'].append(('-der', nder))

            elif arg == "-gbp":
                fcenter = float(argv.pop(0))
                alpha = float(argv.pop(0))
                options['prepro'].append(('-gbp', fcenter, alpha))
                
            elif arg == "-f":
                options['prepro'].append(('-f', ))

            elif arg == "-cwp":
                reference_trace = int(argv.pop(0))
                pretrig = float(argv.pop(0))
                maxlag = float(argv.pop(0))
                minphase = {"True": True, "False": False}[argv.pop(0)]
                options['prepro'].append(('-cwp', reference_trace, pretrig, maxlag, minphase))

            elif arg in ("-Nc", ):
                options['postpro'].append((arg, ))

            elif arg in ("-Ns", ):
                options['postpro'].append((arg, ))

            elif arg in ("-Nm", ):
                options['postpro'].append((arg, ))

            else:
                raise NotImplementedError(arg)

        # elif arg.endswith('.seiscodstream.npz'):
        elif os.path.isfile(arg):
            datafiles.append(arg)

    return datafiles, options


def prepro(st: Stream, options):
    for arg in options['prepro']:
        cmd = arg[0]
        if cmd == "-tr":
            for tr in st:
                tr.starttime = 0.

        elif cmd == "-reg":
            print(st.regularize())
            print("npts:%d, delta=%.2f, t0=%f" % st.check_stream_sampling_regularization())

        elif cmd == "-fl32":
            for tr in st:
                tr.float32()

        elif cmd == "-fl64":
            for tr in st:
                tr.float64()

        elif cmd == "-trim":
            start, end = arg[1], arg[2]
            for tr in st:
                tr.trim(start, end)

        elif cmd == "-d":
            for tr in st:
                tr.detrend()

        elif cmd == "-tap":
            width = arg[1]
            for tr in st:
                tr.taperwidth(width)

        elif cmd == "-ns":
            for tr in st:
                tr.norm('std')

        elif cmd == "-nm":
            for tr in st:
                tr.norm('max')

        elif cmd == "-na":
            for tr in st:
                tr.norm('amax')

        elif cmd == "-bp":
            fmin, fmax, order, zerophase = arg[1:]
            for tr in st:
                tr.bandpass(
                    freqmin=fmin, freqmax=fmax,
                    order=order, 
                    zerophase=zerophase,
                    )

        elif cmd == "-lp":
            fmax, order, zerophase = arg[1:]
            for tr in st:
                tr.lowpass(
                    freqmax=fmax,
                    order=order, 
                    zerophase=zerophase,
                    )

        elif cmd == "-hp":
            fmin, order, zerophase = arg[1:]
            for tr in st:
                tr.highpass(
                    freqmin=fmin,
                    order=order, 
                    zerophase=zerophase,
                    )

        elif cmd == "-dc":
            decim_rate = arg[1]
            for tr in st:
                tr: Trace
                tr.decimate(
                    decim_rate=decim_rate, 
                    anti_alias=0.95, 
                    anti_alias_order=4., 
                    anti_alias_zerophase=True,
                    )
                    
        elif cmd == "-der":
            nder = arg[1]
            for tr in st:
                for _ in range(nder):
                    tr.derivate()

        elif cmd == "-gbp":
            fcenter, alpha = arg[1:]
            for tr in st:
                tr.gaussbandpass(freq0=fcenter, alpha=alpha)

        elif cmd == "-f":
            st = Stream([tr.fft() for tr in st])

        elif cmd == "-cwp":
            reference_trace = int(np.arange(len(st))[arg[1]])  # -1 works also
            pretrig = arg[2]
            maxlag = arg[3]
            minimum_phase = arg[4]            

            st.correlate_with_trace(
                reference_trace, 
                minimum_phase=minimum_phase, 
                pretrig=pretrig, maxlag=maxlag,
                verbose=True,
                )

    if options['-v']:
        for tr in st:
            print(tr)

    return st


def group(streams: list):
    # group all streams into one
    new_stream = Stream()
    for _ in streams:
        new_stream += _
    streams = [new_stream]
    return streams


def merge(streams: list):
    # assume that all streams have the same number of traces
    # and that they all correspond to the same channel
    # normalize all of them similarly
    assert [len(st) == len(streams[0]) for st in streams[1:]]

    stream = Stream()
    for traces in zip(*streams):
        t = np.hstack([tr.atime() for tr in traces])
        d = np.hstack([tr.data for tr in traces])

        newdt = np.min([trace.delta for trace in traces])
        newt = np.arange(min(t), max(t), newdt)
        newd = np.interp(newt, xp=t, fp=d)
        tr_merge = traces[0].copy()
        tr_merge.starttime = newt.min()
        tr_merge.delta = newdt
        tr_merge.data = newd
        stream.append(tr_merge)
    return [stream]

def tick(ax, options):

    tickmode = options['-tk']
    
    if tickmode == 0:
        pass
    elif tickmode == 1:
        timetick(ax, "x")
    elif tickmode == 2:
        millitimetick(ax, "x")        
    elif tickmode == 3:
        microtimetick(ax, "x")        
    else:
        pass
                
def main():
    PICKING_MODES = [123, 1234]

    datafiles, options = read_arguments()
    print(options)

    select_before_grouping, select_slice = False, None
    if "-s" in options.keys():
        select_before_grouping, select_slice = options["-s"]

    streams = []
    for datafile in datafiles:
        print(f'loading {datafile}')

        if datafile.endswith('.seiscodstream.npz') or datafile.endswith('.seispystream.npz'):

            if select_before_grouping:
                print(f'slicing {datafile}')

                st = Stream().from_npz(
                    datafile,
                    trace_indexs=select_slice,
                    additional_keys='*' if options['-m'] in PICKING_MODES else None)
            else:
                st = Stream().from_npz(
                    datafile,
                    additional_keys='*' if options['-m'] in PICKING_MODES else None)

        elif datafile.lower().endswith(('.sg2', '.seg2', '.dat')):
            st = Stream().from_seg2_using_obspy(datafile)
            # st = Stream().from_seg2_using_pyseg2(datafile)  # read only issue?
            if select_before_grouping:
                print(f'slicing {datafile}')
                st = st[select_slice]

        elif datafile.lower().endswith(('.sgd', '.segd')):
            st = Stream().from_segd(datafile)
            if select_before_grouping:
                print(f'slicing {datafile}')
                st = st[select_slice]

        elif datafile.lower().endswith(('.mseed', '.miniseed')):
            st = Stream().from_mseed(datafile)
            if select_before_grouping:
                print(f'slicing {datafile}')
                st = st[select_slice]

        elif datafile.lower().endswith(('.segy', '.sgy')):
            st = Stream().from_segy_using_obspy(datafile, segy_keys_to_load="*")
            st.set('starttime', st.get('delay_recording_time')*1e-3)  # mimic suxwigb
            if select_before_grouping:
                print(f'slicing {datafile}')
                st = st[select_slice]
                
        else:
            raise NotImplementedError
        streams.append(st)

    if "-grp" in options.keys():
        streams = group(streams)

    if "-s" in options.keys() and not select_before_grouping:
        # no selection done yet, the selection applies to the groupped stream
        print('select_slice', select_slice)
        streams = [streams[0][select_slice]]

    if "-mrg" in options.keys():
        raise NotImplementedError
        streams = merge(streams)

    # process only the selected traces
    for n, stream in enumerate(streams):
        streams[n] = prepro(stream, options)

    # normalize traces after grouping and processing
    for arg in options['postpro']:

        cmd = arg[0]
        if cmd == "-Nc":
            if len(streams) > 1:
                # assume that all streams have the same number of traces
                # and that they all correspond to the same channel
                # normalize all of them similarly
                assert [len(st) == len(streams[0]) for st in streams[1:]]
                for traces in zip(*streams):
                    std = np.std(np.concatenate([tr.data for tr in traces]))
                    for tr in traces:
                        tr.data /= std if std != 0. else 1.
            else:
                streams[0].norm('std')

        if cmd == "-Ns":
            # each stream is normalized by its own std
            for st in streams:
                st.norm('std')

        if cmd == "-Nm":
            # each stream is normalized by its own std
            for st in streams:
                st.norm('max')
                
    print('display mode :', options['-m'])
    tmin, tmax = np.inf, -np.inf

    if options['-m'] == 0:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for st in streams:
            for tr in st:
                tr: Trace
                tr.show(ax)
        tick(ax, options)
        plt.show()

    elif options['-m'] == 1:
        fig = plt.figure()
        ax = fig.add_subplot(111)

        if isinstance(streams[0][0], FFTTrace):
            std0 = np.max([np.std(np.abs(st.get('data')).flat[:]) for st in streams])
        else:
            std0 = np.max([st.std() for st in streams])

        for n, st in enumerate(streams):
            color = "k"

            if isinstance(st[0], FFTTrace):
                s = np.std(np.abs(st.get('data')).flat[:])
            else:
                s = st.std()

            st.show(ax, gain=options['-g'] * s / std0, 
                    seedticks=True,
                    timeticks=False,                    
                    color=color, gain_mode="relative",
                    )

            tmin = min([tmin, st.get('starttime').min()])
            tmax = max([tmax, st.get('endtime').max()])

        if not isinstance(st[0], FFTTrace):
            ax.set_xlim(tmin, tmax)  # pb in Fourier domain
        tick(ax, options)
        plt.show()

    elif options['-m'] == 11:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        std0 = np.max([st.std() for st in streams])
        for st in streams:
            st.show(ax, gain=options['-g'] * st.std() / std0, 
                seedticks=True, 
                timeticks=False,                
                obspy_decim=True)
            tmin = min([tmin, st.get('starttime').min()])
            tmax = max([tmax, st.get('endtime').max()])
        if not isinstance(st[0], FFTTrace):
            ax.set_xlim(tmin, tmax)  # pb in Fourier domain
        tick(ax, options)
        plt.show()

    elif options['-m'] == 2:
        for st in streams:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            st.shade(ax, powergain=options['-pg'], 
                seedticks=True,
                timeticks=False,                
                )
            tick(ax, options)                
            plt.show()

    elif options['-m'] == 12:

        for st in streams:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            st.shade(ax, powergain=options['-pg'], cmap=plt.get_cmap("seismic"))
            st.show(ax, gain=options['-g'], 
                seedticks=True,
                timeticks=False,
                )
            tick(ax, options)                
            plt.show()

    elif options['-m'] == 123:
        warnings.warn('picking mode : the saveas option may not include all the data/attributes')
        assert options['-m'] in PICKING_MODES
        std0 = np.max([st.std() for st in streams])
        for st in streams:
            fig = plt.figure()
            ax = fig.add_subplot(111)

            st.pick(ax, gain=options['-g'] * st.std() / std0, 
                seedticks=True,
                timeticks=True,                  
                save_stream_as="_picks.seiscodstream.npz")
            tick(ax, options)
            plt.show()

    elif options['-m'] == 1234:
        warnings.warn('picking mode : the saveas option may not include all the data/attributes')
        assert options['-m'] in PICKING_MODES
        std0 = np.max([st.std() for st in streams])
        for st in streams:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            corr = st.std() / std0
            st.shade(ax, powergain=options['-pg'] * corr, cmap=plt.get_cmap("gray"))
            st.pick(ax, gain=options['-g'] * corr, 
                seedticks=True,
                timeticks=False,                  
                save_stream_as="_picks.seiscodstream.npz")
            tick(ax, options)
            plt.show()

    elif options['-m'] == 3:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for st in streams:
            st.show(ax, gain=options['-g'], 
                seedticks=True,
                timeticks=False,                
                ydim="distance")
        tick(ax, options)
        plt.show()

    else:
        raise NotImplementedError


if __name__ == "__main__":
    main()
