from ...core.instrument import Instrument, BaseEnum, mark_query, mark_command


class ReferenceSource(BaseEnum):
    INTERNAL = (0, "Internal")
    EXTERNAL = (1, "External")
    DUAL = (2, "Dual")
    CHOP = (3, "Chopped")


class ReferenceSlope(BaseEnum):
    SINE = (0, "Sine")
    TTL_RISING = (1, "TTL Rising")
    TTL_FALLING = (2, "TTL Falling")


class InputMode(BaseEnum):
    VOLTAGE = (0, "Voltage")
    CURRENT = (1, "Current")


class InputConfiguration(BaseEnum):
    A = (0, "A")
    A_B = (1, "A-B")


class InputGrounding(BaseEnum):
    FLOAT = (0, "Floating")
    GROUND = (1, "Grounded")


class InputCoupling(BaseEnum):
    AC = (0, "AC")
    DC = (1, "DC")


class InputVoltageRange(BaseEnum):
    V_1 = (0, "1 V")
    mV_300 = (1, "300 mV")
    mV_100 = (2, "100 mV")
    mV_30 = (3, "30 mV")
    mV_10 = (4, "10 mV")


class SyncFilter(BaseEnum):
    OFF = (0, "Off")
    ON = (1, "On")


class AdvancedFilter(BaseEnum):
    OFF = (0, "Off")
    ON = (1, "On")


class Sensitivity(BaseEnum):
    nV_1 = (27, "1 nV")
    nV_2 = (26, "2 nV")
    nV_5 = (25, "5 nV")
    nV_10 = (24, "10 nV")
    nV_20 = (23, "20 nV")
    nV_50 = (22, "50 nV")
    nV_100 = (21, "100 nV")
    nV_200 = (20, "200 nV")
    nV_500 = (19, "500 nV")
    uV_1 = (18, "1 µV")
    uV_2 = (17, "2 µV")
    uV_5 = (16, "5 µV")
    uV_10 = (15, "10 µV")
    uV_20 = (14, "20 µV")
    uV_50 = (13, "50 µV")
    uV_100 = (12, "100 µV")
    uV_200 = (11, "200 µV")
    uV_500 = (10, "500 µV")
    mV_1 = (9, "1 mV")
    mV_2 = (8, "2 mV")
    mV_5 = (7, "5 mV")
    mV_10 = (6, "10 mV")
    mV_20 = (5, "20 mV")
    mV_50 = (4, "50 mV")
    mV_100 = (3, "100 mV")
    mV_200 = (2, "200 mV")
    mV_500 = (1, "500 mV")
    V_1 = (0, "1 V")


class TimeConstant(BaseEnum):
    us_1 = (0, "1 µs")
    us_3 = (1, "3 µs")
    us_10 = (2, "10 µs")
    us_30 = (3, "30 µs")
    us_100 = (4, "100 µs")
    us_300 = (5, "300 µs")
    ms_1 = (6, "1 ms")
    ms_3 = (7, "3 ms")
    ms_10 = (8, "10 ms")
    ms_30 = (9, "30 ms")
    ms_100 = (10, "100 ms")
    ms_300 = (11, "300 ms")
    s_1 = (12, "1 s")
    s_3 = (13, "3 s")
    s_10 = (14, "10 s")
    s_30 = (15, "30 s")
    s_100 = (16, "100 s")
    s_300 = (17, "300 s")
    ks_1 = (18, "1 ks")
    ks_3 = (19, "3 ks")
    ks_10 = (20, "10 ks")
    ks_30 = (21, "30 ks")


class FilterSlope(BaseEnum):
    db6 = (0, "6 dB")
    db12 = (1, "12 dB")
    db18 = (2, "18 dB")
    db24 = (3, "24 dB")


