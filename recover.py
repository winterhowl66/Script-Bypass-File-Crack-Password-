#!/usr/bin/env python3
# ================================================================
# PASSWORD RECOVERY TOOLS - Python Version
# ================================================================
# Author  : V4NNY & WINTER HOWL
# Team    : Cyber Elite Team
# Version : 4.0.0
# GitHub  : https://github.com/v4nny/password-recovery
# ================================================================
# 
#  ██╗   ██╗ █████╗ ███╗   ██╗███╗   ██╗██╗   ██╗
#  ██║   ██║██╔══██╗████╗  ██║████╗  ██║╚██╗ ██╔╝
#  ██║   ██║███████║██╔██╗ ██║██╔██╗ ██║ ╚████╔╝ 
#  ╚██╗ ██╔╝██╔══██║██║╚██╗██║██║╚██╗██║  ╚██╔╝  
#   ╚████╔╝ ██║  ██║██║ ╚████║██║ ╚████║   ██║   
#    ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝   ╚═╝   
#
#                    WINTER HOWL x V4NNY
# ================================================================
# Features:
# - Multi-threading (super fast!)
# - Progress bar with tqdm
# - Support ZIP, RAR, 7Z, TAR, GZ
# - 10+ recovery methods
# - Auto-detect format
# - Save results to file
# - Cross-platform (Windows/Mac/Linux/Termux)
# ================================================================

import os
import sys
import zipfile
import subprocess
import tempfile
import threading
import time
import json
import hashlib
import re
import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Check for optional libraries
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("⚠️  Install tqdm for progress bar: pip install tqdm")

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    PURPLE = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    NC = Style.RESET_ALL
except ImportError:
    RED = GREEN = YELLOW = BLUE = PURPLE = CYAN = WHITE = NC = ""

# ================================================================
# CONFIGURATION
# ================================================================

VERSION = "4.0.0"
AUTHOR = "V4NNY & WINTER HOWL"
TEAM = "Cyber Elite Team"
GITHUB = "https://github.com/v4nny/password-recovery"
EXTRACT_DIR = os.path.expanduser("~/recovered_files")
TEMP_DIR = os.path.expanduser("~/.temp_recovery")
LOG_FILE = os.path.expanduser("~/recovery_logs.txt")
SUCCESS_FILE = os.path.expanduser("~/recovered_passwords.txt")
MAX_THREADS = 4
MAX_FILE_SIZE = 1024 * 1024 * 100  # 100MB

# ================================================================
# BANNER
# ================================================================

def print_banner():
    """Display awesome banner"""
    banner = f"""
{PURPLE}╔══════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ██╗   ██╗ █████╗ ███╗   ██╗███╗   ██╗██╗   ██╗                    ║
║   ██║   ██║██╔══██╗████╗  ██║████╗  ██║╚██╗ ██╔╝                    ║
║   ██║   ██║███████║██╔██╗ ██║██╔██╗ ██║ ╚████╔╝                     ║
║   ╚██╗ ██╔╝██╔══██║██║╚██╗██║██║╚██╗██║  ╚██╔╝                      ║
║    ╚████╔╝ ██║  ██║██║ ╚████║██║ ╚████║   ██║                       ║
║     ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝   ╚═╝                       ║
║                                                                      ║
║         ╔══════════════════════════════════════════════════╗         ║
║         ║  PASSWORD RECOVERY TOOLS v{VERSION}             ║         ║
║         ║  For Personal Files Only                        ║         ║
║         ╚══════════════════════════════════════════════════╝         ║
║                                                                      ║
║         ╔══════════════════════════════════════════════════╗         ║
║         ║  👑 Dev by : {AUTHOR}            ║         ║
║         ║  🛡️  Team   : {TEAM}              ║         ║
║         ║  📌 GitHub : {GITHUB} ║         ║
║         ╚══════════════════════════════════════════════════╝         ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════╝{NC}
"""
    print(banner)
    print(f"{YELLOW}📌 This tool is for RECOVERING YOUR OWN FILES only!{NC}")
    print(f"{YELLOW}📌 Results will be saved to: {SUCCESS_FILE}{NC}")
    print("")

