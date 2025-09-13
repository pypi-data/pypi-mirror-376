#!/usr/bin/env python3
import socket, ipaddress, threading, itertools, sys, time, queue, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from colorama import init, Fore, Style

# --- colors/init ---
init(autoreset=True)
C_IP = Fore.CYAN + Style.BRIGHT
C_PORT = Fore.YELLOW + Style.BRIGHT
C_FOUND = Fore.GREEN + Style.BRIGHT
C_ERR = Fore.RED + Style.BRIGHT
C_INFO = Fore.MAGENTA + Style.BRIGHT
RESET = Style.RESET_ALL

# --- default config ---
DEFAULT_SCAN_FROM = "192.168.0.1"
DEFAULT_SCAN_END  = "192.168.0.255"
DEFAULT_PORT_START = 80
DEFAULT_PORT_END = 80
MAX_WORKERS = 50
SOCKET_TIMEOUT = 0.35

# --- shared state ---
status_lock = threading.Lock()
current_ip = ""
current_port = 0
scanned_ips = 0
total_ips = 0
stop_spinner = False
found_results = []
message_queue = Queue()

# --- network check ---
def check_network():
    try:
        # Try connecting to a well-known IP (Google DNS)
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

# --- port scan ---
def is_port_open(ip, port, timeout=SOCKET_TIMEOUT):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False

# --- status line spinner ---
def print_status_line():
    spinner = next(print_status_line.spinner)
    with status_lock:
        pct_ip = (scanned_ips / total_ips * 100) if total_ips else 0
        status = (
            f"{Fore.CYAN}[{spinner}] {C_INFO}Scanning {C_IP}{current_ip}{RESET}"
            f"{C_INFO}: {C_PORT}{current_port}{RESET} "
            f"{C_INFO}| IPs: {scanned_ips}/{total_ips} ({pct_ip:5.1f}%)"
        )
    sys.stdout.write("\r" + status + " " * 10)
    sys.stdout.flush()
print_status_line.spinner = itertools.cycle("|/-\\")

# --- scan single IP ---
def scan_ip(ip):
    global current_ip, current_port, scanned_ips
    open_ports = []
    with status_lock:
        current_ip = ip
    for port in range(PORT_START, PORT_END + 1):
        with status_lock:
            current_port = port
        if is_port_open(ip, port):
            open_ports.append(port)
            message_queue.put(f"{C_FOUND}[+] {C_IP}{ip}{RESET} -> Open port: {C_PORT}{port}{RESET}")
    with status_lock:
        scanned_ips += 1
    return (ip, open_ports) if open_ports else None

# --- spinner & message printer thread ---
def spinner_and_queue_thread():
    while not stop_spinner or not message_queue.empty():
        while not message_queue.empty():
            msg = message_queue.get()
            sys.stdout.write("\r" + " " * 120 + "\r")
            print(msg)
        print_status_line()
        time.sleep(0.12)
    sys.stdout.write("\r" + " " * 120 + "\r")
    sys.stdout.flush()

# --- nice header ---
def nice_header(scan_from, scan_end, port_start, port_end):
    # Build banner lines
    banner = [
        Fore.MAGENTA + Style.BRIGHT + "╭──────══════════════════════════──────╮" + RESET,
        Fore.MAGENTA + Style.BRIGHT + f"│  Range: {scan_from} → {scan_end}".ljust(46),
        Fore.MAGENTA + Style.BRIGHT + f"│  Ports: {port_start} - {port_end}".ljust(46),
        Fore.MAGENTA + Style.BRIGHT +
f"╰───────═══════════════════════───────╯".ljust(46),
 Fore.RED + Style.BRIGHT + f"\n                                 - SABIR7718™" + RESET
    ]
    
    print("\n".join(banner))
    print()

# --- generate IPs ---
def ip_range(start_ip, end_ip):
    start = int(ipaddress.IPv4Address(start_ip))
    end = int(ipaddress.IPv4Address(end_ip))
    for i in range(start, end + 1):
        yield str(ipaddress.IPv4Address(i))

# --- main ---
def main():
    global total_ips, scanned_ips, stop_spinner, PORT_START, PORT_END

    # --- parse command-line args ---
    parser = argparse.ArgumentParser(description="Network Scanner")
    parser.add_argument('-i', nargs=2, metavar=('START_IP', 'END_IP'), help='IP range to scan')
    parser.add_argument('-p', nargs=2, type=int, metavar=('START_PORT', 'END_PORT'), help='Port range to scan')
    args = parser.parse_args()

    scan_from = args.i[0] if args.i else DEFAULT_SCAN_FROM
    scan_end  = args.i[1] if args.i else DEFAULT_SCAN_END
    PORT_START = args.p[0] if args.p else DEFAULT_PORT_START
    PORT_END   = args.p[1] if args.p else DEFAULT_PORT_END

    # --- network check ---
    if not check_network():
        print(f"{C_ERR}No internet/network connection detected!{RESET}")
        sys.exit(1)

    nice_header(scan_from, scan_end, PORT_START, PORT_END)
    start_time = time.time()

    start = int(ipaddress.IPv4Address(scan_from))
    end = int(ipaddress.IPv4Address(scan_end))
    total_ips = end - start + 1
    scanned_ips = 0

    t = threading.Thread(target=spinner_and_queue_thread, daemon=True)
    t.start()

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_ip = {executor.submit(scan_ip, ip): ip for ip in ip_range(scan_from, scan_end)}
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    res = future.result()
                    if res:
                        found_results.append(res)
                except Exception as e:
                    message_queue.put(f"{C_ERR}[!] Error scanning {ip}: {e}{RESET}")
    except KeyboardInterrupt:
        message_queue.put(f"\n{C_ERR}Scan interrupted by user. Showing results found so far...{RESET}")
    finally:
        stop_spinner = True
        t.join()

    end_time = time.time()
    total_time = end_time - start_time

    # --- format time nicely ---
    hours, rem = divmod(total_time, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours >= 1:
        time_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    elif minutes >= 1:
        time_str = f"{int(minutes)}m {int(seconds)}s"
    else:
        time_str = f"{seconds:.2f}s"

    print("\n" + Fore.BLUE + Style.BRIGHT + "────────── Scan complete ──────────" + RESET)
    if found_results:
        for ip, ports in found_results:
            print(f"{C_FOUND}[+] {C_IP}{ip}{RESET} -> Open Ports: {C_PORT}{ports}{RESET}")
    else:
        print(f"{Fore.YELLOW}No open ports found in the scanned range.{RESET}")
    print(f"\n{C_INFO}Total hosts with open ports: {len(found_results)}{RESET}")
    print(f"\n{C_PORT}Complete in {time_str}{RESET}\n")

if __name__ == "__main__":
    main()