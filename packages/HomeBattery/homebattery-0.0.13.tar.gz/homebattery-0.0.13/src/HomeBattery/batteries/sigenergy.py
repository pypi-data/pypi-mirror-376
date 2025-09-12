'''
Copyright (C) 2025  ElaadNL

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

-------------------------------------------------------------------------------

This module provides a class to interface with a Sigenergy inverter using Modbus
protocol. The SigenergyInverter class allows for communication with the inverter
to read and write various parameters, such as power setpoints, battery state
of charge, and grid voltage.

The class utilizes the ModbusBattery base class and defines specific registers
for the Sigenergy inverter. It includes methods to set power and current setpoints,
read all registers, and get specific values like active power and battery SOC.
'''

import warnings
from enum import Enum
from ..battery import ModbusBattery
from ..modbus import Register, AccessType, DataType


class SigenergyInverter(ModbusBattery):
    '''Sigenergy modbus inverter class

    This class is used to communicate with a Sigenergy inverter through
    the modbus protocol.

    Arguments:
        modbus_ip (str): the ip address of the Sigenergy inverter
        modbus_port (int): the port of the Sigenergy inverter
        timeout (int): the timeout of the modbus client in seconds
        capacity (int): the capacity of the battery in Wh
        max_charge_power (int): the maximum charge power of the battery in W
        max_discharge_power (int): the maximum discharge power of the battery
                                   in W
        soc (int): the state of charge of the battery in %
    '''

    def __init__(
            self,
            modbus_ip: str,
            modbus_port: int = 502,
            timeout: int = 3,
            capacity: int = None,
            max_charge_power: int = None,
            max_discharge_power: int = None,
            soc: int = None
    ):
        super().__init__(modbus_ip, modbus_port, timeout, capacity,
                         max_charge_power, max_discharge_power, soc)

        self._init_power_control()

    def _init_power_control(self):
        '''Initialize the inverter for power control mode'''
        try:
            self.write_register(
                self.PlantSettingsRegisters.RemoteEMSEnable.value, 1,
                self.PlantSettingsRegisters.slave_id.value
            )
            # Set remote EMS control mode to 0 (Power control mode)
            self.write_register(
                self.PlantSettingsRegisters.RemoteEMSControlMode.value, 0,
                self.PlantSettingsRegisters.slave_id.value
            )
        except Exception as e:
            warnings.warn(f"Failed to initialize power control: {e}")

    def set_power_setpoint(self, setpoint: int):
        '''Sets the power setpoint of the inverter

        Arguments:
            setpoint (int): the power setpoint to set in W
                           positive values for charging (import from grid)
                           negative values for discharging (export to grid)
        '''
        if (self._max_charge_power is None or
                self._max_discharge_power is None):
            warnings.warn("Max charge power or max discharge power not set, "
                          "setpoint may exceed limits")
        elif setpoint > self._max_charge_power:
            warnings.warn(f"Power setpoint {setpoint} exceeds the maximum "
                          f"charge power {self._max_charge_power}\n"
                          f"Reverting to maximum charge power")
            setpoint = self._max_charge_power
        elif setpoint < -self._max_discharge_power:
            warnings.warn(f"Power setpoint {setpoint} exceeds the maximum "
                          f"discharge power {-self._max_discharge_power}\n"
                          f"Reverting to maximum discharge power")
            setpoint = -self._max_discharge_power

        try:
            # Register expects kW
            setpoint_kw = setpoint / 1000.0

            self.write_register(
                self.PlantSettingsRegisters.ActivePowerFixedTarget.value,
                setpoint_kw,
                self.PlantSettingsRegisters.slave_id.value
            )
        except Exception as e:
            warnings.warn(f"Failed to set power setpoint: {e}")

    def set_current_setpoint(self, setpoint: int):
        '''Sets the current setpoint of the inverter

        Arguments:
            setpoint (int): the current setpoint to set in A
        '''
        try:
            phase_voltage = self.get_phase_voltage(1)
            power_setpoint = setpoint * phase_voltage
            self.set_power_setpoint(power_setpoint)
        except Exception as e:
            warnings.warn(f"Failed to set current setpoint: {e}")

    def get_active_power_total(self):
        '''Gets the active power of the inverter

        Returns:
            float: the active power of the inverter in W
        '''
        try:
            power_kw = self.read_holding_register(
                self.PlantInfoRegisters.ActivePower.value,
                self.PlantInfoRegisters.slave_id.value
            )
            return power_kw * 1000  # Convert kW to W
        except Exception as e:
            warnings.warn(f"Failed to read active power: {e}")
            return 0

    def get_active_current_total(self):
        '''Gets the active total current of the inverter

        Returns:
            float: the active current of the inverter in A
        '''
        # we calculate the current instead of reading the corresponding
        # registers because those values are absolute
        try:
            power = self.get_active_power_total()
            voltage_total = 0
            phase_count = 0

            for phase in [1, 2, 3]:
                try:
                    voltage = self.get_phase_voltage(phase)
                    if voltage > 0:
                        voltage_total += voltage
                        phase_count += 1
                except Exception as e:
                    warnings.warn(f"Failed to read phase {phase} voltage: {e}")
                    continue

            if phase_count > 0 and voltage_total > 0:
                avg_voltage = voltage_total / phase_count
                return power / avg_voltage
            else:
                return 0
        except Exception as e:
            warnings.warn(f"Failed to calculate active current: {e}")
            return 0

    def get_battery_soc(self):
        '''Gets the state of charge of the battery

        Returns:
            float: the state of charge of the battery in %
        '''
        try:
            soc = self.read_holding_register(
                self.PlantInfoRegisters.BatterySOC.value,
                self.PlantInfoRegisters.slave_id.value
            )
            return soc
        except Exception as e:
            warnings.warn(f"Failed to read battery SOC: {e}")
            return 0

    def get_phase_voltage(self, phase: int):
        '''Gets the grid voltage for a specific phase

        Arguments:
            phase (int): the phase to get the voltage from (1, 2, or 3)
                        Sigenergy uses A, B, C notation which maps to 1, 2, 3

        Returns:
            float: the grid voltage in V
        '''
        try:
            if phase == 1:  # Phase A
                voltage = self.read_holding_register(
                    self.HybridInverterInfoRegisters.PhaseAVoltage.value,
                    self.HybridInverterInfoRegisters.slave_id.value
                )
                return voltage
            elif phase == 2:  # Phase B
                voltage = self.read_holding_register(
                    self.HybridInverterInfoRegisters.PhaseBVoltage.value,
                    self.HybridInverterInfoRegisters.slave_id.value
                )
                return voltage
            elif phase == 3:  # Phase C
                voltage = self.read_holding_register(
                    self.HybridInverterInfoRegisters.PhaseCVoltage.value,
                    self.HybridInverterInfoRegisters.slave_id.value
                )
                return voltage
            else:
                raise ValueError("Invalid phase number. Must be 1, 2, or 3")
        except Exception as e:
            warnings.warn(f"Failed to read phase {phase} voltage: {e}")
            return 0

    def get_battery_temperature(self):
        '''Gets the battery temperature

        Returns:
            float: the battery temperature in °C (average cell temperature)
        '''
        try:
            temp = self.read_holding_register(
                self.HybridInverterInfoRegisters.ESSAverageCellTemperature.value,
                self.HybridInverterInfoRegisters.slave_id.value
            )
            return temp
        except Exception as e:
            warnings.warn(f"Failed to read battery temperature: {e}")
            return 0

    def get_phase_current(self, phase: int):
        '''Gets the current for a specific phase

        Arguments:
            phase (int): the phase to get the current from (1, 2, or 3)
                        Sigenergy uses A, B, C notation which maps to 1, 2, 3

        Returns:
            float: the absolute phase current in A
        '''
        try:
            if phase == 1:  # Phase A
                current = self.read_holding_register(
                    self.HybridInverterInfoRegisters.PhaseACurrent.value,
                    self.HybridInverterInfoRegisters.slave_id.value
                )
                return current
            elif phase == 2:  # Phase B
                current = self.read_holding_register(
                    self.HybridInverterInfoRegisters.PhaseBCurrent.value,
                    self.HybridInverterInfoRegisters.slave_id.value
                )
                return current
            elif phase == 3:  # Phase C
                current = self.read_holding_register(
                    self.HybridInverterInfoRegisters.PhaseCCurrent.value,
                    self.HybridInverterInfoRegisters.slave_id.value
                )
                return current
            else:
                raise ValueError("Invalid phase number. Must be 1, 2, or 3")
        except Exception as e:
            warnings.warn(f"Failed to read phase {phase} current: {e}")
            return 0

    class PlantInfoRegisters(Enum):
        slave_id = 247
        SystemTime = Register(
            30000, "SystemTime", DataType.UINT32, count=2,
            unit="s", access_type=AccessType.READ)
        SystemTimezone = Register(
            30002, "SystemTimezone", DataType.INT16,
            unit="min", access_type=AccessType.READ)
        EMSWorkMode = Register(
            30003, "EMSWorkMode", DataType.UINT16,
            access_type=AccessType.READ)
        GridSensorStatus = Register(
            30004, "GridSensorStatus", DataType.UINT16,
            access_type=AccessType.READ)
        GridSensorActivePower = Register(
            30005, "GridSensorActivePower", DataType.INT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        GridSensorReactivePower = Register(
            30007, "GridSensorReactivePower", DataType.INT32, count=2,
            unit="kvar", gain=1000, access_type=AccessType.READ)
        OnOffGridStatus = Register(
            30009, "OnOffGridStatus", DataType.UINT16,
            access_type=AccessType.READ)
        MaxActivePower = Register(
            30010, "MaxActivePower", DataType.UINT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        MaxApparentPower = Register(
            30012, "MaxApparentPower", DataType.UINT32, count=2,
            unit="kvar", gain=1000, access_type=AccessType.READ)

        # Battery State of Charge - Main register for battery monitoring
        BatterySOC = Register(
            30014, "BatterySOC", DataType.UINT16,
            unit="%", gain=10, access_type=AccessType.READ)

        # Phase power readings
        PhaseAActivePower = Register(
            30015, "PhaseAActivePower", DataType.INT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        PhaseBActivePower = Register(
            30017, "PhaseBActivePower", DataType.INT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        PhaseCActivePower = Register(
            30019, "PhaseCActivePower", DataType.INT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        PhaseAReactivePower = Register(
            30021, "PhaseAReactivePower", DataType.INT32, count=2,
            unit="kvar", gain=1000, access_type=AccessType.READ)
        PhaseBReactivePower = Register(
            30023, "PhaseBReactivePower", DataType.INT32, count=2,
            unit="kvar", gain=1000, access_type=AccessType.READ)
        PhaseCReactivePower = Register(
            30025, "PhaseCReactivePower", DataType.INT32, count=2,
            unit="kvar", gain=1000, access_type=AccessType.READ)

        # Alarm registers
        GeneralAlarm1 = Register(
            30027, "GeneralAlarm1", DataType.UINT16,
            access_type=AccessType.READ)
        GeneralAlarm2 = Register(
            30028, "GeneralAlarm2", DataType.UINT16,
            access_type=AccessType.READ)
        GeneralAlarm3 = Register(
            30029, "GeneralAlarm3", DataType.UINT16,
            access_type=AccessType.READ)
        GeneralAlarm4 = Register(
            30030, "GeneralAlarm4", DataType.UINT16,
            access_type=AccessType.READ)
        GeneralAlarm5 = Register(
            30072, "GeneralAlarm5", DataType.UINT16,
            access_type=AccessType.READ)

        # Total plant power
        ActivePower = Register(
            30031, "ActivePower", DataType.INT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        ReactivePower = Register(
            30033, "ReactivePower", DataType.INT32, count=2,
            unit="kvar", gain=1000, access_type=AccessType.READ)
        PhotovoltaicPower = Register(
            30035, "PhotovoltaicPower", DataType.INT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)

        # ESS (Battery) power - Critical for battery monitoring
        ESSPower = Register(
            30037, "ESSPower", DataType.INT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)

        # Available power limits
        AvailableMaxActivePower = Register(
            30039, "AvailableMaxActivePower", DataType.UINT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        AvailableMinActivePower = Register(
            30041, "AvailableMinActivePower", DataType.UINT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        ESSAvailableMaxChargingPower = Register(
            30047, "ESSAvailableMaxChargingPower", DataType.UINT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        ESSAvailableMaxDischargingPower = Register(
            30049, "ESSAvailableMaxDischargingPower", DataType.UINT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)

        # Plant running state
        RunningState = Register(
            30051, "RunningState", DataType.UINT16,
            access_type=AccessType.READ)

        # Grid sensor phase powers
        GridSensorPhaseAActivePower = Register(
            30052, "GridSensorPhaseAActivePower", DataType.INT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        GridSensorPhaseBActivePower = Register(
            30054, "GridSensorPhaseBActivePower", DataType.INT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        GridSensorPhaseCActivePower = Register(
            30056, "GridSensorPhaseCActivePower", DataType.INT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)

        # ESS capacity and limits
        ESSAvailableMaxChargingCapacity = Register(
            30064, "ESSAvailableMaxChargingCapacity", DataType.UINT32, count=2,
            unit="kWh", gain=100, access_type=AccessType.READ)
        ESSAvailableMaxDischargingCapacity = Register(
            30066, "ESSAvailableMaxDischargingCapacity", DataType.UINT32, count=2,
            unit="kWh", gain=100, access_type=AccessType.READ)
        ESSRatedChargingPower = Register(
            30068, "ESSRatedChargingPower", DataType.UINT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        ESSRatedDischargingPower = Register(
            30070, "ESSRatedDischargingPower", DataType.UINT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ)
        ESSRatedEnergyCapacity = Register(
            30083, "ESSRatedEnergyCapacity", DataType.UINT32, count=2,
            unit="kWh", gain=100, access_type=AccessType.READ)
        ESSChargeCutOffSOC = Register(
            30085, "ESSChargeCutOffSOC", DataType.UINT16,
            unit="%", gain=10, access_type=AccessType.READ)
        ESSdischargeCutOffSOC = Register(
            30086, "ESSdischargeCutOffSOC", DataType.UINT16,
            unit="%", gain=10, access_type=AccessType.READ)
        ESSStateOfHealth = Register(
            30087, "ESSStateOfHealth", DataType.UINT16,
            unit="%", gain=10, access_type=AccessType.READ)

    class HybridInverterInfoRegisters(Enum):
        slave_id = 1
        PhaseAVoltage = Register(
            31011, "PhaseAVoltage", DataType.UINT32, count=2,
            unit="V", gain=100, access_type=AccessType.READ)
        PhaseBVoltage = Register(
            31013, "PhaseBVoltage", DataType.UINT32, count=2,
            unit="V", gain=100, access_type=AccessType.READ)
        PhaseCVoltage = Register(
            31015, "PhaseCVoltage", DataType.UINT32, count=2,
            unit="V", gain=100, access_type=AccessType.READ)
        PhaseACurrent = Register(
            31017, "PhaseACurrent", DataType.UINT32, count=2,
            unit="A", gain=100, access_type=AccessType.READ)
        PhaseBCurrent = Register(
            31019, "PhaseBCurrent", DataType.UINT32, count=2,
            unit="A", gain=100, access_type=AccessType.READ)
        PhaseCCurrent = Register(
            31021, "PhaseCCurrent", DataType.UINT32, count=2,
            unit="A", gain=100, access_type=AccessType.READ)

        # ESS (Battery) specific registers (30600 series)
        ESSBatterySOC = Register(
            30601, "ESSBatterySOC", DataType.UINT16,
            unit="%", gain=10, access_type=AccessType.READ)
        ESSBatterySOH = Register(
            30602, "ESSBatterySOH", DataType.UINT16,
            unit="%", gain=10, access_type=AccessType.READ)
        ESSAverageCellTemperature = Register(
            30603, "ESSAverageCellTemperature", DataType.INT16,
            unit="°C", gain=10, access_type=AccessType.READ)
        ESSAverageCellVoltage = Register(
            30604, "ESSAverageCellVoltage", DataType.UINT16,
            unit="V", gain=1000, access_type=AccessType.READ)

        # Plant parameter registers (40000 series - Read/Write control)
    class PlantSettingsRegisters(Enum):
        slave_id = 247
        StartStop = Register(
            40000, "StartStop", DataType.UINT16,
            access_type=AccessType.WRITE)
        ActivePowerFixedTarget = Register(
            40001, "ActivePowerFixedTarget", DataType.INT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ_WRITE)
        ReactivePowerFixedTarget = Register(
            40003, "ReactivePowerFixedTarget", DataType.INT32, count=2,
            unit="kvar", gain=1000, access_type=AccessType.READ_WRITE)
        ActivePowerPercentageTarget = Register(
            40005, "ActivePowerPercentageTarget", DataType.INT16,
            unit="%", gain=100, access_type=AccessType.READ_WRITE)

        # Remote EMS control
        RemoteEMSEnable = Register(
            40029, "RemoteEMSEnable", DataType.UINT16,
            access_type=AccessType.READ_WRITE)
        # Remote EMS control mode values:
        # 0x00: PCS remote control
        # 0x01: Standby
        # 0x02: Maximum self-consumption
        # 0x03: Command charging (consume grid power first)
        # 0x04: Command charging (consume PV power first)
        # 0x05: Command discharging (output from PV first)
        # 0x06: Command discharging (output from ESS first)
        RemoteEMSControlMode = Register(
            40031, "RemoteEMSControlMode", DataType.UINT16,
            access_type=AccessType.READ_WRITE)

        # ESS control limits
        ESSMaxChargingLimit = Register(
            40032, "ESSMaxChargingLimit", DataType.UINT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ_WRITE)
        ESSMaxDischargingLimit = Register(
            40034, "ESSMaxDischargingLimit", DataType.UINT32, count=2,
            unit="kW", gain=1000, access_type=AccessType.READ_WRITE)

        # SOC control
        BackupSOC = Register(
            40046, "BackupSOC", DataType.UINT16,
            unit="%", gain=10, access_type=AccessType.READ_WRITE)
        ChargeCutOffSOC = Register(
            40047, "ChargeCutOffSOC", DataType.UINT16,
            unit="%", gain=10, access_type=AccessType.READ_WRITE)
        DischargeCutOffSOC = Register(
            40048, "DischargeCutOffSOC", DataType.UINT16,
            unit="%", gain=10, access_type=AccessType.READ_WRITE)