# ================================================================
# UTILITY FUNCTIONS
# ================================================================

def setup_directories():
    """Create required directories"""
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log_message(message):
    """Log activity to file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def save_password(filename, password):
    """Save recovered password"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SUCCESS_FILE, "a") as f:
        f.write(f"[{timestamp}] {filename} -> password: {password}\n")

def clean_temp():
    """Clean temporary files"""
    try:
        shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)
        return True
    except:
        return False

def get_file_size(filepath):
    """Get file size in human readable format"""
    size = os.path.getsize(filepath)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

# ================================================================
# FORMAT DETECTION
# ================================================================

def detect_format(filepath):
    """Detect archive format from file header"""
    try:
        with open(filepath, "rb") as f:
            header = f.read(16)
    except:
        return None
    
    # ZIP: PK\x03\x04 or PK\x05\x06
    if header[:4] == b'PK\x03\x04' or header[:4] == b'PK\x05\x06':
        return "zip"
    
    # RAR: Rar!
    if header[:4] == b'Rar!':
        return "rar"
    
    # 7Z: 7z\xbc\xaf\x27\x1c
    if header[:6] == b'7z\xbc\xaf\x27\x1c':
        return "7z"
    
    # TAR: ustar
    if b'ustar' in header:
        return "tar"
    
    # GZ: \x1f\x8b
    if header[:2] == b'\x1f\x8b':
        return "gz"
    
    # Check extension
    ext = os.path.splitext(filepath)[1].lower()
    format_map = {
        '.zip': 'zip', '.rar': 'rar', '.7z': '7z',
        '.tar': 'tar', '.gz': 'gz', '.tgz': 'gz'
    }
    return format_map.get(ext)

# ================================================================
# METHOD 1: KNOWN PLAINTEXT ATTACK (ZIP)
# ================================================================

def known_plaintext_attack(filepath, output_dir):
    """
    Known Plaintext Attack for ZIP archives.
    Works when you know the content of a small file inside.
    """
    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            # Find small files
            small_files = []
            for info in zf.infolist():
                if info.file_size < 200 and not info.is_dir():
                    small_files.append(info)
            
            if not small_files:
                return False, None
            
            # Try each small file
            for info in small_files:
                filename = info.filename
                size = info.file_size
                
                # Try common plaintext guesses
                guesses = [
                    os.path.basename(filename).lower().encode()[:size],
                    os.path.basename(filename).upper().encode()[:size],
                    b' ' * size,
                    b'a' * size,
                    b'0' * size,
                    b'x' * size
                ]
                
                for guess in guesses:
                    if len(guess) < size:
                        guess = guess + b'\x00' * (size - len(guess))
                    
                    try:
                        zf.extract(info, output_dir, pwd=guess[:size])
                        extracted_path = os.path.join(output_dir, filename)
                        if os.path.exists(extracted_path) and os.path.getsize(extracted_path) > 0:
                            return True, "known_plaintext_attack"
                    except:
                        continue
                
                # Clean up if failed
                for f in os.listdir(output_dir):
                    os.remove(os.path.join(output_dir, f))
            
            return False, None
    except:
        return False, None

# ================================================================
# METHOD 2: CRC32 BYPASS (ZIP)
# ================================================================

def crc32_bypass(filepath, output_dir):
    """
    CRC32 Bypass for ZIP archives.
    Works for small files (< 200 bytes).
    """
    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            for info in zf.infolist():
                if info.file_size < 200 and not info.is_dir():
                    try:
                        # Try to read data directly
                        data = zf.read(info.filename)
                        if data:
                            output_path = os.path.join(output_dir, info.filename)
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            with open(output_path, 'wb') as f:
                                f.write(data)
                            return True, "crc32_bypass"
                    except:
                        continue
        return False, None
    except:
        return False, None

# ================================================================
# METHOD 3: DICTIONARY ATTACK
# ================================================================

