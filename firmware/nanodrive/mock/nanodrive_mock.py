#!/usr/bin/env python3
"""NanoDrive v0.9 protocol mock for stdio or TCP tests."""

import argparse
import socket
import sys


class MockNanoDrive:
    def __init__(self):
        self.enc_l = 0
        self.enc_r = 0
        self.battery_mv = 7600
        self.motors_enabled = False
        self.emergency_stop = False
        self.motion_active = False
        self.timeout_ms = 2000
        self.di_l = False
        self.di_r = False

    def status(self):
        return (
            f"ST:L{self.enc_l},R{self.enc_r},V{self.battery_mv},"
            f"E{int(self.emergency_stop)},M{int(self.motion_active)}"
        )

    def process(self, command):
        operation, _, argument = command.strip().upper().partition(":")
        parameters = argument.split(",") if argument else []

        if operation == "PING":
            return "OK:PONG:v0.9"
        if operation == "EN":
            self.motors_enabled = bool(parameters and parameters[0] != "0")
            self.emergency_stop = False
            self.motion_active = False
            return f"OK:EN:{int(self.motors_enabled)}"
        if operation == "ST":
            self.motion_active = False
            self.emergency_stop = True
            return "OK:ST"
        if operation == "GS":
            return self.status()
        if operation == "TO":
            self.timeout_ms = max(0, min(10000, int(parameters[0])))
            return f"OK:TO:{self.timeout_ms}"
        if operation == "RS":
            self.enc_l = 0
            self.enc_r = 0
            self.di_l = False
            self.di_r = False
            return "OK:RS:0"
        if operation == "DI":
            return f"DI:L{int(self.di_l)},R{int(self.di_r)}"

        if operation not in {"FW", "BW", "TL", "TR", "VL"}:
            return "ERR:UNKNOWN"
        if not self.motors_enabled:
            return "ERR:DISABLED"
        if self.emergency_stop:
            return "ERR:ESTOP"

        if operation == "VL":
            left = max(-255, min(255, int(parameters[0])))
            right = max(-255, min(255, int(parameters[1])))
        else:
            speed = max(0, min(255, int(parameters[0])))
            left, right = {
                "FW": (speed, speed),
                "BW": (-speed, -speed),
                "TL": (-speed, speed),
                "TR": (speed, -speed),
            }[operation]

        self.enc_l += left
        self.enc_r += right
        self.di_l = True
        self.di_r = True
        self.motion_active = True
        return self.status()


def run_stdio(mock):
    print("NanoDrive v0.9")
    print("READY")
    for line in sys.stdin:
        command = line.strip()
        if command:
            print(mock.process(command), flush=True)


def run_tcp(mock, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", port))
        server.listen(1)
        print(f"Mock NanoDrive listening on 127.0.0.1:{port}", flush=True)
        while True:
            connection, _ = server.accept()
            with connection:
                connection.sendall(b"NanoDrive v0.9\nREADY\n")
                stream = connection.makefile("r", encoding="utf-8", newline="\n")
                for line in stream:
                    response = mock.process(line)
                    connection.sendall((response + "\n").encode())


def main():
    parser = argparse.ArgumentParser(description="NanoDrive v0.9 mock")
    parser.add_argument("--tcp", type=int, help="listen on localhost TCP port")
    arguments = parser.parse_args()
    mock = MockNanoDrive()
    if arguments.tcp:
        run_tcp(mock, arguments.tcp)
    else:
        run_stdio(mock)


if __name__ == "__main__":
    main()
