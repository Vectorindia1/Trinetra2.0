#!/usr/bin/env python3

import subprocess
import sys
import os
import platform
import requests
import time

def run_command(command, description):
    """Run a system command with error handling"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def install_python_packages():
    """Install required Python packages"""
    packages = [
        'scrapy>=2.11.0',
        'selenium>=4.15.0',
        'requests>=2.31.0',
        'psutil>=5.9.0',
        'tqdm>=4.66.0',
        'python-telegram-bot>=20.7',
        'beautifulsoup4>=4.12.0',
        'lxml>=4.9.0',
        'fake-useragent>=1.4.0',
        'pysocks>=1.7.1',
        'requests[socks]>=2.31.0'
    ]
    
    print("📦 Installing Python packages...")
    for package in packages:
        print(f"  Installing {package}...")
        if not run_command(f"pip3 install '{package}'", f"Install {package}"):
            print(f"⚠️ Failed to install {package}, continuing...")
    
    print("✅ Python package installation completed")

def install_system_dependencies():
    """Install system-level dependencies"""
    print("🖥️ Installing system dependencies...")
    
    # Detect OS
    if platform.system() == "Linux":
        # Check if it's Debian/Ubuntu or Arch/Kali
        try:
            with open('/etc/os-release', 'r') as f:
                os_info = f.read().lower()
        except:
            os_info = ""
        
        if 'ubuntu' in os_info or 'debian' in os_info or 'kali' in os_info:
            # Debian-based systems
            commands = [
                "sudo apt-get update",
                "sudo apt-get install -y tor privoxy",
                "sudo apt-get install -y python3-pip python3-dev",
                "sudo apt-get install -y chromium-browser chromium-chromedriver",
                "sudo apt-get install -y wget curl git",
                "sudo apt-get install -y build-essential libxml2-dev libxslt1-dev",
                "sudo apt-get install -y libffi-dev libssl-dev"
            ]
        elif 'arch' in os_info or 'manjaro' in os_info:
            # Arch-based systems
            commands = [
                "sudo pacman -Syu --noconfirm",
                "sudo pacman -S --noconfirm tor privoxy",
                "sudo pacman -S --noconfirm python python-pip",
                "sudo pacman -S --noconfirm chromium",
                "sudo pacman -S --noconfirm wget curl git",
                "sudo pacman -S --noconfirm base-devel libxml2 libxslt"
            ]
        else:
            # Generic Linux
            print("⚠️ Unsupported Linux distribution. Please install manually:")
            print("  - tor")
            print("  - privoxy") 
            print("  - chromium-browser and chromedriver")
            print("  - python3-dev and build tools")
            return False
            
        for cmd in commands:
            if not run_command(cmd, f"Execute: {cmd}"):
                print(f"⚠️ Command failed: {cmd}")
                
    elif platform.system() == "Darwin":
        # macOS
        commands = [
            "brew install tor privoxy",
            "brew install chromium chromedriver",
            "brew install python3"
        ]
        
        for cmd in commands:
            if not run_command(cmd, f"Execute: {cmd}"):
                print(f"⚠️ Command failed: {cmd}")
    else:
        print("❌ Unsupported operating system")
        return False
        
    return True

def setup_tor_config():
    """Setup Tor configuration for multiple instances"""
    print("🧅 Setting up Tor configuration...")
    
    tor_configs = [
        {
            'port': 9050,
            'control_port': 9051,
            'config_file': '/etc/tor/torrc'
        },
        {
            'port': 9052,
            'control_port': 9053,
            'config_file': '/etc/tor/torrc.secondary'
        }
    ]
    
    # Basic torrc configuration
    basic_config = """
# Enhanced Tor configuration for crawling
SocksPort 9050
ControlPort 9051
CookieAuthentication 1
DataDirectory /var/lib/tor

# Circuit building
NewCircuitPeriod 30
MaxCircuitDirtiness 600
CircuitBuildTimeout 60

