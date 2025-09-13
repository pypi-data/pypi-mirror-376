#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial  # type: ignore
import time
import sys
import os
import glob
import ast
import hashlib
import textwrap
import serial.tools.list_ports  # type: ignore

__VERSION__ = "1.0.1"

# ===================== Config =====================

SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200
RAW_OUTPUT = False

# Size of upload chunk (both host and receiver must match)
UP_CHUNK = 256  # 256/512/1024/2048 depending on memory constraints
READY_TIMEOUT_S = 2.0  # wait 'RDY'
ACK_TIMEOUT_S = 5.0  # wait 'OK/KO' for chunk

# ================= Raw REPL helpers =================

RAW_OK = b"raw REPL; CTRL-B to exit\r\n>"


RECV_CODE = """
import sys, hashlib, os, gc

UP_CHUNK = {UP_CHUNK}

def _readline():
    s = b''
    while True:
        ch = sys.stdin.buffer.read(1)
        if not ch:
            break
        if ch == b'\\n':
            break
        s += ch
    return s.decode()

def _read_n(n):
    buf = b''
    while len(buf) < n:
        chunk = sys.stdin.buffer.read(n - len(buf))
        if not chunk:
            break
        buf += chunk
    return buf

def _is_hex64(s):
    if len(s) != 64:
        return False
    s = s.lower()
    for c in s:
        if not (('0' <= c <= '9') or ('a' <= c <= 'f')):
            return False
    return True

def _hex2bytes(s):
    # 64 hex -> 32 bytes
    s = s.lower()
    out = bytearray(32)
    for i in range(32):
        hi = s[2*i]; lo = s[2*i+1]
        def _v(ch):
            oc = ord(ch)
            if 48 <= oc <= 57: return oc - 48    # 0-9
            if 97 <= oc <= 102: return oc - 87   # a-f
            return -1
        hv = _v(hi); lv = _v(lo)
        if hv < 0 or lv < 0:
            return None
        out[i] = (hv<<4) | lv
    return bytes(out)

try:
    print('RDY')  # initial handshake
    fn = _readline().strip()
    try:
        size = int(_readline().strip() or '0')
    except:
        print('ERR:BAD_SIZE_LINE')
        raise SystemExit

    written = 0
    # Crear/truncar
    try:
        f = open(fn, 'wb'); f.close()
    except Exception as e:
        s = str(e);  s = s if len(s) < 80 else s[:77]+'...'
        print('ERR:OPEN:{}'.format(s))
        raise SystemExit

    idx = 0
    while written < size:
        # Announce we are going to read the next chunk (host must wait for this)
        idx += 1
        print('CH:{}'.format(idx))

        # Read expected hash line (64 hex)
        hline = _readline().strip()
        if not _is_hex64(hline):
            msg = hline if len(hline) < 40 else (hline[:37]+'...')
            print('ERR:BAD_HASH_LINE:{}'.format(msg))
            raise SystemExit

        # Read data (up to UP_CHUNK or remaining)
        need = size - written
        if need > UP_CHUNK:
            need = UP_CHUNK
        data = _read_n(need)
        if not data or len(data) != need:
            print('ERR:SHORT_READ:{}<{}'.format(len(data) if data else 0, need))
            raise SystemExit

        # Compute SHA256 of data and compare to expected
        h = hashlib.sha256()
        h.update(data)
        calc = h.digest()
        exp = _hex2bytes(hline)
        if exp is None:
            print('ERR:BAD_HEX_DECODE')
            raise SystemExit

        if calc == exp:
            try:
                with open(fn, 'ab') as wf:
                    wf.write(data)
            except Exception as e:
                s = str(e); s = s if len(s) < 80 else s[:77]+'...'
                print('ERR:WRITE:{}'.format(s))
                raise SystemExit
            written += len(data)
            print('OK')
        else:
            # Return prefix of calculated hash for debugging
            pref = ''.join('{{:02x}}'.format(b) for b in calc[:16])
            print('KO:'+pref)

        # Force garbage collection after each chunk
        gc.collect()

    print('DONE:{}'.format(written))

except SystemExit:
    pass
except Exception as e:
    s = str(e)
    if len(s) > 80: s = s[:77]+'...'
    print('ERR:EXC:{}'.format(s))
"""  # noqa: E501

HEADER = (
    "ESP32 Manager - MicroPython file manager over "
    f"serial (version {__VERSION__})"
)


