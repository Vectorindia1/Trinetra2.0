#!/usr/bin/env python3
"""
Simple Working Bridge Configuration
Uses basic bridge format that's known to work
"""

import os
import shutil
from datetime import datetime

def create_simple_bridge_config():
    """Create a simple, working bridge configuration"""
    torrc_path = "/etc/tor/torrc"
    
    print("🔧 Creating simple bridge configuration...")
    
    # Restore from backup first
    backups = [f for f in os.listdir('/etc/tor/') if f.startswith('torrc.backup.')]
    if backups:
        latest_backup = f"/etc/tor/{sorted(backups)[-1]}"
        print(f"📁 Restoring from backup: {latest_backup}")
        shutil.copy2(latest_backup, torrc_path)
    
    # Read current torrc
    with open(torrc_path, 'r') as f:
        current_config = f.read()
    
    # Simple bridge configuration that works
    bridge_config = """
# Simple Bridge Configuration
UseBridges 1

# Use basic bridges (no obfs4 to avoid complexity)
Bridge 192.95.36.142:443
Bridge 37.218.247.217:443

# End bridge configuration
"""
    
    # Append to existing config
    final_config = current_config + bridge_config
    
    # Write the configuration
    with open(torrc_path, 'w') as f:
        f.write(final_config)
    
    print("✅ Simple bridge configuration written")
    
    # Verify the configuration
    print("🔍 Verifying configuration...")
    result = os.system("tor --verify-config -f /etc/tor/torrc 2>&1")
    
    return result == 0

def main():
    if os.geteuid() != 0:
        print("❌ This script needs to be run with sudo")
        print("Run: sudo python3 simple_bridge_config.py")
        return
    
    print("🌉 Simple Tor Bridge Setup")
    print("=" * 30)
    
    if create_simple_bridge_config():
        print("✅ Configuration verified successfully")
        
        # Restart Tor
        print("🔄 Restarting Tor...")
        result = os.system("sudo systemctl restart tor@default")
        
        if result == 0:
            print("✅ Tor restarted successfully with bridges!")
            print("\n💡 Next steps:")
            print("1. Wait 1-2 minutes for Tor to connect through bridges")
            print("2. Test with: python3 quick_onion_test.py")
            print("3. If successful, try your crawler with a valid .onion URL")
        else:
            print("❌ Failed to restart Tor")
    else:
        print("❌ Configuration verification failed")

if __name__ == "__main__":
    main()
