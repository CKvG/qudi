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

import visa
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
        module.Class: 'microwave.mw_source_srssg.MicrowaveSRSSG'
        ip_address: 'TCPIP::169.254.2.20::inst0::INSTR'
        gpib_timeout: 10

    """

    ip_address = ConfigOption('ip_address', missing='error')


    def on_activate(self):
        """ Initialisation performed during activation of the module. """
        self.rm = pyvisa.ResourceManager()
        try:
            self.dev = self.rm.open_resource(self.ip_address)
            print('connected to device ' + str(self.dev.query('*IDN?')))
        except:
            print('could not connect to device!\n' + 
                  'check if it is turned on and the lan cable correctly plugged in\n' +
                  'is the IP address of the device 169.254.2.20?\n' + 
                  'if not change it to this ip address in the SGMA GUI and try again')
                                             self._FIRMWARE_VERSION))

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module."""

        # TODO

    def cw_on(self):
        """
        Switches on cw microwave output.
        Must return AFTER the device is actually running.

        @return int: error code (0:OK, -1:error)
        """
        # TODO

    def get_status(self):
        """
        Gets the current status of the MW source, i.e. the mode (cw, list or
        sweep) and the output state (stopped, running)

        @return str, bool: mode ['cw', 'list', 'sweep'], is_running [True, False]
        """
        # TODO

    def get_limits(self):
        """ Return the device-specific limits in a nested dictionary.

        @return MicrowaveLimits: object containing Microwave limits
        """
        # TODO
        
    def off(self):
        """ Switches off any microwave output.
        Must return AFTER the device is actually stopped.

        @return int: error code (0:OK, -1:error)
        """
        # TODO

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
        # TODO

    def list_on(self):
        """ Switches on the list mode.

        @return int: error code (0:OK, -1:error)
        """
        # TODO
    def set_list(self, frequency=None, power=None):
        """ Sets the MW mode to list mode

        @param list freq: list of frequencies in Hz
        @param float power: MW power of the frequency list in dBm

        @return int: error code (0:OK, -1:error)
        """
        # TODO

    def reset_listpos(self):
        """ Reset of MW List Mode position to start from first given frequency

        @return int: error code (0:OK, -1:error)
        """
        # TODO

    def sweep_on(self):
        """ Switches on the sweep mode.

        @return int: error code (0:OK, -1:error)
        """
        # TODO

    def set_sweep(self, start, stop, step, power):
        """ Sweep from frequency start to frequency sto pin steps of width stop with power.
        """
        # TODO

    def reset_sweeppos(self):
        """ Reset of MW sweep position to start

        @return int: error code (0:OK, -1:error)
        """
        # TODO

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

    def _ask(self, question):
        """ Ask wrapper.

        @param str question: a question to the device

        @return: the received answer
        """
        return self._gpib_connection.query(question)

    def _write(self, command, wait=True):
        """ Write wrapper.

        @param str command: a command to the device
        @param bool wait: optional, is the wait statement should be skipped.

        @return: str: the statuscode of the write command.
        """
        statuscode = self._gpib_connection.write(command)
        if wait:
            self._gpib_connection.write('*WAI')
        return statuscode

    def on(self):
        """ Switches on any preconfigured microwave output.

        @return int: error code (0:OK, -1:error)
        """
        self._write('ENBR 1')

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
        self._write('AMPR {0:f}'.format(power))
        return 0

    def set_frequency(self, freq=0.):
        """ Sets the frequency of the microwave output.

        @param float freq: the frequency (in Hz) set for this device

        @return int: error code (0:OK, -1:error)
        """

        self._write('FREQ {0:e}'.format(freq))
        return 0

    def reset_device(self):
        """ Resets the device and sets the default values."""
        self._write('*RST')
        self._write('ENBR 0')   # turn off Type N output
        self._write('ENBL 0')   # turn off BNC output