def _read_until(port, token: bytes, timeout=3.0):
    t0 = time.time()
    buf = b""
    while time.time() - t0 < timeout:
        chunk = port.read_all()
        if chunk:
            buf += chunk
            if token in buf:
                return buf
        time.sleep(0.01)
    return buf  # Returns whatever was read (for debug)


def read_until_with_prefill(port, token: bytes, prefill: bytes, timeout=3.0):
    """
    Looks for 'token' first in 'prefill'. If not found, continues reading from
    the port until found or timeout expires. Returns prefill + what was read.
    """
    if token in prefill:
        return prefill
    t0 = time.time()
    buf = (
        prefill[:]
        if isinstance(prefill, (bytes, bytearray))
        else bytes(prefill)
    )
    while time.time() - t0 < timeout:
        chunk = port.read_all()
        if chunk:
            buf += chunk
            if token in buf:
                break
        time.sleep(0.01)
    return buf


def enter_raw_repl(port):
    # Ctrl-C to stop any running program
    port.write(b"\x03")
    time.sleep(0.1)
    port.reset_input_buffer()
    # Ctrl-A to enter raw REPL
    port.write(b"\x01")
    got = _read_until(port, RAW_OK, timeout=1.5)
    if RAW_OK not in got:
        raise RuntimeError(
            "Could not enter raw REPL. Got:\n" + got.decode(errors="ignore")
        )


def exit_raw_repl(port):
    port.write(b"\x02")  # Ctrl-B
    time.sleep(0.1)


def raw_run(port, code: str):
    """
    Sends 'code' to raw REPL and runs it (Ctrl-D). Does not read output.
    """
    port.reset_input_buffer()
    port.write(code.encode("utf-8"))
    port.write(b"\x04")  # Ctrl-D -> ejecutar


def raw_read_until_eof(port, timeout=12.0):
    """
    Reads program output in raw REPL until seeing 0x04 (EOF of program).
    Returns (out_bytes, saw_eof: bool)
    """
    t0 = time.time()
    out = b""
    saw_eof = False
    while time.time() - t0 < timeout:
        chunk = port.read_all()
        if chunk:
            out += chunk
            if b"\x04" in out:
                saw_eof = True
                break
        time.sleep(0.01)
    return out, saw_eof


def write_all(port, data: bytes, drain_every=512):
    """
    Writes all 'data' to the port. Drains device stdout periodically.
    """
    total = 0
    n = len(data)
    last_drain = 0
    while total < n:
        sent = port.write(data[total:])
        if not sent:
            sent = 0
        total += sent
        if total - last_drain >= drain_every:
            _ = port.read_all()  # discard intermediate 'OK/KO/K/ERR'
            last_drain = total


# ================= Friendly REPL helpers =================


def serial_repl_ready(port):
    # Send Ctrl-C and see if there's a >>> prompt
    port.write(b"\x03")
    time.sleep(0.2)
    port.reset_input_buffer()
    port.write(b"\r\n")
    time.sleep(0.2)
    port.write(b"\r\n")
    time.sleep(0.2)
    response = port.read_all().decode(errors="ignore")
    return ">>> " in response


def connect_serial():
    try:
        port = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1, write_timeout=5)
        port.timeout = 2.5
        port.dtr = False
        port.rts = False
        # Check REPL prompt (3 attempts)
        ready = False
        for _ in range(3):
            if serial_repl_ready(port):
                ready = True
                break
            time.sleep(2)
        if ready:
            print(f"✅ Connected to {SERIAL_PORT} at {BAUDRATE} baud.")
            return port
        else:
            print(
                "❌ No REPL prompt detected. Is the ESP32 running MicroPython?"
            )
            sys.exit(1)
    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")
        sys.exit(1)


def send(port, cmd, delay=0.1):
    port.write(cmd.encode("utf-8") + b"\r")
    time.sleep(delay)


def send_and_capture(port, cmd, delay=0.3):
    port.reset_input_buffer()
    port.write(cmd.encode("utf-8") + b"\r")
    time.sleep(delay)
    response = port.read_all().decode(errors="ignore")
    lines = response.splitlines()
    filtered = [
        line
        for line in lines
        if not line.strip().startswith(">>>") and line.strip() != cmd
    ]
    return "\n".join(filtered)


# ================= Device file ops (friendly REPL) =================


def list_files_on_device():
    port = connect_serial()
    out = send_and_capture(port, "import os; print(os.listdir())")
    port.close()
    try:
        return ast.literal_eval(out.strip())
    except Exception:
        print("❌ Failed to parse file list from ESP32.")
        return []