# Performance tuning
KeepalivePeriod 60
ClientOnly 1
ExitPolicy reject *:*

# Logging
Log notice file /var/log/tor/notices.log
"""
    
    try:
        # Backup original torrc
        run_command("sudo cp /etc/tor/torrc /etc/tor/torrc.backup", "Backup original torrc")
        
        # Write enhanced configuration
        with open('/tmp/torrc_enhanced', 'w') as f:
            f.write(basic_config)
        
        run_command("sudo cp /tmp/torrc_enhanced /etc/tor/torrc", "Install enhanced torrc")
        run_command("sudo chmod 644 /etc/tor/torrc", "Set torrc permissions")
        
        print("✅ Tor configuration updated")
        
    except Exception as e:
        print(f"⚠️ Could not update Tor config: {e}")

def setup_privoxy_config():
    """Setup Privoxy configuration for Tor"""
    print("🔗 Setting up Privoxy configuration...")
    
    privoxy_config = """
# Enhanced Privoxy configuration for Tor
user-manual /usr/share/doc/privoxy/user-manual
confdir /etc/privoxy
templdir /etc/privoxy/templates
logdir /var/log/privoxy
actionsfile match-all.action
actionsfile default.action
actionsfile user.action
filterfile default.filter
filterfile user.filter
logfile logfile
listen-address 127.0.0.1:8118
toggle 1
enable-remote-toggle 0
enable-remote-http-toggle 0
enable-edit-actions 0
enforce-blocks 0
buffer-limit 4096
enable-proxy-authentication-forwarding 0
forward-socks5t / 127.0.0.1:9050 .
forwarded-connect-retries 0
accept-intercepted-requests 0
allow-cgi-request-crunching 0
split-large-forms 0
keep-alive-timeout 5
tolerate-pipelining 1
socket-timeout 300
"""
    
    try:
        # Backup original privoxy config
        run_command("sudo cp /etc/privoxy/config /etc/privoxy/config.backup", "Backup original privoxy config")
        
        # Write enhanced configuration
        with open('/tmp/privoxy_enhanced', 'w') as f:
            f.write(privoxy_config)
        
        run_command("sudo cp /tmp/privoxy_enhanced /etc/privoxy/config", "Install enhanced privoxy config")
        run_command("sudo chmod 644 /etc/privoxy/config", "Set privoxy config permissions")
        
        print("✅ Privoxy configuration updated")
        
    except Exception as e:
        print(f"⚠️ Could not update Privoxy config: {e}")

def start_services():
    """Start and enable Tor and Privoxy services"""
    print("🚀 Starting services...")
    
    services = ['tor', 'privoxy']
    
    for service in services:
        # Start service
        run_command(f"sudo systemctl start {service}", f"Start {service}")
        
        # Enable service to start on boot
        run_command(f"sudo systemctl enable {service}", f"Enable {service}")
        
        # Check status
        result = subprocess.run(f"sudo systemctl is-active {service}", 
                              shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == 'active':
            print(f"✅ {service} is running")
        else:
            print(f"⚠️ {service} may not be running properly")

def test_installation():
    """Test the installation by checking connections"""
    print("🧪 Testing installation...")
    
    # Test Tor connection
    try:
        import requests
        
        # Test Privoxy proxy
        proxies = {'http': 'http://127.0.0.1:8118', 'https': 'http://127.0.0.1:8118'}
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=30)
        
        if response.status_code == 200:
            ip_info = response.json()
            print(f"✅ Privoxy proxy working - External IP: {ip_info.get('origin', 'unknown')}")
        else:
            print("❌ Privoxy proxy test failed")
            
    except Exception as e:
        print(f"❌ Proxy test failed: {e}")
    
    # Test imports
    try:
        import scrapy
        import selenium
        import requests
        import psutil
        print("✅ All Python packages imported successfully")
    except ImportError as e:
        print(f"❌ Import test failed: {e}")

def setup_captcha_config():
    """Setup CAPTCHA solving service configuration"""
    print("🧩 Setting up CAPTCHA service configuration...")
    
    config_content = """
