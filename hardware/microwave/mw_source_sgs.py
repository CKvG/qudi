# -*- coding: utf-8 -*-

"""
This file contains the Qudi hardware file to control R+S SGS devices.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import pyvisa
import time

from core.module import Base
from core.configoption import ConfigOption
from interface.microwave_interface import MicrowaveInterface
from interface.microwave_interface import MicrowaveLimits
from interface.microwave_interface import MicrowaveMode
from interface.microwave_interface import TriggerEdge

class MicrowaveRSSGS(Base, MicrowaveInterface):
    """ Hardware control class to controls RS SGS devices.

    Example config for copy-paste:

    mw_source_srssg:
        ip_address: 'TCPIP::169.254.2.20::inst0::INSTR'

        # Are they necessary:
        module.Class: 'microwave.mw_source_srssg.MicrowaveSRSSG'
        gpib_timeout: 10
    """

    ip_address = ConfigOption('ip_address', missing='error')
    model = ''
    is_running = False
    mode = ''

    def on_activate(self):
        """ Initialisation performed during activation of the module. """
        self.rm = pyvisa.ResourceManager()
        self.mode = 'none'
        try:
            self.dev = self.rm.open_resource(self.ip_address)
            self.model = 'SGS100A' if 'SGS100A' in str(self.dev.query('*IDN?')) else 'unknown'
            self.log.info('connected to device ' + str(self.dev.query('*IDN?')))
            # checks if output is activated
            if '1' in self.dev.query('outp:stat'):
                self.is_running = True
            elif '0' in self.dev.query('outp:stat'):
                self.is_running = False
        except:
            self.log.error('could not connect to device!\n' +
                  'check if it is turned on and the lan cable correctly plugged in\n' +
                  'is the IP address of the device >>{:s}<<?\n'.format(self.ip_address) +
                  'if not change it to this ip address in the SGMA GUI and try again')

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module."""
        self.dev.write(':OUTPut:STATe 0')

    def cw_on(self):
        """
        Switches on cw microwave output.
        Must return AFTER the device is actually running.

        @return int: error code (0:OK, -1:error)
        """
        try:
            self.dev.write(':OUTPut:STATe 1;:wai')
            self.log.info('Microwave output is activated')
            self.is_running = True
            self.mode = 'cw'
            return 0
        except:
            self.log.error('Error while activating Microwave output')
            return -1

    def get_status(self):
        """
        Gets the current status of the MW source, i.e. the mode (cw, list or
        sweep) and the output state (stopped, running)

        @return str, bool: mode ['cw', 'list', 'sweep'], is_running [True, False]
        """
        return ('last mode used: ' + str(self.mode),
                'output status: ' + str(self.is_running))

    def get_limits(self):
        """ Return the device-specific limits in a nested dictionary.

        @return MicrowaveLimits: object containing Microwave limits
        """
        if self.model == 'SGS100A':
             # different values in user manual, depends on if offset function is used
            return {'amp_lower': -20,
                    'amp_upper': 15,
                    'freq_lower': 1000,
                    'freq_upper': 6e6} # This depends on the options one bought.

    def off(self):
        """ Switches off any microwave output.
        Must return AFTER the device is actually stopped.

        @return int: error code (0:OK, -1:error)
        """
        try:
            self.dev.write(':OUTPut:STATe 0;:wai')
            self.log.info('Microwave output is deactivated')
            self.is_running = False
            return 0
        except:
            self.log.error('Error while deactivating Microwave output')
            return -1

    def get_power(self):
        """ Gets the microwave output power.

        @return float: the power set at the device in dBm
        """
        return float(self.dev.query(':SOURCe:POWer:POWer?'))

    def get_frequency(self):
        """ Gets the frequency of the microwave output.

        @return float: frequency (in Hz), which is currently set for this device
        """
        return float(self.dev.query(':SOURce:FREQuency:CW?'))

    def set_cw(self, frequency=None, power=None, useinterleave=None):
        """
        Configures the device for cw-mode and optionally sets frequency and/or power

        @param float frequency: frequency to set in Hz
        @param float power: power to set in dBm

        @return tuple(float, float, str): with the relation
            current frequency in Hz,
            current power in dBm,
            current mode
        """
        try:
            self.dev.write(':SOURce:FREQuency:CW ' + str(frequency) + ';:wai')
            self.dev.write(':pow:pow ' + str(power) + ';:wai')
            self.log.info('Microwave parameter set')
            return frequency, power, self.mode
        except:
            self.log.error('Error while setting Microwave parameter')
            return -1

    def list_on(self):
        """ Switches on the list mode.
        Must return AFTER the device is actually running.

        @return int: error code (0:OK, -1:error)
        """
        try:
            self.dev.write(':OUTPut:STATe 1;:wai')
            self.log.info('Microwave output is activated')
            self.is_running = True
            self.mode = 'list'
            return 0
        except:
            self.log.error('Error while activating Microwave output')
            return -1

    def set_list(self, frequency=None, power=None):
        """ Sets the MW mode to list mode

        @param list freq: list of frequencies in Hz
        @param float power: MW power of the frequency list in dBm

        @return int: error code (0:OK, -1:error)
        """
        if (len(frequency) != len(power)
            and
            len(frequency) != 1
            and
            len(power) != 1):
            raise Exception('list of frequencies and power levels must have the same length or length 1')
        else:
            try:
                self.list_pos = 0
                self.param_list = (frequency, power)
                self.dev.write(':SOURce:FREQuency:CW ' + str(self.param_list[0][self.list_pos]) + ';:wai')
                self.dev.write(':pow:pow ' + str(self.param_list[1][self.list_pos]) + ';:wai')
                self.log.info('Microwave list set')
                return 0
            except:
                self.log.error('Error while setting Microwave list')
                return 1
        # TODO: how to change to next list item (here by changing k) or add duration for each list item?

    def reset_listpos(self):
        """ Reset of MW List Mode position to start from first given frequency

        @return int: error code (0:OK, -1:error)
        """
        try:
            self.list_pos = 0
            return 0
        except:
            return -1

    def sweep_on(self):
        """ Switches on the sweep mode.

        @return int: error code (0:OK, -1:error)
        """
        try:
            self.dev.write(':OUTPut:STATe 1;:wai')
            self.log.info('Microwave sweep is activated')
            self.is_running = True
            self.mode = 'sweep'
            for i in [k for k in self.sweep_list if k >= self.sweep_freq]:
                self.sweep_freq = i
                self.dev.write(':SOURce:FREQuency:CW ' + str(self.sweep_freq) + ';:wai')
            return 0
        except:
            self.log.error('Error while activating Microwave sweep mode')
            return -1
        
    def set_sweep(self, start = 2.7e9, stop = 3e9, step = 1e6, power = -10):
        """ Sweep from 'start' frequency to 'stop' frequency with steps of width 'step' with 'power'.
        """
        try:
            self.sweep_list = []
            self.sweep_freq = start
            while self.sweep_freq <= stop:
                self.sweep_list.append(self.sweep_freq)
                self.sweep_freq = self.sweep_freq + step
            self.dev.write(':SOURce:FREQuency:CW ' + str(self.sweep_list[0]) + ';:wai')
            self.dev.write(':pow:pow ' + str(power) + ';:wai')
            self.log.info('Microwave sweep set')
            return 0
        except:
            self.log.error('Error while setting up sweep mode\n' + 
                  'have you given "start", "stop", "step" and "power" values?')
            return -1
        # TODO: how to adjust duration of each frequency? (e.g. for longer integration times)

    def reset_sweeppos(self):
        """ Reset of MW sweep position to start

        @return int: error code (0:OK, -1:error)
        """
        self.sweep_freq = self.sweep_list[0]

    def set_ext_trigger(self, pol, timing):
        """ Set the external trigger for this device with proper polarization.

        @param float timing: estimated time between triggers
        @param TriggerEdge pol: polarisation of the trigger (basically rising edge or
                        falling edge)

        @return object, float: current trigger polarity [TriggerEdge.RISING, TriggerEdge.FALLING],
            trigger timing
        """
        # TODO

    def trigger(self):
        """ Trigger the next element in the list or sweep mode programmatically.

        @return int: error code (0:OK, -1:error)

        Ensure that the Frequency was set AFTER the function returns, or give
        the function at least a save waiting time corresponding to the
        frequency switching speed.
        """
        # TODO

    # ================== Non interface commands: ==================

    def _custom(self, msg):
        """ Function to send other commands to the microwave source.

        If the command is a query (i.e. it includes a '?' ) the result will be printed
        """
        if '?' in msg:
            self.log.info(self.dev.query(msg))
        else:
            self.dev.write(msg)

    def _on(self):
        """ Switches on any preconfigured microwave output.

        @return int: error code (0:OK, -1:error)
        """
        self._custom('ENBR 1')

        dummy, is_running = self.get_status()
        while not is_running:
            time.sleep(0.1)
            dummy, is_running = self.get_status()

        return 0

    def set_power(self, power=0.):
        """ Sets the microwave output power.

        @param float power: the power (in dBm) set for this device

        @return int: error code (0:OK, -1:error)
        """
        self._custom('pow:pow {0:f}'.format(power))
        return 0

    def _set_frequency(self, freq=0.):
        """ Sets the frequency of the microwave output.

        @param float freq: the frequency (in Hz) set for this device

        @return int: error code (0:OK, -1:error)
        """

        self._custom('freq {0:e}'.format(freq))
        return 0

    def _reset_device(self):
        """ Resets the device and sets the default values."""
        self.mode = 'none'
        self._custom('*RST')
        self._custom('ENBR 0')   # turn off Type N output
        self._custom('ENBL 0')   # turn off BNC output