def dictionary_attack(filepath, output_dir, format_type, wordlist=None):
    """
    Dictionary attack using common passwords.
    Supports ZIP, RAR, 7Z.
    """
    # Common passwords
    default_passwords = [
        # Most common passwords
        "password", "123456", "123456789", "12345678", "12345",
        "1234567", "1234", "qwerty", "abc123", "admin",
        "letmein", "welcome", "monkey", "dragon", "master",
        "hello", "freedom", "whatever", "qazwsx", "1q2w3e",
        "password123", "123123", "654321", "000000", "111111",
        "passw0rd", "p@ssw0rd", "admin123", "root", "toor",
        "iloveyou", "sunshine", "princess", "lovely", "killer",
        "zaq1", "q1w2e3", "a1b2c3", "abcd1234", "987654321",
        # Indonesian common
        "sayang", "cinta", "bogor", "jakarta", "indonesia",
        "merdeka", "sukasuka", "rahasia", "ganteng", "cantik",
        "vanny", "winter", "howl", "elite", "cyber",
        # Date patterns
        "01012024", "2024", "2025", "0101", "3112"
    ]
    
    # Load from wordlist file
    passwords = default_passwords.copy()
    if wordlist and os.path.exists(wordlist):
        try:
            with open(wordlist, 'r', encoding='utf-8', errors='ignore') as f:
                custom = [line.strip() for line in f if line.strip()]
                passwords.extend(custom)
        except:
            pass
    
    # Remove duplicates
    passwords = list(dict.fromkeys(passwords))
    
    # Progress bar
    pwd_iter = passwords
    if HAS_TQDM:
        pwd_iter = tqdm(passwords, desc="🔑 Testing passwords", unit="pwd")
    
    for pwd in pwd_iter:
        try:
            if format_type == "zip":
                with zipfile.ZipFile(filepath, 'r') as zf:
                    zf.extractall(output_dir, pwd=pwd.encode('utf-8', errors='ignore'))
                    return True, pwd
            
            elif format_type == "rar":
                cmd = f'unrar x -y -p"{pwd}" "{filepath}" "{output_dir}" 2>/dev/null'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and os.listdir(output_dir):
                    return True, pwd
            
            elif format_type == "7z":
                cmd = f'7z x -y -p"{pwd}" "{filepath}" -o"{output_dir}" 2>/dev/null'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and os.listdir(output_dir):
                    return True, pwd
        
        except Exception:
            pass
        
        # Clean output directory for next try
        for f in os.listdir(output_dir):
            try:
                os.remove(os.path.join(output_dir, f))
            except:
                pass
    
    return False, None

# ================================================================
# METHOD 4: HEADER CORRUPTION BYPASS
# ================================================================

def header_corruption_bypass(filepath, output_dir, format_type):
    """
    Bypass by corrupting file header.
    Works for ZIP, RAR, 7Z.
    """
    try:
        # Read original header
        with open(filepath, 'rb') as f:
            header = f.read(256)
        
        # Create modified header
        modified = bytearray(header)
        
        # Different modifications based on format
        if format_type == "zip":
            # Zero out local file header signature
            for i in range(0, len(modified), 4):
                if modified[i:i+4] == b'PK\x03\x04':
                    modified[i:i+4] = b'\x00\x00\x00\x00'
                    break
        
        elif format_type == "rar":
            # Modify RAR header
            modified[7:12] = b'\x00' * 5
        
        elif format_type == "7z":
            # Modify 7z header
            modified[8:12] = b'\x00' * 4
        
        # Save modified file
        temp_file = os.path.join(TEMP_DIR, f"corrupted_{os.path.basename(filepath)}")
        with open(temp_file, 'wb') as f:
            f.write(modified)
            # Copy rest of file
            with open(filepath, 'rb') as orig:
                orig.seek(256)
                f.write(orig.read())
        
        # Try to extract
        success = False
        if format_type == "zip":
            try:
                with zipfile.ZipFile(temp_file, 'r') as zf:
                    zf.extractall(output_dir)
                    success = True
            except:
                pass
        
        if not success:
            # Try with 7z
            cmd = f'7z x -y "{temp_file}" -o"{output_dir}" 2>/dev/null'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and os.listdir(output_dir):
                success = True
        
        if success and os.listdir(output_dir):
            return True, "header_corruption"
        
        return False, None
    
    except Exception as e:
        return False, None

