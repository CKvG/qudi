# -*- coding: utf-8 -*-
"""
This module controls Toptica lasers.

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

from core.module import Base
from core.configoption import ConfigOption
from interface.Toptica_laser_interface import TopticaLaserInterface
from interface.Toptica_laser_interface import ControlMode
from interface.Toptica_laser_interface import ShutterState
from interface.Toptica_laser_interface import LaserState
from interface.Toptica_laser_interface import ChannelSelect
from interface.Toptica_laser_interface import AdvancedFeatureSelect
from time import sleep
from enum import Enum

import serial

class Models(Enum):
    """ Model numbers for Toptica lasers
    """
    iBeamSmart = 0


class TopticaLaser(Base, TopticaLaserInterface):
    """ Qudi module to communicate with Toptica lasers.

    Example config for copy-paste:

    toptica_laser:
        module.Class: 'laser.toptica_laser.TopticaLaser'
        com_port: 'COM3'
        maxpower: .15
        model_name: 'iBeamSmart'
    """

    com_port = ConfigOption('com_port', missing='error')
    maxpower = ConfigOption('maxpower', .15, missing='warn')
    model_name = ConfigOption('model', 'iBeamSmart', missing='warn')

    def on_activate(self):
        """ Activate module.

            @return bool: activation success
        """
        self.model = Models[self.model_name]

        self.ser = serial.Serial()
        self.ser.baudrate = 115200
        self.ser.timeout = 0.03

        if not self.connect_laser(self.com_port):
            self.log.error('Laser does not seem to be connected.')
            return False
        return True

    def on_deactivate(self):
        """ Deactivate module.
        """

        self.disconnect_laser()

    def connect_laser(self, port):
        """ Connect to Instrument.

            @param str port: COM port

            @return bool: connection success
        """
        self.ser.port = port
        try:
            self.ser.open()
        except serial.SerialException:
            self.log.exception('Communication failure:')
            return False

        if not self.ser.is_open:
            self.log.error('Serial port failure.')
            return False
        if not (self._checkIfToptica()==True):
            self.log.error('Connected Device is not a Toptica iBEAM Laser.')
            return False
        return True

    def disconnect_laser(self):
        """ Close the connection to the instrument.
        """
        self.ser.close()
        if self.ser.is_open:
            self.log.error('Serial port failure. Laser still connected.')

    def allowed_control_modes(self):
        """ Control modes for this laser.
        """
        if self.model_name == Models.iBeamSmart:
            return [ControlMode.POWER]

    def get_control_mode(self):
        """ Get current laser control mode.

            @return ControlMode: current laser control-mode
        """
        if self.model_name == Models.iBeamSmart:
            return ControlMode.POWER

    def set_control_mode(self, mode):
        """ Set laser control mode.

            @param ControlMode mode: desired control-mode
            
            @return ControlMode: actual control-mode
        """
        if self.model_name == Models.iBeamSmart:
            return ControlMode.POWER

    def get_power(self):
        """ Get laser power.

            @return float: laser power in milliwatts
        """
        # 'pow' returns power in uW
        ret = self._communicate('sh pow')
        #sleep(.5)
        power = (float(self._getValue(ret)) / 1e3)
        return power

    def get_power_setpoint(self):
        """ Get the laser power setpoint.

        @return float: laser power setpoint in milliwatts
        """
        # TODO to check or implement

        self.ser.write(b'sh pow\r\n')
        #sleep(.5)
        power = float(self._getValue(self._get_terminal_string())) * 1e3
        return power
        # self.log.warning('Getting the power setpoint is not supported by the ' + self.model_name)
        # return -1

    def get_power_range(self):
        """ Get laser power range.

            @return tuple(float, float): laser power range in milliwatts
        """
        # TODO to check or implement
        power_range = (0.00, 150.00)
        #self.log.warning('Getting the power range is not supported by the ' + self.model_name)
        return power_range

    def set_power_ch1(self, power):
        """ Set laser power for channel 1

            @param float power: desired laser power in milliwatts
            
        """
        powerIn_mW_str = bytes(str(power), encoding='utf8')
        self.ser.write(b'ch 1 power ' + powerIn_mW_str + b'\r\n')
        #sleep(.5)

    def get_info_ch(self):
        """ Get channel infos (not used)
        """
        #self.ser.write(b'sh ch\r\n')
        #sleep(.5)
        return self._communicate('sh ch')

    def set_power_ch2(self, power):
        """ Set laser power for channel 2

            @param float power: desired laser power in milliwatts
        """
        powerIn_mW_str = bytes(str(power), encoding='utf8')
        self.ser.write(b'ch 2 power ' + powerIn_mW_str + b'\r\n')
        #sleep(.5)

    def get_current_unit(self):
        """ Get unit for laser current.

            @return str: unit for laser curret
        """
        # TODO to check or implement
        self.log.warning('Getting the current unit is not supported by the ' + self.model_name)
        return -1

    def get_current_range(self):
        """ Get range for laser current.

            @return tuple(float, float): range for laser current
        """
        # TODO to check or implement
        self.log.warning('Getting the current range is not supported by the ' + self.model_name)
        return -1

    def get_current(self):
        """ Get current laser current

            @return float: current laser-current in amps
        """
        self.ser.write(b'sh cur\r\n')
        sleep(.5)
        current = float(self._getValue(self._get_terminal_string()))
        return current

    def get_current_setpoint(self):
        """ Get laser current setpoint.

            @return float: laser current setpoint
        """
        # TODO to check or implement
        self.log.warning('Getting the current setpoint is not supported by the ' + self.model_name)
        return -1

    def set_current(self, current_percent):
        """ Set laser current setpoint.

            @param float current_percent: laser current setpoint
        """
        self.log.warning('Setting the current is not supported by the ' + self.model_name)
        return -1

    def get_shutter_state(self):
        """ Get laser shutter state.

            @return ShutterState: laser shutter state
        """
        self.log.warning('Getting the shutter state is not supported by the ' + self.model_name)

    def set_shutter_state(self, state):
        """ Set the desired laser shutter state.

            @param ShutterState state: desired laser shutter state

            @return ShutterState: actual laser shutter state
        """
        self.log.warning('Setting the shutter state is not supported by the ' + self.model_name)

    def get_temperatures(self):
        """ Get all available temperatures.

            @return dict: dict of temperature names and value
        """
        self.ser.write(b'sh temp sys\r\n')
        temp_sys = float(self._getValue(self._get_terminal_string()))
        self.ser.write(b'sh temp\r\n')
        temp_ld = float(self._getValue(self._get_terminal_string()))
        tempdict = {"Base Plate": temp_sys, 
                    "Diode": temp_ld}
        return tempdict

    def set_temperatures(self, temps):
        """ Set temperature for lasers with adjustable temperature for tuning

            @return dict: dict with new temperature setpoints
        """
        self.log.warning('Setting the temperatures is not supported by the ' + self.model_name)

    def get_temperature_setpoints(self):
        """ Get temperature setpints.

            @return dict: dict of temperature name and setpoint value
        """
        self.log.warning('Getting the temperatures setpoints is not supported by the ' + self.model_name)

    def get_laser_state(self):
        """ Get laser operation state

        @return LaserState: laser state
        """
        state = self._communicate('sta la')
        #print('Laser state: ' + state)
        if 'ON' in state:
            return LaserState.ON
        elif 'OFF' in state:
            return LaserState.OFF
        else:
            return LaserState.UNKNOWN

    def set_laser_state(self, status):
        """ Set desited laser state.

            @param LaserState status: desired laser state

            @return LaserState: actual laser state
        """
        if status == LaserState.ON:
            self.ser.write(b'la on')
        elif status == LaserState.OFF:
            self.ser.write(b'la off')
        else:
            self.log.warning('The desired Laser state is not available ' + self.model_name)
        return self.get_laser_state()

    def on(self):
        """ Turn laser on.

            @return LaserState: actual laser state
        """
        ret = self._communicate('la on')
        return ret

    def off(self):
        """ Turn laser off.

            @return LaserState: actual laser state
        """
        ret = self._communicate('la off')
        return ret

    def set_autopulse(self, state):
        '''Turn autopulse on/off.

        Parameters
        ----------
        None.

        Returns
        -------
        None.

        '''
        #print(state)
        if state:
            ret = self._communicate('puls on')
        else:
            ret = self._communicate('puls off')
        return ret

    def get_autopulseStatus(self):
        '''Get status of autopulse feature.

        Parameters
        ----------
        None.

        Returns
        -------
        @return status: Status of the autopulse feature.

        '''
        status = self._communicate('sta puls')
        return status

    def set_autopulse_freq(self, freq):
        '''Set the frequency parameter of the autopulse feature.

        Parameters
        ----------
        freq : int.
            Frequency of Autopulse in Hz. (Inputs such as "1e6" for 1MHz are allowed)

        Returns
        -------
        None.

        '''
        freq = freq*1e3
        #print(freq)
        ret = self._communicate('puls freq ' + str(freq))
        return ret

    def set_autopulse_duty(self, duty):
        '''Set the duty cycle parameter of the autopulse feature.

        Parameters
        ----------
        duty : int.
            Duty cycle of Autopulse in %.

        Returns
        -------
        None.

        '''
        #print(duty)
        ret = self._communicate('puls duty ' + str(duty))
        return ret

    def set_autopulse_per(self, per):
        '''Set the periode parameter of the autopulse feature.

        Parameters
        ----------
        per : int.
            Periode of Autopulse in microseconds.

        Returns
        -------
        None.

        '''
        per = per/1e6
        #print(per)
        ret = self._communicate('puls period ' + str(per))
        return ret

    def set_autopulse_width(self, width):
        '''Set the width parameter of the autopulse feature.

        Parameters
        ----------
        width : int.
            Width of Autopulse in microseconds.

        Returns
        -------
        None.

        '''
        width = width /1e6
        #print(width)
        ret = self._communicate('puls width ' + str(width))
        return ret

    def getAutopulseStatus(self):
        ret = self._communicate('sta puls')
        return ret

    def set_fine_ON(self):
        ''' enable FINE feature

        Parameters
        ----------
        None.

        Returns
        -------
        None.

        '''
        ret = self._communicate('fine on')
        return ret

    def set_fine_OFF(self):
        ''' disable FINE feature

        Parameters
        ----------
        None

        Returns
        -------
        None.

        '''
        ret = self._communicate('fine off')
        return ret


    def set_fine_A(self, paramA):
        ''' setting FINE parameter a

        Parameters
        ----------
        paramA : int.
            The a parameter of the FINE feature.

        Returns
        -------
        None.

        '''
        ret = self._communicate('fine a ' + str(paramA))
        return ret

    def set_fine_B(self, paramB):
        ''' setting FINE parameter b

        Parameters
        ----------
        paramB : int.
            The b parameter of the FINE feature.

        Returns
        -------
        None.

        '''
        ret = self._communicate('fine b ' + str(paramB))
        return ret

    def set_skill(self):
        ''' set SKILL feature on

        Parameters
        ----------
        None.

        Returns
        -------
        None.

        '''
        ret = self._communicate('skill on')
        return ret

    def set_skill_off(self):
        ''' set SKILL feature off

        Parameters
        ----------
        None.

        Returns
        -------
        None.

        '''
        ret = self._communicate('skill off')
        return ret


    def get_fineStatus(self):
        """ Get the status of the FINE feature.
        """
        status = self._communicate('sta fine')
        return status

    def get_extra_info(self):
        """ Extra information from laser.

            @return str: multiple lines of text with information about laser
        """
        extra = ('Serial number: '      + self._communicate('serial')   + '\n'
                 'Firmware Version: '   + self._communicate('ver')      + '\n'
                 'System UP Time: '     + self._communicate('sh timer') + '\n')

        return extra

#%% Internal methods

    def _send(self, message):
        """ Send a message to the laser
        """

        pass

    def _communicate(self, message):
        """ Send a message to the laser
        """
        self.ser.write(bytes(message, encoding='utf8')+b'\r\n')
        ret = self._get_terminal_string()
        return ret

    def _get_laser_temp(self):
        """ Returns actual LD temperature

            @temp : str
        """
        self.ser.write(b'sh temp\r\n')
        temp = self._get_terminal_string()
        #print('Laser Temperature: \r\n' + temp)
        return temp

    def _get_terminal_string(self, chunk_size=200):
        """Read all characters on the serial port and return them."""
        if not self.ser.timeout:
            raise TypeError('Port needs to have a timeout set!')

        read_buffer = b''

        while True:
            # Read in chunks. Each chunk will wait as long as specified by
            # timeout. Increase chunk_size to fail quicker
            byte_chunk = self.ser.read(size=chunk_size)
            read_buffer += byte_chunk
            if not len(byte_chunk) == chunk_size:
                break
        read_buffer = str(read_buffer, 'utf-8')
        read_buffer = read_buffer[0:len(read_buffer)-5]
        return read_buffer

    def _getValue(self, terminalString):
        ''' If terminalString contains a value - returns value as integer or float
            If terminalString contains NO value - returns '404'

        Parameters
        ----------
        terminalString : TYPE
            DESCRIPTION.

        Returns
        -------
        val : TYPE
            DESCRIPTION.

        '''
        if "=" in terminalString:
            start_num = terminalString.find("=", 0, len(terminalString))
            end_num = terminalString.find(" ", start_num+2, len(terminalString))
            val = terminalString[start_num+2:end_num]
        else:
            val = 404
        return val

    def _checkIfToptica(self):
        '''Check if the connected device is a Toptica iBeam Laser.
        
        Parameters
        ----------
        None.

        Returns
        -------
        ret : BOOL

        '''
        ret = self._communicate('serial')
        if 'iBEAM' in ret:
            return True
        else:
            return False