# Changelog

## [2.3.3] - 2025-09-11
### Changed:
- Fixed ethernet communication sending ID in messages
- Python 3.12.10 installation requirements

## [2.3.2] - 2024-02-15
### Changed:
- SWLS resonant converter updated PT100 sensor nomenclature 
- Added driver channel 2 current reading for auxiliary board

## [2.3.1] - 2023-10-18
### Changed:
- SWLS resonant converter name correction for reading variables 

## [2.3.0] - 2023-05-09
### Changed:
- SWLS resonant converter BSMP specification, including new variables, alarms and interlocks

## [2.2.0] - 2023-02-27
### Changed:
- ID of BSMP variables in FAC-DCDC and FAC-DCDC-EMA 
- ID of BSMP variables in FAP-4P and FAP-2P2S 

### Removed:
- "Ground Leakage Overcurrent" from FAC-DCDC and FAC-DCDC-EMA module alarm and interlock lists

## [2.1.0] - 2023-01-18
### Added:
- SWLS resonant converter PS module specification
- Leakage overcurrent interlock for FAC-DCDC and FAC-DCDC-EMA

### Changed:
- Fixed variable type for IIB interlock and alarm registers from FAC-DCDC-EMA PS module

### Removed:
- Obsolete ListVar list from consts

## [1.2.5] - 2022-08-15
### Added:
- `read_csv_dsp_modules_bank`
- `read_csv_param_bank`
- `close_loop` as a gramatically correct alias for `closed_loop`

### Removed:
- Redundant and unused `read_ps_status` calls in var reading functions

## [1.2.4] - 2022-08-12
### Changed:
- Fix identation bug on `get_dsp_modules_bank()`
- List into dict (get/set params) and also returns digital value for FP
- Returns dict for certain FAC/FBP/FAP read_vars() functions

## [1.2.3] - 2022-08-08
### Added:
- Deprecation messages for substituted/altered functions

## [1.2.2] - 2022-07-28
### Added:
- Error messages for BSMP return errors (0xE_)

### Changed:
- `set_slave_add` is now a property, `slave_addr`
- `EthDRS`, `GenericDRS` and `SerialDRS` can be imported from the base module
- Fixed BSMP errors appearing as checksum errors
- Fixed eth-bridge version compatibility troubles (such as including the response status byte in the checksum)

## [1.2.1] - 2022-07-25
### Added:
- Resolution steps on error message
- `save_param_bank` timeout is set to a base safe value

### Changed:
- Empty reply always throws exception
- Fixed exception type on error response (proper `SerialError` response instead of `SerialErrPckgLen`)
- Fixed leftover "broken" messages on a new command when another command times out
- Increases timeout for `save_param_bank`

### Removed:
- Removed `get_ps_model`

## [1.2.0] - 2022-06-21
### Added:
- Support for TCP/IP communication (eth-bridge)
- Base class for different forms of communication
- BSMP validation
- Descriptive exceptions and warnings based on BSMP validation

### Changed:
- `timeout` is now a property
- Connection is handled when every class instance is created instead of requiring `connect`