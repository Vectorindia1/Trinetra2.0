#!/usr/bin/env python3
"""
Fixed Tor Bridges Configuration Script
Properly configures Tor to use bridges
"""

import os
import shutil
from datetime import datetime

def fix_bridge_config():
    """Fix the bridge configuration with proper formatting"""
    torrc_path = "/etc/tor/torrc"
    
    print("🔧 Fixing Tor bridge configuration...")
    
    # First, restore from backup if the current config is broken
    backups = [f for f in os.listdir('/etc/tor/') if f.startswith('torrc.backup.')]
    if backups:
        latest_backup = f"/etc/tor/{sorted(backups)[-1]}"
        print(f"📁 Restoring from backup: {latest_backup}")
        shutil.copy2(latest_backup, torrc_path)
    
    # Read current torrc
    with open(torrc_path, 'r') as f:
        current_config = f.read()
    
    # Remove any broken bridge configuration
    lines = current_config.split('\n')
    clean_lines = []
    
    skip_section = False
    for line in lines:
        if "# Bridge configuration added by setup_tor_bridges.py" in line:
            skip_section = True
            continue
        elif "# End bridge configuration" in line:
            skip_section = False
            continue
        elif skip_section:
            continue
        else:
            clean_lines.append(line)
    
    # Create properly formatted bridge configuration
    bridge_config = f"""
# Bridge configuration added by fix_tor_bridges.py
# Generated on {datetime.now().isoformat()}

# Enable bridges
UseBridges 1

# Use obfs4 bridges (recommended for bypassing censorship)
ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy

# Working bridge list (updated 2025)
Bridge obfs4 192.95.36.142:443 CDF2E852BF539B82BD549EB5F0E5B39E8AFEABB6 cert=BroadbandNow bkUbEdGPqw4+d0eZP9F8xtGHjCJfTqS6F0z5caMhNTZ7j2MbmFOcHWOTW0K15YSAA6U iat-mode=0
Bridge obfs4 37.218.247.217:443 74FAD13168806246602538555B5521A0383A1875 cert=BNPQR9dG+E3Qmit1KRd0dJxvQHo5UGBo1x6ySrcOUz1eV0qfBNEZxrPdmBhONrGLuUF6LQ iat-mode=0

# End bridge configuration
"""
    
    # Combine clean config with new bridge config
    final_config = '\n'.join(clean_lines) + bridge_config
    
    # Write the fixed configuration
    with open(torrc_path, 'w') as f:
        f.write(final_config)
    
    print("✅ Fixed bridge configuration written")
    
    # Verify the configuration
    print("🔍 Verifying Tor configuration...")
    os.system("tor --verify-config -f /etc/tor/torrc")
    
    return True

def restart_tor_service():
    """Restart Tor service properly"""
    print("🔄 Restarting Tor service...")
    
    # Stop the service
    os.system("sudo systemctl stop tor@default")
    
    # Wait a moment
    import time
    time.sleep(3)
    
    # Start the service
    result = os.system("sudo systemctl start tor@default")
    
    if result == 0:
        print("✅ Tor service restarted successfully")
        return True
    else:
        print("❌ Failed to restart Tor service")
        return False

def main():
    if os.geteuid() != 0:
        print("❌ This script needs to be run with sudo")
        print("Run: sudo python3 fix_tor_bridges.py")
        return
    
    print("🌉 Fixing Tor Bridge Configuration")
    print("=" * 40)
    
    # Fix the configuration
    if fix_bridge_config():
        # Restart Tor
        if restart_tor_service():
            print("\n🎉 Tor bridges configured successfully!")
            print("💡 Wait 1-2 minutes for Tor to bootstrap, then test your crawler")
        else:
            print("\n⚠️ Configuration fixed but service restart failed")
            print("Try manually: sudo systemctl restart tor@default")
    else:
        print("\n❌ Failed to fix configuration")

if __name__ == "__main__":
    main()