def cmd_ls():
    files = list_files_on_device()
    print("\n".join(files))


def cmd_get(files):
    port = connect_serial()
    for filename in files:
        if not RAW_OUTPUT:
            print(f"⬇️  Downloading {filename}")
        try:
            content = send_and_capture(
                port,
                f"f = open('{filename}', 'r'); print(f.read()); f.close()",
            )
            with open(filename, "w") as f:
                f.write(content)
            if not RAW_OUTPUT:
                print(f"📝 Saved as {filename}")
        except Exception as e:
            print(f"❌ Failed to get {filename}: {e}")
    port.close()


def cmd_cat(files):
    port = connect_serial()
    for filename in files:
        if not RAW_OUTPUT:
            print(f"📄 {filename}:")
        try:
            content = send_and_capture(
                port,
                f"f = open('{filename}', 'r'); print(f.read()); f.close()",
            )
            print(content.strip())
        except Exception as e:
            print(f"❌ Failed to read {filename}: {e}")
        if not RAW_OUTPUT:
            print("-" * 40)
    port.close()


def cmd_rm(files):
    port = connect_serial()
    for filename in files:
        if not RAW_OUTPUT:
            print(f"🗑️  Deleting {filename}")
        try:
            send(port, f"import os; os.remove('{filename}')")
        except Exception as e:
            print(f"❌ Failed to delete {filename}: {e}")
    port.close()


def cmd_clean():
    if not RAW_OUTPUT:
        print("🧹 Deleting all files on the ESP32...")
    files = list_files_on_device()
    if not files:
        if not RAW_OUTPUT:
            print("ℹ️ No files to delete.")
        return
    if "boot.py" in files:
        if not RAW_OUTPUT:
            print("⚠️  Preserving boot.py")
        files.remove("boot.py")
    cmd_rm(files)


def cmd_run():
    if not RAW_OUTPUT:
        print("🔁 Rebooting ESP32 to run main.py...")
    port = connect_serial()
    send(port, "import machine; machine.reset()")
    port.close()


# ================= Upload (chunked with per-chunk SHA256) =================


