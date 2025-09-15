import json
import os
import platform
import sys
import hashlib
import uuid
import socket
import datetime
from pathlib import Path


def load_version_from_config():
    """
    Load version from config.json in the current working directory
    
    Returns:
        str or None: Version string or None if not found
    """
    config_path = Path.cwd() / 'config.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return str(config.get('version')) if config.get('version') else None
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return None


def save_version_to_config(version):
    """
    Save version to config.json in the current working directory
    
    Args:
        version (str): Version to save
    
    Returns:
        bool: Success status
    """
    config_path = Path.cwd() / 'config.json'
    config = {}
    
    try:
        # Try to read existing config
        with open(config_path, 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Config doesn't exist or is invalid, we'll create a new one
        pass
    
    config['version'] = version
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save version to config: {e}")
        return False


def get_system_info():
    """
    Get system information
    
    Returns:
        dict: System profile
    """
    profile = {
        'diag_version': '1.2',
        'os_platform': sys.platform,
        'python_version': sys.version,
        'os_architecture': platform.machine(),
        'runtime_ver': f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }
    
    try:
        profile['os_release'] = platform.release()
    except Exception:
        profile['os_release'] = 'unknown'
    
    return profile


def get_system_component():
    """
    Get a persistent, unique system identifier

    Returns:
        str: Consistent system identifier (MAC address or deterministic hash)
    """
    # First, check if we have a stored system component
    stored_component = _load_stored_system_component()
    if stored_component:
        return stored_component

    # Try to get MAC address using uuid
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                      for elements in range(0, 8*6, 8)][::-1])
        if mac != '00:00:00:00:00:00':
            component = mac.replace(':', '').upper()
            _store_system_component(component)
            return component
    except Exception:
        pass

    # Deterministic fallback using system-specific data
    component = _generate_deterministic_component()
    _store_system_component(component)
    return component


def _load_stored_system_component():
    """Load stored system component from file"""
    try:
        component_file = Path.home() / '.spamir_updater_component'
        if component_file.exists():
            with open(component_file, 'r') as f:
                component = f.read().strip()
                if component and len(component) >= 12:  # Validate minimum length
                    return component
    except Exception:
        pass
    return None


def _store_system_component(component):
    """Store system component to file"""
    try:
        component_file = Path.home() / '.spamir_updater_component'
        with open(component_file, 'w') as f:
            f.write(component)
    except Exception:
        pass  # Silently fail if we can't store


def _generate_deterministic_component():
    """Generate a deterministic system component using system-specific data"""
    try:
        # Gather system-specific but consistent data
        import getpass

        components = [
            platform.node() or 'unknown',  # hostname
            getpass.getuser() or 'unknown',  # username
            platform.machine() or 'unknown',  # architecture
            str(Path.home()),  # home directory path
        ]

        # Create a deterministic hash
        combined_data = '|'.join(components)
        hash_obj = hashlib.sha256(combined_data.encode('utf-8'))
        return hash_obj.hexdigest()[:16].upper()  # 16 characters like MAC

    except Exception:
        # Last resort: use a fixed but unique-enough identifier
        return hashlib.md5(b'spamir_updater_fallback').hexdigest()[:16].upper()


def generate_instance_signature(auth_token):
    """
    Generate a unique instance signature
    
    Args:
        auth_token (str): Shared authentication token
    
    Returns:
        str: UUID v5 based on system component and auth token
    """
    system_component = get_system_component()
    id_material = system_component + auth_token
    
    # Using OID namespace for UUID v5
    OID_NAMESPACE = uuid.UUID('6ba7b812-9dad-11d1-80b4-00c04fd430c8')
    return str(uuid.uuid5(OID_NAMESPACE, id_material))


def log_to_file(message, level='INFO'):
    """
    Simple logging function (can be enhanced later)
    
    Args:
        message (str): Message to log
        level (str): Log level (INFO, WARNING, ERROR, etc.)
    """
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] [{level}] {message}")