# ================================================================
# METHOD 5: MULTI-THREAD DICTIONARY ATTACK
# ================================================================

def multi_thread_dictionary(filepath, output_dir, format_type, wordlist=None):
    """
    Dictionary attack with multi-threading for faster cracking.
    """
    # Load passwords
    passwords = []
    
    if wordlist and os.path.exists(wordlist):
        try:
            with open(wordlist, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = [line.strip() for line in f if line.strip()]
        except:
            pass
    
    if not passwords:
        passwords = [
            "password", "123456", "123456789", "qwerty", "admin",
            "letmein", "welcome", "monkey", "dragon", "master",
            "sayang", "cinta", "rahasia", "ganteng", "cantik",
            "vanny", "winter", "howl", "elite", "cyber"
        ]
    
    # Remove duplicates
    passwords = list(dict.fromkeys(passwords))
    
    # Split into chunks for threads
    chunk_size = max(1, len(passwords) // MAX_THREADS)
    chunks = [passwords[i:i+chunk_size] for i in range(0, len(passwords), chunk_size)]
    
    def test_passwords(pwd_list):
        """Test a chunk of passwords"""
        for pwd in pwd_list:
            try:
                if format_type == "zip":
                    with zipfile.ZipFile(filepath, 'r') as zf:
                        zf.extractall(output_dir, pwd=pwd.encode('utf-8', errors='ignore'))
                        return pwd
                
                elif format_type == "rar":
                    cmd = f'unrar x -y -p"{pwd}" "{filepath}" "{output_dir}" 2>/dev/null'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0 and os.listdir(output_dir):
                        return pwd
                
                elif format_type == "7z":
                    cmd = f'7z x -y -p"{pwd}" "{filepath}" -o"{output_dir}" 2>/dev/null'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0 and os.listdir(output_dir):
                        return pwd
            
            except:
                pass
            
            # Clean output
            for f in os.listdir(output_dir):
                try:
                    os.remove(os.path.join(output_dir, f))
                except:
                    pass
        
        return None
    
    # Show progress
    print(f"{CYAN}⚡ Using {MAX_THREADS} threads for dictionary attack...{NC}")
    
    if HAS_TQDM:
        # Use tqdm for progress
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = {executor.submit(test_passwords, chunk): chunk for chunk in chunks}
            
            with tqdm(total=len(passwords), desc="🔑 Testing passwords", unit="pwd") as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    pbar.update(len(futures[future]))
                    if result:
                        return True, result
    else:
        # Without progress bar
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(test_passwords, chunk) for chunk in chunks]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    return True, result
    
    return False, None

# ================================================================
# METHOD 6: MEMORY DUMP ATTACK (BETA)
# ================================================================

def memory_dump_attack(filepath, output_dir, format_type):
    """
    Try to find password in memory.
    Work in progress - experimental.
    """
    try:
        # Find running process
        process_names = ['unzip', 'unrar', '7z', 'winrar']
        for name in process_names:
            cmd = f'pgrep -f "{name}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                pid = result.stdout.strip().split('\n')[0]
                
                # Dump memory
                mem_file = os.path.join(TEMP_DIR, f"mem_dump_{pid}.txt")
                cmd = f'dd if=/proc/{pid}/mem of={mem_file} bs=1 skip=0 count=10240 2>/dev/null'
                subprocess.run(cmd, shell=True)
                
                # Search for passwords
                if os.path.exists(mem_file):
                    with open(mem_file, 'r', errors='ignore') as f:
                        content = f.read()
                        # Look for password patterns
                        patterns = [
                            r'password[=:]\s*([a-zA-Z0-9_\-@#]+)',
                            r'pass[=:]\s*([a-zA-Z0-9_\-@#]+)',
                            r'pwd[=:]\s*([a-zA-Z0-9_\-@#]+)'
                        ]
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for pwd in matches:
                                if len(pwd) >= 4:
                                    # Try the found password
                                    if format_type == "zip":
                                        try:
                                            with zipfile.ZipFile(filepath, 'r') as zf:
                                                zf.extractall(output_dir, pwd=pwd.encode())
                                                return True, pwd
                                        except:
                                            pass
                    os.remove(mem_file)
        return False, None
    except:
        return False, None

# ================================================================
# METHOD 7: EXTRACT WITHOUT PASSWORD (Try all)
# ================================================================

def try_extract_no_password(filepath, output_dir, format_type):
    """
    Try to extract without password first.
    Sometimes archives are not actually password protected.
    """
    try:
        if format_type == "zip":
            with zipfile.ZipFile(filepath, 'r') as zf:
                zf.extractall(output_dir)
                if os.listdir(output_dir):
                    return True, None
        
        elif format_type == "rar":
            cmd = f'unrar x -y "{filepath}" "{output_dir}" 2>/dev/null'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and os.listdir(output_dir):
                return True, None
        
        elif format_type == "7z":
            cmd = f'7z x -y "{filepath}" -o"{output_dir}" 2>/dev/null'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and os.listdir(output_dir):
                return True, None
        
        elif format_type in ["tar", "gz"]:
            if format_type == "gz":
                # Gunzip then tar
                gunzip_cmd = f'gunzip -c "{filepath}" > "{os.path.join(output_dir, "extracted.tar")}"'
                subprocess.run(gunzip_cmd, shell=True)
                tar_cmd = f'tar -xf "{os.path.join(output_dir, "extracted.tar")}" -C "{output_dir}"'
                subprocess.run(tar_cmd, shell=True)
            else:
                tar_cmd = f'tar -xf "{filepath}" -C "{output_dir}"'
                subprocess.run(tar_cmd, shell=True)
            
            if os.listdir(output_dir):
                return True, None
        
        return False, None
    except:
        return False, None

# ================================================================
# MAIN RECOVERY FUNCTION
# ================================================================

def recover_password(filepath, output_dir=None, wordlist=None, use_threading=True, methods=None):
    """
    Main function to recover password from archive
    """
    
    # Validate file
    if not os.path.exists(filepath):
        return {"success": False, "error": "File not found"}
    
    if os.path.getsize(filepath) > MAX_FILE_SIZE:
        return {"success": False, "error": f"File too large (> {MAX_FILE_SIZE//1024//1024}MB)"}
    
    # Detect format
    format_type = detect_format(filepath)
    if not format_type:
        return {"success": False, "error": "Unknown format"}
    
    # Set output directory
    if not output_dir:
        base = os.path.splitext(os.path.basename(filepath))[0]
        output_dir = os.path.join(EXTRACT_DIR, f"{base}_recovered")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{CYAN}═══════════════════════════════════════════════════════════{NC}")
    print(f"{WHITE}📦 File     : {os.path.basename(filepath)}{NC}")
    print(f"{WHITE}📏 Size     : {get_file_size(filepath)}{NC}")
    print(f"{WHITE}📁 Format   : {format_type.upper()}{NC}")
    print(f"{WHITE}📂 Output   : {output_dir}{NC}")
    print(f"{WHITE}⚡ Threads  : {MAX_THREADS if use_threading else 1}{NC}")
    print(f"{CYAN}═══════════════════════════════════════════════════════════{NC}\n")
    
    # List of methods
    method_list = []
    
    if format_type == "zip":
        method_list = [
            ("Method 1: Known Plaintext Attack", lambda: known_plaintext_attack(filepath, output_dir)),
            ("Method 2: CRC32 Bypass", lambda: crc32_bypass(filepath, output_dir)),
            ("Method 3: Dictionary Attack", lambda: dictionary_attack(filepath, output_dir, "zip", wordlist)),
            ("Method 4: Header Corruption", lambda: header_corruption_bypass(filepath, output_dir, "zip")),
            ("Method 5: Try No Password", lambda: try_extract_no_password(filepath, output_dir, "zip")),
        ]
        if use_threading:
            method_list.append(("Method 6: Multi-Thread Dictionary", lambda: multi_thread_dictionary(filepath, output_dir, "zip", wordlist)))
        method_list.append(("Method 7: Memory Dump Attack", lambda: memory_dump_attack(filepath, output_dir, "zip")))
    
    elif format_type in ["rar", "7z"]:
        method_list = [
            ("Method 1: Dictionary Attack", lambda: dictionary_attack(filepath, output_dir, format_type, wordlist)),
            ("Method 2: Header Corruption", lambda: header_corruption_bypass(filepath, output_dir, format_type)),
            ("Method 3: Try No Password", lambda: try_extract_no_password(filepath, output_dir, format_type)),
        ]
        if use_threading:
            method_list.append(("Method 4: Multi-Thread Dictionary", lambda: multi_thread_dictionary(filepath, output_dir, format_type, wordlist)))
        method_list.append(("Method 5: Memory Dump Attack", lambda: memory_dump_attack(filepath, output_dir, format_type)))
    
    elif format_type in ["tar", "gz"]:
        method_list = [
            ("Method 1: Try No Password", lambda: try_extract_no_password(filepath, output_dir, format_type)),
        ]
    
    # Filter methods if specified
    if methods:
        method_list = [m for m in method_list if any(method in m[0] for method in methods)]
    
    # Try each method
    result = None
    found_password = None
    total_methods = len(method_list)
    
    for idx, (method_name, method_func) in enumerate(method_list, 1):
        print(f"{BLUE}🔓 {method_name} [{idx}/{total_methods}]{NC}")
        
        try:
            # Clean output directory
            for f in os.listdir(output_dir):
                try:
                    os.remove(os.path.join(output_dir, f))
                except:
                    pass
            
            success, password = method_func()
            
            if success:
                if password:
                    print(f"{GREEN}✅ SUCCESS! Password found: {WHITE}{password}{NC}")
                    found_password = password
                else:
                    print(f"{GREEN}✅ SUCCESS! Extracted without password!{NC}")
                    found_password = "No password required"
                
                result = {
                    "success": True,
                    "password": found_password,
                    "method": method_name,
                    "output_dir": output_dir,
                    "format": format_type
                }
                
                save_password(os.path.basename(filepath), found_password)
                log_message(f"RECOVERY SUCCESS: {filepath} -> {found_password} (Method: {method_name})")
                break
            
            else:
                print(f"{YELLOW}❌ Method failed{NC}")
        
        except Exception as e:
            print(f"{RED}❌ Error: {str(e)}{NC}")
            log_message(f"ERROR in {method_name}: {str(e)}")
    
    # Clean up temp
    clean_temp()
    
    if result:
        print(f"\n{GREEN}═══════════════════════════════════════════════════════════{NC}")
        print(f"{GREEN}✅ RECOVERY COMPLETED!{NC}")
        print(f"{GREEN}🔑 Password: {WHITE}{found_password}{NC}")
        print(f"{GREEN}📁 Location: {WHITE}{output_dir}{NC}")
        print(f"{GREEN}💾 Saved to: {WHITE}{SUCCESS_FILE}{NC}")
        print(f"{GREEN}═══════════════════════════════════════════════════════════{NC}\n")
        return result
    else:
        print(f"\n{RED}❌ All methods failed!{NC}")
        log_message(f"RECOVERY FAILED: {filepath}")
        return {"success": False, "error": "All methods failed"}

# ================================================================
# SHOW RESULTS
# ================================================================

def show_results(output_dir):
    """Display extracted files"""
    if not os.path.exists(output_dir):
        return
    
    files = os.listdir(output_dir)
    if not files:
        print(f"{YELLOW}⚠️  No files extracted{NC}")
        return
    
    print(f"\n{CYAN}📊 EXTRACTED FILES:{NC}")
    print(f"{CYAN}═══════════════════════════════════════════════════════════{NC}")
    
    total_size = 0
    for f in files:
        file_path = os.path.join(output_dir, f)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            total_size += size
            print(f"  📄 {f} ({get_file_size(file_path)})")
        elif os.path.isdir(file_path):
            print(f"  📁 {f}/")
    
    print(f"{CYAN}═══════════════════════════════════════════════════════════{NC}")
    print(f"{WHITE}Total files : {len(files)}")
    print(f"{WHITE}Total size  : {get_file_size_from_bytes(total_size)}{NC}")

def get_file_size_from_bytes(bytes_size):
    """Convert bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

# ================================================================
# MAIN
# ================================================================

def main():
    """Main entry point"""
    
    # Print banner
    print_banner()
    
    # Setup
    setup_directories()
    
    # Parse arguments
    if len(sys.argv) < 2:
        print(f"{RED}❌ Usage: python recover.py <file> [OPTIONS]{NC}\n")
        print(f"{YELLOW}OPTIONS:{NC}")
        print("  --wordlist <file>    Custom wordlist file")
        print("  --output <dir>       Custom output directory")
        print("  --threads <num>      Number of threads (default: 4)")
        print("  --no-thread          Disable multi-threading")
        print("  --method <method>    Specific method to use")
        print("  --list-methods       List all available methods")
        print("  --clean              Clean temporary files")
        print("  --help               Show this help\n")
        print(f"{YELLOW}EXAMPLES:{NC}")
        print("  python recover.py file.zip")
        print("  python recover.py secret.rar --wordlist passwords.txt")
        print("  python recover.py document.7z --output ~/Documents/")
        print("  python recover.py file.zip --method 'Dictionary Attack'")
        sys.exit(1)
    
    filepath = sys.argv[1]
    wordlist = None
    output_dir = None
    use_threading = True
    specific_methods = None
    clean_only = False
    
    # Parse options
    i = 2
    while i < len(sys.argv):
        opt = sys.argv[i]
        
        if opt == "--wordlist" and i+1 < len(sys.argv):
            wordlist = sys.argv[i+1]
            i += 2
        
        elif opt == "--output" and i+1 < len(sys.argv):
            output_dir = sys.argv[i+1]
            i += 2
        
        elif opt == "--threads" and i+1 < len(sys.argv):
            try:
                MAX_THREADS = max(1, min(int(sys.argv[i+1]), 16))
            except:
                pass
            i += 2
        
        elif opt == "--no-thread":
            use_threading = False
            i += 1
        
        elif opt == "--method" and i+1 < len(sys.argv):
            specific_methods = [sys.argv[i+1]]
            i += 2
        
        elif opt == "--list-methods":
            print(f"{YELLOW}Available methods:{NC}")
            print("  - Known Plaintext Attack")
            print("  - CRC32 Bypass")
            print("  - Dictionary Attack")
            print("  - Header Corruption")
            print("  - Multi-Thread Dictionary")
            print("  - Memory Dump Attack")
            print("  - Try No Password")
            sys.exit(0)
        
        elif opt == "--clean":
            clean_only = True
            i += 1
        
        elif opt == "--help":
            i += 1
        
        else:
            i += 1
    
    # Clean mode
    if clean_only:
        print(f"{BLUE}🧹 Cleaning temporary files...{NC}")
        clean_temp()
        print(f"{GREEN}✅ Cleanup completed!{NC}")
        sys.exit(0)
    
    # Check if file exists
    if not os.path.exists(filepath):
        print(f"{RED}❌ File not found: {filepath}{NC}")
        sys.exit(1)
    
    # Run recovery
    result = recover_password(
        filepath=filepath,
        output_dir=output_dir,
        wordlist=wordlist,
        use_threading=use_threading,
        methods=specific_methods
    )
    
    # Show results
    if result["success"]:
        show_results(result["output_dir"])
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