def cmd_put(files):

    # Check that local files exist
    valid_files = []
    for path in files:
        if not os.path.exists(path):
            print(f"❌ Local file does not exist: {path}")
        else:
            valid_files.append(path)

    if not valid_files:
        print("❌ No valid files to upload.")
        return False

    # Embedded receiver: handshake RDY -> filename/size -> loop (hash_line +
    # data) -> OK/KO -> DONE:n
    recv_code = textwrap.dedent(RECV_CODE.replace("{UP_CHUNK}", str(UP_CHUNK)))
    port = connect_serial()

    total_files = len(files)
    for (idx, path) in enumerate(files):
        if os.path.isdir(path):
            if not RAW_OUTPUT:
                print(f"📁 Skipping directory: {path}")
            continue

        # leer archivo local
        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
        except Exception as e:
            print(f"❌ Could not read {path}: {e}")
            continue

        filename = os.path.basename(path)
        file_size = len(raw_bytes)
        print(
            f"⬆️  Uploading {idx+1}/{total_files} "
            f"- {path} → {filename} ({file_size} bytes)"
        )

        try:
            # Enter raw REPL and start receiver
            enter_raw_repl(port)
            raw_run(port, recv_code)

            # Wait for initial RDY handshake from receiver (with small drain)
            ready_buf = _read_until(port, b"RDY", timeout=READY_TIMEOUT_S)
            if b"RDY" not in ready_buf:
                extra = port.read_all()
                ready_buf += extra or b""
                if b"RDY" not in ready_buf:
                    print(
                        "❌ Did not see RDY from device, got:\n"
                        + ready_buf.decode(errors="ignore")
                    )
                    return False

            # Send filename and size
            port.write((filename + "\n").encode("utf-8"))
            port.write((str(file_size) + "\n").encode("utf-8"))
            # Small pause to let the device prepare for chunked upload
            time.sleep(0.1)

            # Loop over chunks
            total_chunks = (file_size + UP_CHUNK - 1) // UP_CHUNK
            processed_chunks = 0
            next_mark = 10

            offset = 0
            chunk_index = 0
            prebuf = b""
            while offset < file_size:
                chunk_index += 1
                end = min(offset + UP_CHUNK, file_size)
                data = raw_bytes[offset:end]
                ch_tag = f"CH:{chunk_index}".encode("utf-8")

                # Wait for CH:<n> from device (with prefill from previous read)
                ch_buf = read_until_with_prefill(
                    port, ch_tag, prebuf, timeout=ACK_TIMEOUT_S
                )
                if ch_tag not in ch_buf:
                    # Drain in case it's coming stuck
                    extra = port.read_all()
                    ch_buf += extra or b""
                    if ch_tag not in ch_buf:
                        print(
                            f"❌ Did not see CH:{chunk_index} from device, "
                            f"got:\n{ch_buf.decode(errors='ignore')}"
                        )
                        return False

                # Calculate hash and send hash+data
                h = hashlib.sha256(data).hexdigest()
                port.write((h + "\n").encode("utf-8"))
                write_all(port, data)
                time.sleep(0.05)

                # Wait up to ACK_TIMEOUT_S seconds for OK/KO/ERR from device
                t0 = time.time()
                got = b""
                verdict = None
                while time.time() - t0 < ACK_TIMEOUT_S:
                    chunk_out = port.read_all()
                    if chunk_out:
                        got += chunk_out
                        if b"OK" in got:
                            verdict = "OK"
                            break
                        if b"KO" in got:
                            verdict = "KO"
                            break
                        if b"ERR:" in got:
                            text_err = got.decode(errors="ignore")
                            print("❌ Receiver error during chunk:")
                            print(text_err.strip())
                            return False
                    time.sleep(0.01)

                if verdict is None and not RAW_OUTPUT:
                    print(
                        "🧪 Device said (timeout window):",
                        got.decode(errors="ignore") or "(empty)",
                    )

                if verdict == "OK":
                    offset = end
                    processed_chunks += 1
                    # prefill for the NEXT CH:<n+1>
                    # keep what was read (may contain the next CH)
                    prebuf = got
                else:
                    # Single retry of the SAME chunk
                    reason = "KO" if verdict == "KO" else "TIMEOUT"
                    if not RAW_OUTPUT:
                        print(
                            f"⚠️  Chunk {chunk_index}/{total_chunks} "
                            f"{reason}. Retrying once..."
                        )

                    # Before retrying, wait for the same CH:<n> again
                    ch_buf2 = read_until_with_prefill(
                        port, ch_tag, got, timeout=ACK_TIMEOUT_S
                    )
                    if ch_tag not in ch_buf2:
                        extra2 = port.read_all()
                        ch_buf2 += extra2 or b""
                        if ch_tag not in ch_buf2:
                            print(
                                f"❌ Retry: did not see CH:{chunk_index}. "
                                f"Got:\n{ch_buf2.decode(errors='ignore')}"
                            )
                            return False

                    port.write((h + "\n").encode("utf-8"))
                    write_all(port, data)

                    t0 = time.time()
                    got2 = b""
                    verdict2 = None
                    while time.time() - t0 < ACK_TIMEOUT_S:
                        chunk_out = port.read_all()
                        if chunk_out:
                            got2 += chunk_out
                            if b"OK" in got2:
                                verdict2 = "OK"
                                break
                            if b"KO" in got2:
                                verdict2 = "KO"
                                break
                            if b"ERR:" in got2:
                                text_err = got2.decode(errors="ignore")
                                print("❌ Receiver error during retry:")
                                print(text_err.strip())
                                return False
                        time.sleep(0.01)

                    if verdict2 == "OK":
                        offset = end
                        processed_chunks += 1
                        # keep what was read (may contain the next CH)
                        prebuf = got2
                    else:
                        text_v1 = got.decode(errors="ignore").strip()
                        text_v2 = got2.decode(errors="ignore").strip()
                        print(
                            "❌ Chunk failed permanently at index "
                            f"{chunk_index} (offset {offset}..{end})"
                        )
                        print("🧪 First attempt device output:")
                        print(text_v1 or "(empty)")
                        print("🧪 Retry attempt device output:")
                        print(text_v2 or "(empty)")
                        return False

                # Progress (CLEANUP: now only here, at end of loop)
                if not RAW_OUTPUT:
                    pct = int((processed_chunks * 100) / total_chunks)
                    if pct >= next_mark or processed_chunks == total_chunks:
                        print(
                            f"📶 Progress: {pct}% "
                            f"({processed_chunks}/{total_chunks} chunks)"
                        )
                        while pct >= next_mark:
                            next_mark += 10

            # Close stdin so the receiver emits DONE and finishes
            port.write(b"\x04")
            out, saw_eof = raw_read_until_eof(port, timeout=12.0)
            text = out.decode(errors="ignore").strip()

            # Look for line starting with DONE: and parse byte count
            done_bytes = None
            for line in text.splitlines():
                if line.startswith("DONE:"):
                    try:
                        done_bytes = int(line.split(":", 1)[1])
                    except Exception:
                        pass

            if done_bytes != file_size:
                print("⚠️  DONE mismatch or not seen.")
                if not RAW_OUTPUT:
                    print("🧪 Device output:")
                    print(text or "(empty)")
                return False

            if not RAW_OUTPUT:
                print(
                    f"✅ Upload completed: "
                    f"{filename} ({processed_chunks}/{total_chunks} chunks)"
                )

        except Exception as e:
            print(f"❌ Upload failed for {filename}: {e}")
            return False
        finally:
            try:
                exit_raw_repl(port)
            except Exception:
                pass

        if idx < total_files - 1 and not RAW_OUTPUT:
            print("-" * 40)

    port.close()
    return True


