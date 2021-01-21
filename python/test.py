'''
Test script for retrieving data from DMM7510
2 methods:
A) running single calls for measurement in a loop in python
B) running a fixed number of measurements at a time and retrieving all the data with one single call

Both methods delay between measurements seems about the same.
Seems like digitize function for fixed interval is only possible for voltage/current measurements

Note:
    Unsure how much storage capacity buffer can contain.
    Might need to stream data and clear buffer occasionally if using (B) especially if running for a long time.
    For now, it seems like capacity is quite large: 11 million full timestamped readings
# todo: implement streaming
'''

import pyvisa
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

##### Configuration #####
rm = pyvisa.ResourceManager()
ret1 = rm.list_resources()
inst = rm.open_resource(ret1[0])
inst.timeout = 20000
inst._read_termination = '\n'
inst.write_termination = '\n'

# Reset the Model DMM7510 to the default settings
inst.write('reset()')
# Set the measure function to 4-wire resistance
inst.write('dmm.measure.func = dmm.FUNC_4W_RESISTANCE')
# Enable autozero (set to dmm.OFF to disable)
inst.write('dmm.measure.autozero.enable = dmm.ON')
# Enable offset compensation (set to dmm.OFF to disable)
inst.write('dmm.measure.offsetcompensation.enable = dmm.ON')
# Set the number of power line cycles to 1 # see ref pg. 13-179. lower = faster sample rate, but higher noise
inst.write('dmm.measure.nplc = 0.1')
# clear buffer just in case.
inst.write('defbuffer1.clear()') #default buffer is called defbuffer1

##### Measurements #####
#### Method (A) each iteration query for 1 count of data and put into dataframe ####
df = pd.DataFrame(columns=['reading', 'seconds', 'fractional'])
inst.write("dmm.measure.count = 1")
for i in range(100):
    # inst.write("dmm.measure.readwithtime()")
    # inst.write("dmm.measure.read(defbuffer1)")
    # reading, seconds, fractional = inst.query("print(dmm.measure.readwithtime())")
    reading, seconds, fractional = inst.query_ascii_values("print(dmm.measure.readwithtime())",separator='\t')

    # resist = inst.query("print(dmm.measure.read())")
    df = df.append({'reading': reading, 'seconds': seconds, 'fractional': fractional}, ignore_index=True)

# post processing - convert to datetime with milliseconds
df['datetime'] = pd.to_datetime(df.seconds+df.fractional, unit='s')
df['dates'] = df['datetime'].dt.date
df['time'] = df['datetime'].dt.time # for plotting

#### Method (B) Query for 100 count of data and put into dataframe ####
inst.write("dmm.measure.count = 10000")
inst.write('defbuffer1.clear()')
inst.write('dmm.measure.readwithtime()')

# see list of attributes available from buffer in reference doc 13-254
# get reading + time data from buffer
data = inst.query_ascii_values("printbuffer(1,defbuffer1.n,defbuffer1.readings, defbuffer1.seconds, defbuffer1.fractionalseconds)")
data = np.array(data).reshape((len(data) // 3, 3))  # reshape into (n,3) so that can put into dataframe
df2 = pd.DataFrame(data, columns=['reading', 'seconds', 'fractional'])  # convert to dataframe

# post processing - convert to datetime with milliseconds
df2['datetime'] = pd.to_datetime(df2.seconds+df2.fractional, unit='s')
df2['dates'] = df['datetime'].dt.date
df2['time'] = df['datetime'].dt.time # for plotting

### Plotting
fig = df.plot(x='time',y='reading')
df2.plot(x='time',y='reading',ax=fig)
