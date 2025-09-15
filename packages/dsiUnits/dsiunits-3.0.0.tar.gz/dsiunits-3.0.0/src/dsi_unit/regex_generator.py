"""Functions for generate regex expressions."""

from dsi_unit.unit_mapping import (
    DSI_UNIT_TO_LATEX_MAP,
    INVALID_UNITS_PREFIXES_MAP,
    NO_PREFIX_N_EXPONENT_UNITS,
    NO_PREFIX_UNITS,
    PREFIX_TO_LATEX_MAP,
)

_DEFAULT_EXP_REGEX = r"(\\tothe\{-?\d+([\._]\d+)?\})?"


def generate_regex(xsd_flavoured: bool = False) -> str:
    """
    Generate a regex that matches D-SI unit strings, as well as other unit strings if they are marked with | as the
    first character. This matches the requirements for the si:unitType in the DCC.

    Parameters
    ----------
    xsd_flavoured : bool, default=False
        If True, generates a regex that can be used in a XSD schema for XML.
        If False, a regex is generated that can be used with most major regex implementations,
        for example python or JavaScript.
    """
    dsi_regex = _get_dsi_regex()
    non_dsi_regex = r"(\|.*)"

    unit_regex = rf"({dsi_regex}|{non_dsi_regex})"
    return rf"\s*{unit_regex}\s*" if xsd_flavoured else rf"^{unit_regex}$"


def generate_list_regex(xsd_flavoured: bool = False) -> str:
    """
    Generate a regex that matches a whitespace-separated list of D-SI units. May be used for a si:unitXMLListType
    in the DCC.

    Parameters
    ----------
    xsd_flavoured : bool, default=False
        If True, generates a regex that can be used in a XSD schema for XML.
        If False, a regex is generated that can be used with most major regex implementations,
        for example python or JavaScript.
    """
    dsi_regex = _get_dsi_regex()
    non_dsi_regex = r"(\|\S*)"  # for the list, whitespace chars are not allowed in units
    unit_regex = f"({dsi_regex}|{non_dsi_regex})"

    unit_list_regex = rf"({unit_regex}(\s{unit_regex})*)"
    return rf"\s*{unit_list_regex}\s*" if xsd_flavoured else rf"^{unit_list_regex}$"


def _get_dsi_regex() -> str:
    """Generate a regex that matches D-SI unit strings."""
    prefixes_set = set(PREFIX_TO_LATEX_MAP)
    prefixes_set.remove("")

    # These units can't have a prefix (R010, \one is treated separately in R014).
    no_prefix_regex = f"({_get_unit_regex(NO_PREFIX_UNITS)}{_DEFAULT_EXP_REGEX})"

    # Can't enforce the second part of R010 because we don't know if \second\tothe{-1} is used for frequency
    # or quantity of rotation

    # gram can't have prefix kilo (R011)
    # bel can't have prefix deci (R012)
    invalid_prefix_regex_list = [
        rf"({_get_prefix_regex(prefixes_set - {prefix})}(\\{unit}){_DEFAULT_EXP_REGEX})"
        for unit, prefix in INVALID_UNITS_PREFIXES_MAP.items()
    ]

    # \one, \percent and \ppm can't have prefix or exponent (R010 and R014)
    no_exp_regex = _get_unit_regex(NO_PREFIX_N_EXPONENT_UNITS)

    # all other cases
    default_prefix_regex = _get_prefix_regex(PREFIX_TO_LATEX_MAP)
    extended_no_prefix_units = NO_PREFIX_UNITS | NO_PREFIX_N_EXPONENT_UNITS | INVALID_UNITS_PREFIXES_MAP.keys()
    default_unit_regex = _get_unit_regex(
        [unit for unit in DSI_UNIT_TO_LATEX_MAP if unit not in extended_no_prefix_units]
    )
    default_regex = f"({default_prefix_regex}{default_unit_regex}{_DEFAULT_EXP_REGEX})"

    dsi_regex_without_per = f"({'|'.join([no_prefix_regex, no_exp_regex, default_regex, *invalid_prefix_regex_list])})+"

    return rf"({dsi_regex_without_per}(\\per{dsi_regex_without_per})?)"


def _get_prefix_regex(prefixes: list) -> str:
    """
    Generate a regex that matches any of the prefixes in the list, or an empty string (so, no prefix). The prefixes
    shall be given without the leading backslash, it will be added for the regex.
    """
    return f"{_get_unit_regex(prefixes)}?"


def _get_unit_regex(units: list) -> str:
    """
    Generate a regex that matches any of the units in the list. The units shall be given without the leading
    backslash, it will be added for the regex.
    """
    joined_units = "|".join(rf"(\\{item})" for item in units)
    return f"({joined_units})"