class SR_860(Instrument):
    """
    Class for the Stanford Research SR-860 Lock-In Amplifier.
    """

    @mark_query
    def identify(self) -> str:
        """Queries the instrument identification string.

        Returns:
            str: The identification string of the instrument.
        """
        return self.query("*IDN?")

    @mark_command
    def reset(self) -> int:
        """Resets the instrument to its default state.

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command("*RST")

    @mark_command
    def clear(self) -> int:
        """Clears the status and error registers of the instrument.

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command("*CLS")

    @mark_query
    def get_phase(self) -> float:
        """Queries the current excitation phase in degrees.

        Returns:
            float: The current phase angle in degrees.
        """
        return float(self.query("PHAS?"))

    @mark_command
    def set_phase(self, phase: float) -> int:
        """Sets the excitation phase in degrees.

        Args:
            phase (float): The phase angle in degrees to set.

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"PHAS {phase:.2f}")

    @mark_query
    def get_reference_source(self) -> ReferenceSource:
        """Queries the current reference source.

        Returns:
            ReferenceSource: The current reference source (e.g., INTERNAL, EXTERNAL, DUAL, CHOP).
        """
        return ReferenceSource.from_raw_value(int(self.query("RSRC?")))

    @mark_command
    def set_reference_source(self, source: ReferenceSource) -> int:
        """Sets the reference source.

        Args:
            source (ReferenceSource): The reference source to set (e.g., INTERNAL, EXTERNAL, DUAL, CHOP).

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"RSRC {source.raw_value}")

    @mark_query
    def get_frequency(self) -> float:
        """Queries the current reference frequency.

        Returns:
            float: The current reference frequency in Hz.
        """
        return float(self.query("FREQ?"))

    @mark_command
    def set_frequency(self, frequency: float) -> int:
        """Sets the reference frequency.

        Args:
            frequency (float): The frequency in Hz to set.

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"FREQ {frequency:.3f}")

    @mark_query
    def get_internal_frequency(self) -> float:
        """Queries the internal reference frequency.

        Returns:
            float: The internal reference frequency in Hz.
        """
        return float(self.query("FREQINT?"))

    @mark_command
    def set_internal_frequency(self, frequency: float) -> int:
        """Sets the internal reference frequency.

        Args:
            frequency (float): The internal frequency in Hz to set.

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"FREQINT {frequency:.3f}")

    @mark_query
    def get_external_reference_slope(self) -> ReferenceSlope:
        """Queries the slope of the external reference signal.

        Returns:
            ReferenceSlope: The slope of the external reference signal (e.g., SINE, TTL_RISING, TTL_FALLING).
        """
        return ReferenceSlope.from_raw_value(int(self.query("RSLP?")))

    @mark_command
    def set_external_reference_slope(self, slope: ReferenceSlope) -> int:
        """Sets the slope of the external reference signal.

        Args:
            slope (ReferenceSlope): The slope to set (e.g., SINE, TTL_RISING, TTL_FALLING).

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"RSLP {slope.raw_value}")

    @mark_query
    def get_harmonic(self) -> int:
        """Queries the current harmonic setting.

        Returns:
            int: The current harmonic setting.
        """
        return int(self.query("HARM?"))

    @mark_command
    def set_harmonic(self, harmonic: int) -> int:
        """Sets the harmonic.

        Args:
            harmonic (int): The harmonic to set.

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"HARM {harmonic}")

    @mark_query
    def get_reference_amplitude(self) -> float:
        """Queries the reference amplitude.

        Returns:
            float: The reference amplitude in volts.
        """
        return float(self.query("SLVL?"))

    @mark_command
    def set_reference_amplitude(self, amplitude: float) -> int:
        """Sets the reference amplitude.

        Args:
            amplitude (float): The amplitude in volts to set.

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"SLVL {amplitude:.3f}")

    @mark_query
    def get_reference_offset(self) -> float:
        """Queries the reference offset.

        Returns:
            float: The reference offset in volts.
        """
        return float(self.query("SOFF?"))

    @mark_command
    def set_reference_offset(self, amplitude: float) -> int:
        """Sets the reference offset.

        Args:
            amplitude (float): The offset in volts to set.

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"SOFF {amplitude:.3f}")

    @mark_query
    def get_input_mode(self) -> InputMode:
        """Queries the input mode.

        Returns:
            InputMode: The current input mode (e.g., VOLTAGE, CURRENT).
        """
        return InputMode.from_raw_value(int(self.query("IVMD?")))

    @mark_command
    def set_input_mode(self, mode: InputMode) -> int:
        """Sets the input mode.

        Args:
            mode (InputMode): The input mode to set (e.g., VOLTAGE, CURRENT).

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"IVMD {mode.raw_value}")

    @mark_query
    def get_input_configuration(self) -> InputConfiguration:
        """Queries the input configuration.

        Returns:
            InputConfiguration: The current input configuration (e.g., A, A-B).
        """
        return InputConfiguration.from_raw_value(int(self.query("ISRC?")))

    @mark_command
    def set_input_configuration(self, configuration: InputConfiguration) -> int:
        """Sets the input configuration.

        Args:
            configuration (InputConfiguration): The input configuration to set (e.g., A, A-B).

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"ISRC {configuration.raw_value}")

    @mark_query
    def get_input_coupling(self) -> InputCoupling:
        """Queries the input coupling configuration.

        Returns:
            InputCoupling: The current input coupling configuration (e.g., AC, DC).
        """
        return InputCoupling.from_raw_value(int(self.query("ICPL?")))

    @mark_command
    def set_input_coupling(self, coupling: InputCoupling) -> int:
        """Sets the input coupling configuration.

        Args:
            coupling (InputCoupling): The input coupling configuration to set (e.g., AC, DC).

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"ICPL {coupling.raw_value}")

    @mark_query
    def get_input_grounding(self) -> InputGrounding:
        """Queries the input grounding configuration.

        Returns:
            InputGrounding: The current input grounding configuration (e.g., FLOAT, GROUND).
        """
        return InputGrounding.from_raw_value(int(self.query("IGND?")))

    @mark_command
    def set_input_grounding(self, grounding: InputGrounding) -> int:
        """Sets the input grounding configuration.

        Args:
            grounding (InputGrounding): The input grounding configuration to set (e.g., FLOAT, GROUND).

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"IGND {grounding.raw_value}")

    @mark_query
    def get_input_voltage_range(self) -> InputVoltageRange:
        """Queries the input voltage range.

        Returns:
            InputVoltageRange: The current input voltage range (e.g., 1 V, 300 mV).
        """
        return InputVoltageRange.from_raw_value(int(self.query("IRNG?")))

    @mark_command
    def set_input_voltage_range(self, input_range: InputVoltageRange) -> int:
        """Sets the input voltage range.

        Args:
            input_range (InputVoltageRange): The input voltage range to set (e.g., 1 V, 300 mV).

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"IRNG {input_range.raw_value}")

    @mark_query
    def get_sync_filter(self) -> SyncFilter:
        """Queries the synchronization filter state.

        Returns:
            SyncFilter: The current synchronization filter state (e.g., OFF, ON).
        """
        return SyncFilter.from_raw_value(int(self.query("SYNC?")))

    @mark_command
    def set_sync_filter(self, configuration: SyncFilter) -> int:
        """Sets the synchronization filter state.

        Args:
            configuration (SyncFilter): The synchronization filter state to set (e.g., OFF, ON).

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"SYNC {configuration.raw_value}")

    @mark_query
    def get_advanced_filter(self) -> AdvancedFilter:
        """Queries the advanced filter state.

        Returns:
            AdvancedFilter: The current advanced filter state (e.g., OFF, ON).
        """
        return AdvancedFilter.from_raw_value(int(self.query("ADVFILT?")))

    @mark_command
    def set_advanced_filter(self, configuration: AdvancedFilter) -> int:
        """Sets the advanced filter state.

        Args:
            configuration (AdvancedFilter): The advanced filter state to set (e.g., OFF, ON).

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"ADVFILT {configuration.raw_value}")

    @mark_query
    def get_sensitivity(self) -> Sensitivity:
        """Queries the sensitivity setting.

        Returns:
            Sensitivity: The current sensitivity setting.
        """
        return Sensitivity.from_raw_value(int(self.query("SCAL?")))

    @mark_command
    def set_sensitivity(self, sensitivity: Sensitivity) -> int:
        """Sets the sensitivity.

        Args:
            sensitivity (Sensitivity): The sensitivity setting to apply.

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"SCAL {sensitivity.raw_value}")

    @mark_query
    def get_time_constant(self) -> TimeConstant:
        """Queries the time constant setting.

        Returns:
            TimeConstant: The current time constant setting.
        """
        return TimeConstant.from_raw_value(int(self.query("OFLT?")))

    @mark_command
    def set_time_constant(self, time_constant: TimeConstant) -> int:
        """Sets the time constant.

        Args:
            time_constant (TimeConstant): The time constant setting to apply.

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"OFLT {time_constant.raw_value}")

    @mark_query
    def get_filter_slope(self) -> FilterSlope:
        """Queries the filter slope setting.

        Returns:
            FilterSlope: The current filter slope setting (e.g., 6 dB, 12 dB).
        """
        return FilterSlope.from_raw_value(int(self.query("OFSL?")))

    @mark_command
    def set_filter_slope(self, filter_slope: FilterSlope) -> int:
        """Sets the filter slope.

        Args:
            filter_slope (FilterSlope): The filter slope setting to apply (e.g., 6 dB, 12 dB).

        Returns:
            int: Status code indicating the success of the operation.
        """
        return self.command(f"OFSL {filter_slope.raw_value}")

    @mark_query
    def get_output(self, parameter: int) -> float:
        """Queries the output value for a specific parameter.

        Args:
            parameter (int): The parameter index to query (e.g., 0 for X, 1 for Y, 2 for R, 3 for Theta).

        Returns:
            float: The output value corresponding to the specified parameter.
        """
        return float(self.query(f"OUTP? {parameter}"))

    @mark_query
    def get_display_output(self, parameter: int) -> float:
        """Queries the display output value for a specific parameter.

        Args:
            parameter (int): The parameter index to query (e.g., 0 for X, 1 for Y, 2 for R, 3 for Theta).

        Returns:
            float: The display output value corresponding to the specified parameter.
        """
        return float(self.query(f"OUTR? {parameter}"))

    @mark_query
    def get_x(self) -> float:
        """Queries the X output value.

        Returns:
            float: The X output value.
        """
        return float(self.query("OUTP? 0"))

    @mark_query
    def get_y(self) -> float:
        """Queries the Y output value.

        Returns:
            float: The Y output value.
        """
        return float(self.query("OUTP? 1"))

    @mark_query
    def get_r(self) -> float:
        """Queries the R output value.

        Returns:
            float: The R output value.
        """
        return float(self.query("OUTP? 2"))

    @mark_query
    def get_theta(self) -> float:
        """Queries the Theta output value.

        Returns:
            float: The Theta output value in degrees.
        """
        return float(self.query("OUTP? 3"))

    @mark_query
    def get_xy(self) -> list[float]:
        """Queries both X and Y output values simultaneously.

        Returns:
            list[float]: A list containing the X and Y output values.
        """
        return [float(s) for s in self.query("SNAP? 0,1").split(",")]