# ================= CLI =================


def print_help():
    help_text = """
Usage:
  esp32-manager <command> [files...]

Available commands:
  ls                    List files on the ESP32
  put file(s)           Upload file(s) to the ESP32 (chunked with per-chunk SHA256)
  get file(s)           Download file(s) from the ESP32
  cat file(s)           Show contents of file(s) on the ESP32
  rm  file(s)           Delete file(s) from the ESP32
  clean                 Delete all files from the ESP32
  run                   Reset board (machine.reset())

  help, --help, -h      Show this help message

Options:
  --port DEVICE         Set serial port (default: /dev/ttyUSB0)
  --baudrate N          Set baudrate (default: 115200)
  --raw                 Suppress emojis/extra formatting (for scripts)

Examples:
  esp32-manager ls
  esp32-manager put main.py
  esp32-manager put src/*
  esp32-manager get main.py config.yaml
  esp32-manager cat main.py boot.py
  esp32-manager rm main.py
  esp32-manager clean
  esp32-manager run

  esp32-manager ls --port /dev/ttyUSB1 --baudrate 921600
  esp32-manager put main.py --raw
"""  # noqa: E501
    print(help_text.strip())


def main():
    global RAW_OUTPUT, SERIAL_PORT, BAUDRATE

    if "--version" in sys.argv:
        print(f"ESP32 Manager version {__VERSION__}")
        sys.exit(0)

    if "--raw" in sys.argv:
        RAW_OUTPUT = True
        sys.argv.remove("--raw")
    else:
        print(HEADER)
        print()

    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        try:
            SERIAL_PORT = sys.argv[idx + 1]
            del sys.argv[idx : idx + 2]
        except IndexError:
            print("❌ Missing value for --port")
            sys.exit(1)
    else:

        # Auto-detect
        try:
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                if (
                    "USB" in p.device
                    or "CP210" in p.description
                    or "UART" in p.description
                    or "CH340" in p.description
                ):
                    SERIAL_PORT = p.device
                    if not RAW_OUTPUT:
                        print(f"📡 Auto-detected serial port: {SERIAL_PORT}")
                    break
        except Exception:
            pass

    if "--baudrate" in sys.argv:
        idx = sys.argv.index("--baudrate")
        try:
            BAUDRATE = int(sys.argv[idx + 1])
            del sys.argv[idx : idx + 2]
        except (IndexError, ValueError):
            print("❌ Invalid value for --baudrate")
            sys.exit(1)

    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command in ("help", "--help", "-h"):
        print_help()
        sys.exit(0)

    # Expand local globs (e.g. src/*.py)
    expanded_args = []
    for arg in args:
        expanded = glob.glob(arg)
        if not expanded:
            expanded_args.append(arg)
        else:
            expanded_args.extend(expanded)

    if command == "ls":
        cmd_ls()
    elif command == "put":
        if not expanded_args:
            print("❌ No files specified for upload.")
            sys.exit(1)
        if not cmd_put(expanded_args):
            sys.exit(1)
    elif command == "get":
        if not expanded_args:
            print("❌ No files specified for download.")
            sys.exit(1)
        cmd_get(expanded_args)
    elif command == "cat":
        if not expanded_args:
            print("❌ No files specified to read.")
            sys.exit(1)
        cmd_cat(expanded_args)
    elif command == "rm":
        if not expanded_args:
            print("❌ No files specified for deletion.")
            sys.exit(1)
        cmd_rm(expanded_args)
    elif command == "clean":
        cmd_clean()
    elif command == "run":
        cmd_run()
    else:
        print(f"❌ Unknown command: {command}")
        print_help()
        sys.exit(1)
