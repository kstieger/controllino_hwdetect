#!/usr/bin/env python3

import os
import argparse
import json


class CpuInfo:
    def __init__(self,
                 num_processors=0,
                 cpu_implementer="",
                 cpu_architecture="",
                 cpu_variant="",
                 cpu_part="",
                 cpu_revision="",
                 hw_serial="",
                 hw_hardware="",
                 hw_revision="",
                 hw_model="") -> None:
        self.num_processors = num_processors
        self.cpu_implementer = cpu_implementer
        self.cpu_architecture = cpu_architecture
        self.cpu_variant = cpu_variant
        self.cpu_part = cpu_part
        self.cpu_revision = cpu_revision
        self.hw_serial = hw_serial
        self.hw_hardware = hw_hardware
        self.hw_revision = hw_revision
        self.hw_model = hw_model

# class HwInfo:
#     def __init__(self,
#                  model=None,
#                  revision=None,
#                  platform=None,
#                  cpu_serial=None,
#                  mac_eth0=None,
#                  mac_wlan0=None,
#                  debug=None) -> None:
#         self.model = model
#         self.revision = revision
#         self.platform = platform
#         self.cpu_serial = cpu_serial
#         self.mac_eth0 = mac_eth0
#         self.mac_wlan0 = mac_wlan0
#         self.debug = debug


HW_DEFS = [
    {
        "name": "Controllino Hotspot",
        "revision": "1.0",
        "platform": "Raspberry Pi 4b rev1.4",
        "cpuinfo": CpuInfo(
            num_processors=4,
            cpu_implementer="0x41",
            cpu_architecture="8",
            cpu_variant="0x0",
            cpu_part="0xd08",
            cpu_revision="3",
            hw_hardware="bcm2835",
            hw_revision="d03114",
            hw_model="raspberry pi 4 model b rev 1.4"
        )
    },
    {
        "name": "Controllino Hotspot",
        "revision": "1.1",
        "platform": "Rock Pi 4b rev1.5",
        "cpuinfo": CpuInfo(
            num_processors=6,
            cpu_implementer="0x41",
            cpu_architecture="8",
            cpu_variant="0x0",
            cpu_part="0xd03|0xd08",
            cpu_revision="2|4",
            hw_hardware="",
            hw_revision="",
            hw_model=""
        )
    }
]


def get_cpuinfo():
    with open("/proc/cpuinfo") as f:
        raw_cpuinfo = f.read()
    list_cpuinfo = raw_cpuinfo.split("\n\n")
    list_procs = [x for x in list_cpuinfo if x.startswith("processor")]
    procs = []
    for p in list_procs:
        pd = {}
        p = p.splitlines()
        for pv in p:
            k, v = pv.split(": ")
            pd[k.strip().lower()] = v.strip()
        procs.append(pd)
    hwinfo = [x for x in list_cpuinfo if not x.startswith(
        "processor") and "SERIAL" in x.upper()][0]
    c_info = CpuInfo()
    c_info.num_processors = len(procs)

    def get_props(k):
        prop = sorted(list(set([x.get(k) for x in procs])))
        if len(prop) > 1:
            return "|".join(prop)
        elif len(prop) < 1:
            print("no value for {k} ???")
            return ""
        else:
            return prop[0]

    c_info.cpu_implementer = get_props("cpu implementer")
    c_info.cpu_architecture = get_props("cpu architecture")
    c_info.cpu_variant = get_props("cpu variant")
    c_info.cpu_part = get_props("cpu part")
    c_info.cpu_revision = get_props("cpu revision")

    hwinfo = {x.split(": ", 1)[0].strip().lower(): x.split(
        ": ", 1)[-1].strip().lower() for x in hwinfo.splitlines()}
    c_info.hw_hardware = hwinfo.get("hardware", "")
    c_info.hw_revision = hwinfo.get("revision", "")
    c_info.hw_serial = hwinfo.get("serial", "")
    c_info.hw_model = hwinfo.get("model", "")

    return c_info


def get_mac(device):
    address_file = f"/sys/class/net/{device}/address"
    if not os.path.isfile(address_file):
        return "-"
    with open(address_file) as f:
        mac = f.read()
    return mac.strip()


def get_hwinfo(cur):
    for model in HW_DEFS:
        if model["cpuinfo"].num_processors == cur.num_processors and \
                model["cpuinfo"].cpu_implementer == cur.cpu_implementer and \
                model["cpuinfo"].cpu_architecture == cur.cpu_architecture and \
                model["cpuinfo"].cpu_variant == cur.cpu_variant and \
                model["cpuinfo"].cpu_part == cur.cpu_part and \
                model["cpuinfo"].cpu_revision == cur.cpu_revision and \
                model["cpuinfo"].hw_hardware == cur.hw_hardware and \
                model["cpuinfo"].hw_revision == cur.hw_revision and \
                model["cpuinfo"].hw_model == cur.hw_model:
            out = {
                "model": model['name'],
                "revision": model['revision'],
                "platform": model['platform'],
                "cpu_serial": cur.hw_serial,
                "mac_eth0": get_mac('eth0'),
                "mac_wlan0": get_mac('wlan0'),
            }
            return out
    out = {
        "model": model['name'],
        "revision": model['revision'],
        "platform": model['platform'],
        "cpu_serial": cur.hw_serial,
        "mac_eth0": get_mac('eth0'),
        "mac_wlan0": get_mac('wlan0'),
        "debug": {
            "num_processors": cur.num_processors,
            "cpu_implementer": cur.cpu_implementer,
            "cpu_architecture": cur.cpu_architecture,
            "cpu_variant": cur.cpu_variant,
            "cpu_part": cur.cpu_part,
            "cpu_revision": cur.cpu_revision,
            "hw_hardware": cur.hw_hardware,
            "hw_revision": cur.hw_revision,
            "hw_model": cur.hw_model
        }
    }
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(fromfile_prefix_chars="@")
    parser.add_argument(
        '-w', '--write',
        action="store_true",
        help="write hardware info to /var/run/controllino (hwinfo.json and hwinfo.env)"
    )
    parser.add_argument(
        '-p', '--print',
        action="store_true",
        help="print hardware info"
    )

    args = parser.parse_args()
    hwinfo = get_hwinfo(get_cpuinfo())
    
    if args.write:
        with open("/var/run/controllino/hwinfo.json", "w") as f:
            json.dump(hwinfo, f, indent=2)
        env = "# Controllino Hardware Info\n"
        for k, v in hwinfo.items():
            if not k == "debug":
                env += f'CTRL_{k.upper()}="{v}"\n'
        with open("/var/run/controllino/hwinfo.env", "w") as f:
            f.write(env)
    
    if args.print:
        env = "# Controllino Hardware Info\n"
        for k, v in hwinfo.items():
            if not k == "debug":
                env += f'CTRL_{k.upper()}="{v}"\n'
        print(env)
    
    if not args.print and not args.write:
        parser.print_help()
