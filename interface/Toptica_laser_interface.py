# -*- coding: utf-8 -*-
"""
Interface file for lasers where current and power can be set.

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

from enum import Enum
from core.interface import abstract_interface_method
from core.meta import InterfaceMetaclass


class ControlMode(Enum):
    MIXED = 0
    POWER = 1
    CURRENT = 2

class ShutterState(Enum):
    CLOSED = 0
    OPEN = 1
    UNKNOWN = 2
    NOSHUTTER = 3

class LaserState(Enum):
    OFF = 0
    ON = 1
    LOCKED = 2
    UNKNOWN = 3

class ChannelSelect(Enum):
    NONE = 0
    CHANNEL1 = 1
    CHANNEL2 = 2
    BOTH = 3

class AdvancedFeatureSelect(Enum):
    NOAF = 0
    SKILL1 = 1
    FINE = 3

class TopticaLaserInterface(metaclass=InterfaceMetaclass):
    """
    """

    @abstract_interface_method
    def get_power_range(self):
        """ Return laser power
        @return tuple(p1, p2): Laser power range in milliwatts
        """
        pass

    @abstract_interface_method
    def get_power(self):
        """ Return laser power
        @return float: Actual laser power in milliwatts
        """
        pass

    @abstract_interface_method
    def set_power_ch1(self, power):
        """ Set laer power ins watts
          @param float power: laser power setpoint in milliwatts

          @return float: laser power setpoint in milliwatts
        """
        pass

    @abstract_interface_method
    def set_power_ch2(self, power):
        """ Set laer power ins watts
          @param float power: laser power setpoint in milliwatts

          @return float: laser power setpoint in milliwatts
        """
        pass

    @abstract_interface_method
    def get_info_ch(self):
        """ Set laer power ins watts
          @param float power: laser power setpoint in milliwatts

          @return float: laser power setpoint in milliwatts
        """
        pass


    @abstract_interface_method
    def get_power_setpoint(self):
        """ Return laser power setpoint
        @return float: Laser power setpoint in milliwatts
        """
        pass

    @abstract_interface_method
    def get_current_unit(self):
        """ Return laser current unit
        @return str: unit
        """
        pass

    @abstract_interface_method
    def get_current(self):
        """ Return laser current
        @return float: actual laser current as ampere or percentage of maximum current
        """
        pass

    @abstract_interface_method
    def get_current_range(self):
        """ Return laser current range
        @return tuple(c1, c2): Laser current range in current units
        """
        pass

    @abstract_interface_method
    def get_current_setpoint(self):
        """ Return laser current
        @return float: Laser current setpoint in amperes
        """
        pass

    @abstract_interface_method
    def set_current(self, current):
        """ Set laser current
        @param float current: Laser current setpoint in amperes
        @return float: Laser current setpoint in amperes
        """
        pass

    @abstract_interface_method
    def allowed_control_modes(self):
        """ Get available control mode of laser
          @return list: list with enum control modes
        """
        pass

    @abstract_interface_method
    def get_control_mode(self):
        """ Get control mode of laser
          @return enum ControlMode: control mode
        """
        pass

    @abstract_interface_method
    def set_control_mode(self, control_mode):
        """ Set laser control mode.
          @param enum control_mode: desired control mode
          @return enum ControlMode: actual control mode
        """
        pass

    @abstract_interface_method
    def on(self):
        """ Turn on laser. Does not open shutter if one is present.
          @return enum LaserState: actual laser state
        """
        pass

    @abstract_interface_method
    def off(self):
        """ Turn off laser. Does not close shutter if one is present.
          @return enum LaserState: actual laser state
        """
        pass

    @abstract_interface_method
    def get_laser_state(self):
        """ Get laser state.
          @return enum LaserState: laser state
        """
        pass

    @abstract_interface_method
    def set_laser_state(self, state):
        """ Set laser state.
          @param enum state: desired laser state
          @return enum LaserState: actual laser state
        """
        pass

    @abstract_interface_method
    def get_shutter_state(self):
        """ Get shutter state. Has a state for no shutter present.
          @return enum ShutterState: actual shutter state
        """
        pass

    @abstract_interface_method
    def set_shutter_state(self, state):
        """ Set shutter state.
          @param enum state: desired shutter state
          @return enum ShutterState: actual shutter state
        """
        pass

    @abstract_interface_method
    def get_temperatures(self):
        """ Get all available temperatures from laser.
          @return dict: dict of name, value for temperatures
        """
        pass

    @abstract_interface_method
    def get_temperature_setpoints(self):
        """ Get all available temperature setpoints from laser.
          @return dict: dict of name, value for temperature setpoints
        """
        pass

    @abstract_interface_method
    def set_temperatures(self, temps):
        """ Set laser temperatures.
          @param temps: dict of name, value to be set
          @return dict: dict of name, value of temperatures that were set
        """
        pass

    @abstract_interface_method
    def set_autopulse(self, state):
        """ Set laser temperatures.
          @param state: bool to set the autopulse feature ON or OFF
          @return state: string of what the state the autopulse feature is in
        """
        pass

    @abstract_interface_method
    def get_autopulseStatus(self):
        """ Set laser temperatures.
          @return state: string of what the state the autopulse feature is in
        """
        pass

    @abstract_interface_method
    def set_autopulse_freq(self, freq):
        """Set the frequency parameter of the autopulse feature.
          @param frequ: bool to set the autopulse feature ON or OFF
          @return state: string of what the state the autopulse feature is in
        """
        pass

    @abstract_interface_method
    def set_autopulse_duty(self, duty):
        """Set the duty cycle parameter of the autopulse feature.
          @param state: bool to set the autopulse feature ON or OFF
          @return state: string of what the state the autopulse feature is in
        """
        pass

    @abstract_interface_method
    def set_autopulse_per(self, per):
        """Set the periode parameter of the autopulse feature.
          @param state: bool to set the autopulse feature ON or OFF
          @return state: string of what the state the autopulse feature is in
        """
        pass

    @abstract_interface_method
    def set_autopulse_width(self, width):
        """ Set the width parameter of the autopulse feature.
          @param state: bool to set the autopulse feature ON or OFF
          @return state: string of what the state the autopulse feature is in
        """
        pass

    @abstract_interface_method
    def set_fine_ON(self):
        """ enable FINE
          @param state: bool to set the autopulse feature ON or OFF
          @return state: string of what the state the autopulse feature is in
        """
        pass

    @abstract_interface_method
    def set_fine_OFF(self):
        """ disable fine
          @param state: bool to set the autopulse feature ON or OFF
          @return state: string of what the state the autopulse feature is in
        """
        pass

    @abstract_interface_method
    def set_fine_A(self, paramA):
        """ setting FINE parameter a
        @param paramA : int. The a parameter of the FINE feature.
        """
        pass

    @abstract_interface_method
    def set_skill(self):
        """ setting FINE parameter a
        @param paramA : int. The a parameter of the FINE feature.
        """
        pass

    @abstract_interface_method
    def set_skill_off(self):
        """ setting FINE parameter a
        @param paramA : int. The a parameter of the FINE feature.
        """
        pass

    @abstract_interface_method
    def set_fine_B(self, paramB):
        """setting FINE parameter a
        @param  paramB : int. The b parameter of the FINE feature.
        """
        pass

    @abstract_interface_method
    def get_fineStatus(self):
        """get status of FINE feature
        @return  status : string. The status of the FINE feature.
        """
        pass


    @abstract_interface_method
    def get_extra_info(self):
        """ Show dianostic information about lasers.
          @return str: diagnostic info as a string
        """
        pass