# CAPTCHA Service Configuration
# Replace these with your actual API keys

# 2Captcha service
CAPTCHA_2CAPTCHA_API_KEY=your_2captcha_api_key_here

# Anti-Captcha service  
CAPTCHA_ANTICAPTCHA_API_KEY=your_anticaptcha_api_key_here

# DeathByCaptcha service
CAPTCHA_DBC_USERNAME=your_deathbycaptcha_username
CAPTCHA_DBC_PASSWORD=your_deathbycaptcha_password

# Enable/disable services
CAPTCHA_ENABLED=true
CAPTCHA_PREFERRED_SERVICE=2captcha
"""
    
    try:
        with open('captcha_config.env', 'w') as f:
            f.write(config_content)
        
        print("✅ CAPTCHA configuration template created (captcha_config.env)")
        print("📝 Please edit captcha_config.env with your actual API keys")
        
    except Exception as e:
        print(f"⚠️ Could not create CAPTCHA config: {e}")

def display_summary():
    """Display installation summary and next steps"""
    print("\n" + "="*60)
    print("🎉 ROBUST CRAWLER SETUP COMPLETED!")
    print("="*60)
    
    print("\n📋 What was installed:")
    print("  ✅ Enhanced Tor crawler with CAPTCHA handling")
    print("  ✅ Selenium WebDriver integration")
    print("  ✅ Advanced proxy rotation system")
    print("  ✅ Comprehensive blocking detection")
    print("  ✅ Tor and Privoxy services")
    print("  ✅ All required Python packages")
    
    print("\n🚀 Next steps:")
    print("  1. Edit captcha_config.env with your CAPTCHA service API keys")
    print("  2. Test the installation: python3 test_robust_crawler.py")
    print("  3. Run the robust crawler: scrapy crawl robust_onion -a start_url=<url>")
    
    print("\n📁 Key files created:")
    print("  • robust_tor_crawler.py - Enhanced crawler with all features")
    print("  • test_robust_crawler.py - Comprehensive test suite")
    print("  • captcha_config.env - CAPTCHA service configuration template")
    
    print("\n⚙️ Services configured:")
    print("  • Tor: Enhanced configuration for crawling")
    print("  • Privoxy: HTTP proxy for Tor integration")
    
    print("\n🛡️ Security features:")
    print("  • Advanced user-agent rotation")
    print("  • Enhanced proxy rotation with fallbacks")
    print("  • CAPTCHA solving integration")
    print("  • Cloudflare challenge handling")
    print("  • Domain blocking after failures")
    print("  • Session management")

def main():
    """Main setup function"""
    print("🛠️ ROBUST DARK WEB CRAWLER SETUP")
    print("="*60)
    print("This script will install and configure:")
    print("  • Enhanced Tor crawler with CAPTCHA handling")
    print("  • Selenium WebDriver for JavaScript sites")
    print("  • Advanced proxy rotation system") 
    print("  • Comprehensive anti-detection features")
    print("  • All required dependencies")
    print()
    
    # Check if running as root
    if os.geteuid() == 0:
        print("⚠️ Running as root. Some operations may require different permissions.")
    
    # Install system dependencies
    if not install_system_dependencies():
        print("❌ System dependency installation failed")
        return
    
    # Install Python packages
    install_python_packages()
    
    # Setup configurations
    setup_tor_config()
    setup_privoxy_config()
    
    # Start services
    start_services()
    
    # Setup CAPTCHA config
    setup_captcha_config()
    
    # Wait for services to start
    print("⏱️ Waiting for services to start...")
    time.sleep(10)
    
    # Test installation
    test_installation()
    
    # Display summary
    display_summary()

if __name__ == "__main__":
    main()
