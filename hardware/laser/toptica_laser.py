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
from interface.simple_laser_interface import SimpleLaserInterface
from interface.simple_laser_interface import ControlMode
from interface.simple_laser_interface import ShutterState
from interface.simple_laser_interface import LaserState
from enum import Enum

import serial

class Models(Enum):
    """ Model numbers for Toptica lasers
    """
    iBeamSmart = 0


class TopticaLaser(Base, SimpleLaserInterface):
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
        self.ser.timeout = 0.5

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
        if not self._checkIfToptica():
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
        assert self.model_name == Models.iBeamSmart
        return [ControlMode.POWER]

    def get_control_mode(self):
        """ Get current laser control mode.

            @return ControlMode: current laser control-mode
        """
        assert self.model_name == Models.iBeamSmart
        return ControlMode.POWER

    def set_control_mode(self, mode):
        """ Set laser control mode.

            @param ControlMode mode: desired control-mode

            @return ControlMode: actual control-mode
        """
        assert self.model_name == Models.iBeamSmart
        return ControlMode.POWER

    def get_power(self):
        """ Get laser power.

            @return float: laser power in watts
        """
        # 'pow' returns power in uW
        self.ser.write(b'sh pow\r\n')
        power = float(self._getValue(self._get_terminal_string())) * 1e6
        return power

    def get_power_setpoint(self):
        """ Get the laser power setpoint.

        @return float: laser power setpoint in watts
        """
        # TODO to check or implement
        self.log.warning('Getting the power setpoint is not supported by the ' + self.model_name)
        return -1

    def get_power_range(self):
        """ Get laser power range.

            @return tuple(float, float): laser power range
        """
        # TODO to check or implement
        self.log.warning('Getting the power range is not supported by the ' + self.model_name)
        return -1

    def set_power(self, power, channel=2):
        """ Set laser power

            @param float power: desired laser power in watts
            @param int channel: channel of the laser
        """
        if self.model_name == Models.iBeamSmart:
            channel_str = bytes(channel)
            powerIn_uW_str = bytes([power * 1e-6])
            self.ser.write(b'ch ' + channel_str + b' power ' +
                           powerIn_uW_str + b'\r\n')

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
        tempdict = {"Base Plate": temp_sys, \
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
        self.ser.write(b'sta la')
        state = self._get_terminal_string()
        if 'ON' in state:
            return LaserState.ON
        elif 'OFF' in state:
            return LaserState.OFF

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
        self.ser.write(b'la on\r\n')

        return self.get_laser_state()

    def off(self):
        """ Turn laser off.

            @return LaserState: actual laser state
        """
        self.ser.write(b'la off\r\n')

        return self.get_laser_state()

    def get_extra_info(self):
        """ Extra information from laser.

            @return str: multiple lines of text with information about laser
        """
        extra = ('Serial number:    ' + self._communicate('serial')   + '\n'
                 'Firmware Version: ' + self._communicate('ver')      + '\n'
                 'System UP Time:   ' + self._communicate('sh timer') + '\n')

        return 'extra'

#%% Internal methods

    def _communicate(self, message):
        """ Send a message to to laser
        """
        self.ser.write(bytes(message)+b'\r\n')
        ret = self._get_terminal_string()
        return ret

    def _get_laser_temp(self):
        """ Returns actual LD temperature

            @temp : str
        """
        self.ser.write(b'sh temp\r\n')
        temp = self._get_terminal_string()
        print('Laser Temperature: \r\n' + temp)
        return temp

    def _get_terminal_string(self, chunk_size=200):
        """Read all characters on the serial port and return them."""
        if not self.port.timeout:
            raise TypeError('Port needs to have a timeout set!')

        read_buffer = b''

        while True:
            # Read in chunks. Each chunk will wait as long as specified by
            # timeout. Increase chunk_size to fail quicker
            byte_chunk = self.port.read(size=chunk_size)
            read_buffer += byte_chunk
            if not len(byte_chunk) == chunk_size:
                break
        read_buffer = str(read_buffer, 'utf-8')
        read_buffer = read_buffer[0:len(read_buffer)-5]
        return read_buffer

    def _getValue(self, terminalString):
        """ If terminalString contains a value - returns value as integer or float
            If terminalString contains NO value - returns '999'
            @todo Agree on number

        @param str terminalString: String from serial communication

        @return int or float
        """
        if "=" in terminalString:
            start_num = terminalString.find("=")
            end_num = terminalString.find(" ", start_num + 2)
            val = terminalString[start_num + 2 : end_num]
        else:
            val = 404
        return val

    def _checkIfToptica(self):
        """Check if the connected device is a Toptica iBeam Laser.

        @return bool: Wether or not laser is of type iBeam
        """
        ret = self._communicate('serial')
        return bool('iBEAM' in ret)
