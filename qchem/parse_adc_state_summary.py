#!/usr/bin/env python3
import re
import scipy.constants


def find_next_match(fiter, regex, max_advance=None):
    """
    Advance the file iterator until the regex matches,
    then return the new file iterator position as well
    as the match object
    """
    if isinstance(regex, str):
        regex = re.compile(regex)

    while True:
        line = next(fiter).strip()
        match = regex.match(line)
        if match:
            return fiter, match


def parse_state_amplitudes(fiter):
    re_dashes = re.compile(" *" + 20 * "-")
    # Assert that the next line begins the table
    line = next(fiter)
    assert re.match(re_dashes, line)
    line = next(fiter)

    re_orbital = re.compile(r"""
        \s*                        # Skip leading whitespace
        (?P<num>[0-9]+)            # Number of the orbital
        [ ]
        \((?P<irrep>[A-Za-z1-9"']+)\)  # Irrep of the orbital
        [ ]
        (?P<spin>[AB])             # Spin of the orbital
    """, re.VERBOSE)
    spin_map = {"A": "alpha", "B": "beta"}

    amplitudes = []
    while not re.match(re_dashes, line):
        match = re.match("^[^.]*(?P<value>[0-9eE.+-]+)\s*$", line)
        ampl = {"value": float(match.group("value")), "occ": [], "virt": []}

        all_matches = re.findall(re_orbital, line)
        assert len(all_matches) % 2 == 0
        for im, match in enumerate(all_matches):
            is_occ = im < len(all_matches) // 2
            key = "occ" if is_occ else "virt"

            ampl[key].append({
                "number": int(match[0]),
                "irrep": match[1],
                "spin": spin_map[match[2]],
            })
        amplitudes.append(ampl)
        line = next(fiter)
    return fiter, amplitudes


def parse_excited_state(fiter):
    EH_in_eV = scipy.constants.value("atomic unit of energy") \
            / scipy.constants.value("electron volt")

    ret = {}

    # Search beginning
    re_exci = re.compile(
        r"Excited state +(?P<id>[0-9]+) +\(((?P<kind>[a-z]+), )?"
        "(?P<irrep>[A-Za-z1-9\"'])\) "
        "*\[(?P<converged>(converged|not converged))\]"
    )
    fiter, match = find_next_match(fiter, re_exci)

    md = match.groupdict()
    ret["order"] = int(md["id"])
    ret["kind"] = md.get("kind", "state")
    ret["irrep"] = md["irrep"]
    ret["converged"] = md["converged"] == "converged"

    re_term_rr = r"Term symbol: (?P<ts>.*)R\^2 = *(?P<rnorm>[0-9eE.+-]+)"
    fiter, match = find_next_match(fiter, re_term_rr, 2)
    md = match.groupdict()
    ret["term_symbol"] = md["ts"].strip()
    ret["rnorm"] = float(md["rnorm"])

    # This is in Hartree
    re_total_energy = r"Total energy: *(?P<energy>[0-9eE.+-]+)"
    fiter, match = find_next_match(fiter, re_total_energy, 1)
    ret["energy"] = float(match.group("energy"))

    # This is in eV
    re_exci_ene = r"Excitation energy: *(?P<energy>[0-9eE.+-]+)"
    fiter, match = find_next_match(fiter, re_exci_ene, 1)
    ret["excitation_energy"] = float(match.group("energy")) / EH_in_eV

    re_singles_doubles = r"V1\^2 = *(?P<singles_squared>[0-9eE.+-]+)" "(, " \
        "V2\^2 = * (?P<doubles_squared>[0-9eE.+-]+))?"
    fiter, match = find_next_match(fiter, re_singles_doubles, 5)
    md = match.groupdict()
    ret["singles_part_norm"] = float(md["singles_squared"])
    if "doubles_squared" in md:
        ret["doubles_part_norm"] = float(md["doubles_squared"])

    #
    # Parse important amplitudes
    #
    fiter, _ = find_next_match(fiter, "Important amplitudes:")
    next(fiter)
    fiter, ret["important_amplitudes"] = parse_state_amplitudes(fiter)

    return ret


def parse_adc_state_summary(infile):
    ret = []
    fiter = iter(infile)

    # Seek until the excited state summary starts
    while "Excited State Summary" not in next(fiter):
        pass

    try:
        # Now parse excited state by excited state
        while True:
            ret.append(parse_excited_state(fiter))
    except StopIteration:
        return ret
    return ret


def main():
    import os
    import sys
    import yaml

    bn = os.path.basename(__file__)
    if len(sys.argv) not in [2, 3]:
        raise SystemExit("Usage is {} <qchem output> [<yaml file>]".format(bn))

    adc_out = sys.argv[1]
    if not os.path.isfile(adc_out):
        raise SystemExit("Provided ADC output file does not exist.")

    if len(sys.argv) == 3:
        yaml_out = sys.argv[2]
    else:
        pre, ext = os.path.splitext(adc_out)
        yaml_out = pre + ".yaml"

    with open(adc_out, "r") as f:
        parsed = parse_adc_state_summary(f)

    with open(yaml_out, "w") as f:
        yaml.safe_dump(parsed, f)


if __name__ == "__main__":
    main()
