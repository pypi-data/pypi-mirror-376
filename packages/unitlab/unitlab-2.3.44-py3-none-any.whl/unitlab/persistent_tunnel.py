#!/usr/bin/env python3
"""
Persistent Tunnel - Each device gets deviceid.unitlab-ai.com
Uses Cloudflare API to create named tunnels
"""

import subprocess
import requests
import json
import time
import os
import base64
from fastapi import FastAPI
import uvicorn
import threading
import psutil
import secrets

api = FastAPI()

@api.get("/api-agent/")
def get_cpu_info():
    cpu_usage_percent = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    return  {"cpu_percentage": cpu_usage_percent, 'cpu_count': psutil.cpu_count(), 'ram_usage': ram.used }


class PersistentTunnel:
    def __init__(self, device_id=None):
        """Initialize with device ID"""
        
        # Cloudflare credentials (hardcoded for simplicity)
        
        self.cf_api_key = "RoIAn1t9rMqcGK7_Xja216pxbRTyFafC1jeRKIO3"  

        self.cf_account_id = "29df28cf48a30be3b1aa344b840400e6"  # Your account ID
        self.cf_zone_id = "eae80a730730b3b218a80dace996535a"  # Zone ID for unitlab-ai.com
        
        # Clean device ID for subdomain
        if device_id:
            self.device_id = device_id.replace('-', '').replace('_', '').replace('.', '').lower()[:20]
        else:
            import uuid
            self.device_id = str(uuid.uuid4())[:8]
        
        # Main tunnel for Jupyter/API
        self.main_tunnel_name = "agent-{}".format(self.device_id)
        self.main_tunnel_id = None
        self.main_tunnel_process = None
        self.main_tunnel_credentials = None
        
        # SSH tunnel
        self.ssh_tunnel_name = "ssh-{}".format(self.device_id)
        self.ssh_tunnel_id = None
        self.ssh_tunnel_process = None
        self.ssh_tunnel_credentials = None
        
        # URLs
        self.subdomain = self.device_id
        self.domain = "unitlab-ai.com"
        self.jupyter_url = "https://{}.{}".format(self.subdomain, self.domain)
        self.api_expose_url = "https://{}.{}/api-agent/".format(self.subdomain, self.domain)
        self.ssh_subdomain = "ssh{}".format(self.device_id)
        self.ssh_url = "{}.{}".format(self.ssh_subdomain, self.domain)

        self.jupyter_process = None
    
    @property
    def tunnel_process(self):
        """Compatibility property for backward compatibility"""
        return self.main_tunnel_process
    
    def _get_headers(self):
        """Get API headers for Global API Key"""
     
    
        return { 
            "Authorization":  f"Bearer {self.cf_api_key}",                                                                                                                                                         
            "Content-Type": "application/json"                                                                                          
        } 
    
    # def get_or_create_tunnel(self):
    #     """Always create a new tunnel with unique name to avoid conflicts"""
    #     # Generate unique tunnel name to avoid conflicts
    #     import uuid
    #     unique_suffix = str(uuid.uuid4())[:8]
    #     self.tunnel_name = "agent-{}-{}".format(self.device_id, unique_suffix)
    #     print("🔧 Creating tunnel: {}...".format(self.tunnel_name))
        
    #     # Always create new tunnel
    #     return self.create_new_tunnel()


    def create_main_tunnel(self):
        """Create main tunnel for Jupyter/API"""
        print("🔧 Creating main tunnel: {}...".format(self.main_tunnel_name))
        
        # Generate random tunnel secret (32 bytes)
        tunnel_secret = base64.b64encode(secrets.token_bytes(32)).decode()
        
        url = "https://api.cloudflare.com/client/v4/accounts/{}/cfd_tunnel".format(self.cf_account_id)
        headers = self._get_headers()
        
        data = {
            "name": self.main_tunnel_name,
            "tunnel_secret": tunnel_secret
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            result = response.json()["result"]
            self.main_tunnel_id = result["id"]
            
            # Create credentials JSON
            self.main_tunnel_credentials = {
                "AccountTag": self.cf_account_id,
                "TunnelSecret": tunnel_secret,
                "TunnelID": self.main_tunnel_id
            }
            
            # Save credentials to file
            cred_file = "/tmp/tunnel-{}.json".format(self.main_tunnel_name)
            with open(cred_file, 'w') as f:
                json.dump(self.main_tunnel_credentials, f)
            
            print("✅ Main tunnel created: {}".format(self.main_tunnel_id))
            print("✅ Credentials saved to: {}".format(cred_file))
            return cred_file
        else:
            print("❌ Failed to create main tunnel: {}".format(response.text))
            return None
    
    def create_ssh_tunnel(self):
        """Create SSH tunnel"""
        print("🔧 Creating SSH tunnel: {}...".format(self.ssh_tunnel_name))
        
        # Generate random tunnel secret (32 bytes)
        tunnel_secret = base64.b64encode(secrets.token_bytes(32)).decode()
        
        url = "https://api.cloudflare.com/client/v4/accounts/{}/cfd_tunnel".format(self.cf_account_id)
        headers = self._get_headers()
        
        data = {
            "name": self.ssh_tunnel_name,
            "tunnel_secret": tunnel_secret
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            result = response.json()["result"]
            self.ssh_tunnel_id = result["id"]
            
            # Create credentials JSON
            self.ssh_tunnel_credentials = {
                "AccountTag": self.cf_account_id,
                "TunnelSecret": tunnel_secret,
                "TunnelID": self.ssh_tunnel_id
            }
            
            # Save credentials to file
            cred_file = "/tmp/tunnel-{}.json".format(self.ssh_tunnel_name)
            with open(cred_file, 'w') as f:
                json.dump(self.ssh_tunnel_credentials, f)
            
            print("✅ SSH tunnel created: {}".format(self.ssh_tunnel_id))
            print("✅ Credentials saved to: {}".format(cred_file))
            return cred_file
        else:
            print("❌ Failed to create SSH tunnel: {}".format(response.text))
            return None
    
    def create_dns_records(self):
        """Create DNS CNAME records for both tunnels"""
        if not self.main_tunnel_id or not self.ssh_tunnel_id:
            return False
        
        print("🔧 Creating DNS records...")
        
        url = "https://api.cloudflare.com/client/v4/zones/{}/dns_records".format(self.cf_zone_id)
        headers = self._get_headers()
        
        # Create main subdomain record for Jupyter and API
        data = {
            "type": "CNAME",
            "name": self.subdomain,
            "content": "{}.cfargotunnel.com".format(self.main_tunnel_id),
            "proxied": True,
            "ttl": 1
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            print("✅ Main DNS record created: {}.{}".format(self.subdomain, self.domain))
        elif "already exists" in response.text:
            print("⚠️  Main DNS record already exists: {}.{}".format(self.subdomain, self.domain))
        else:
            print("❌ Failed to create main DNS: {}".format(response.text[:200]))
            return False
        
        # Wait a moment for DNS propagation
        time.sleep(2)
        
        # Create SSH subdomain record pointing to SSH tunnel
        ssh_data = {
            "type": "CNAME",
            "name": self.ssh_subdomain,
            "content": "{}.cfargotunnel.com".format(self.ssh_tunnel_id),
            "proxied": True,
            "ttl": 1
        }
        
        print("📝 Creating SSH DNS record: {} -> {}".format(self.ssh_subdomain, self.ssh_tunnel_id))
        ssh_response = requests.post(url, headers=headers, json=ssh_data)
        
        if ssh_response.status_code in [200, 201]:
            print("✅ SSH DNS record created: {}.{}".format(self.ssh_subdomain, self.domain))
            return True
        elif "already exists" in ssh_response.text:
            print("⚠️  SSH DNS record already exists")
            return True
        else:
            print("❌ Failed to create SSH DNS: {}".format(ssh_response.text[:200]))
            return False
    
    
    def create_access_application(self):
        """Create Cloudflare Access application for SSH with bypass policy"""
        print("🔧 Creating Access application for SSH...")
        
        # Create Access application
        app_url = "https://api.cloudflare.com/client/v4/zones/{}/access/apps".format(self.cf_zone_id)
        headers = self._get_headers()
        
        app_data = {
            "name": "SSH-{}".format(self.device_id),
            "domain": "{}.{}".format(self.ssh_subdomain, self.domain),
            "type": "ssh",
            "session_duration": "24h",
            "auto_redirect_to_identity": False
        }
        
        app_response = requests.post(app_url, headers=headers, json=app_data)
        
        if app_response.status_code in [200, 201]:
            app_id = app_response.json()["result"]["id"]
            print("✅ Access application created: {}".format(app_id))
            
            # Create bypass policy (no authentication required)
            policy_url = "https://api.cloudflare.com/client/v4/zones/{}/access/apps/{}/policies".format(
                self.cf_zone_id, app_id
            )
            
            policy_data = {
                "name": "Public Access",
                "decision": "bypass",
                "include": [
                    {"everyone": {}}
                ],
                "precedence": 1
            }
            
            policy_response = requests.post(policy_url, headers=headers, json=policy_data)
            
            
            if policy_response.status_code in [200, 201]:
                print("✅ Bypass policy created - SSH is publicly accessible")
                return True
            else:
                print("⚠️  Could not create bypass policy: {}".format(policy_response.text[:200]))
                return False
        elif "already exists" in app_response.text:
            print("⚠️  Access application already exists")
            return True
        else:
            print("⚠️  Could not create Access application: {}".format(app_response.text[:200]))
            return False
    
    def create_main_tunnel_config(self, cred_file):
        """Create main tunnel config file for Jupyter/API"""
        config_file = "/tmp/tunnel-config-{}.yml".format(self.main_tunnel_name)
        with open(config_file, 'w') as f:
            f.write("tunnel: {}\n".format(self.main_tunnel_id))
            f.write("credentials-file: {}\n\n".format(cred_file))
            f.write("ingress:\n")

            # API (more specific path goes first)
            f.write("  - hostname: {}.{}\n".format(self.subdomain, self.domain))
            f.write("    path: /api-agent\n")
            f.write("    service: http://localhost:8001\n")

            # Jupyter (general hostname for HTTP)
            f.write("  - hostname: {}.{}\n".format(self.subdomain, self.domain))
            f.write("    service: http://localhost:8888\n")

            # Catch-all 404 (MUST be last!)
            f.write("  - service: http_status:404\n")
        
        print("✅ Main tunnel config created: {}".format(config_file))
        return config_file
    
    def create_ssh_tunnel_config(self, cred_file):
        """Create SSH tunnel config file"""
        config_file = "/tmp/tunnel-config-{}.yml".format(self.ssh_tunnel_name)
        with open(config_file, 'w') as f:
            f.write("tunnel: {}\n".format(self.ssh_tunnel_id))
            f.write("credentials-file: {}\n\n".format(cred_file))
            f.write("ingress:\n")

            # SSH service
            f.write("  - hostname: {}.{}\n".format(self.ssh_subdomain, self.domain))
            f.write("    service: ssh://localhost:22\n")

            # Catch-all 404 (MUST be last!)
            f.write("  - service: http_status:404\n")
        
        print("✅ SSH tunnel config created: {}".format(config_file))
        return config_file 

    
    def get_cloudflared_path(self):
        """Get or download cloudflared for any platform"""
        import shutil
        import platform
        
        # Check if already in system PATH
        if shutil.which("cloudflared"):
            return "cloudflared"
        
        # Determine binary location based on OS
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "windows":
            local_bin = os.path.expanduser("~/cloudflared/cloudflared.exe")
        else:
            local_bin = os.path.expanduser("~/.local/bin/cloudflared")
        
        # Check if already downloaded
        if os.path.exists(local_bin):
            return local_bin
        
        # Download based on platform
        print("📦 Downloading cloudflared for {}...".format(system))
        
        if system == "linux":
            # Linux: detect architecture
            if "arm" in machine or "aarch64" in machine:
                arch = "arm64"
            elif "386" in machine or "i686" in machine:
                arch = "386"
            else:
                arch = "amd64"
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{}".format(arch)
            
            os.makedirs(os.path.dirname(local_bin), exist_ok=True)
            subprocess.run("curl -L {} -o {}".format(url, local_bin), shell=True, capture_output=True)
            subprocess.run("chmod +x {}".format(local_bin), shell=True)
            
        elif system == "darwin":
            # macOS: supports both Intel and Apple Silicon
            if "arm" in machine:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
            else:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
            
            os.makedirs(os.path.dirname(local_bin), exist_ok=True)
            # Download and extract tar.gz
            subprocess.run("curl -L {} | tar xz -C {}".format(url, os.path.dirname(local_bin)), shell=True, capture_output=True)
            subprocess.run("chmod +x {}".format(local_bin), shell=True)
            
        elif system == "windows":
            # Windows: typically amd64
            if "arm" in machine:
                arch = "arm64"
            elif "386" in machine:
                arch = "386"
            else:
                arch = "amd64"
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-{}.exe".format(arch)
            
            os.makedirs(os.path.dirname(local_bin), exist_ok=True)
            # Use PowerShell on Windows to download
            subprocess.run("powershell -Command \"Invoke-WebRequest -Uri {} -OutFile {}\"".format(url, local_bin), shell=True, capture_output=True)
        
        else:
            print("❌ Unsupported platform: {}".format(system))
            raise Exception("Platform {} not supported".format(system))
        
        print("✅ cloudflared downloaded successfully")
        return local_bin
        
    def start_jupyter(self):
        """Start Jupyter"""
        print("🚀 Starting Jupyter...")
        
        cmd = [
            "jupyter", "notebook",
            "--port", "8888",
            "--no-browser",
            "--ip", "0.0.0.0",
            "--NotebookApp.token=''",
            "--NotebookApp.password=''",
            "--NotebookApp.allow_origin='*'"
        ]
        
        self.jupyter_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        time.sleep(3)
        print("✅ Jupyter started")
        return True
    
    def start_api(self):
        def run_api():
            uvicorn.run(
                api,
                port=8001
            )
        
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        print('✅ API started')

    def start_main_tunnel(self, config_file):
        """Start main tunnel for Jupyter/API"""
        print("🔧 Starting main tunnel...")
        
        cloudflared = self.get_cloudflared_path()
        
        cmd = [
            cloudflared,
            "tunnel",
            "--config", config_file,
            "run"
        ]
        
        self.main_tunnel_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        time.sleep(2)
        
        # Check if process is still running
        if self.main_tunnel_process.poll() is not None:
            print("❌ Main tunnel process died!")
            # Try to read error output
            try:
                stdout, stderr = self.main_tunnel_process.communicate(timeout=1)
                if stderr:
                    print(f"Error: {stderr.decode()}")
                if stdout:
                    print(f"Output: {stdout.decode()}")
            except:
                pass
            return False
        
        print("✅ Main tunnel running at {}".format(self.jupyter_url))
        print("✅ API running at {}".format(self.api_expose_url))
        return True
    
    def start_ssh_tunnel(self, config_file):
        """Start SSH tunnel"""
        print("🔧 Starting SSH tunnel...")
        
        cloudflared = self.get_cloudflared_path()
        
        cmd = [
            cloudflared,
            "tunnel",
            "--config", config_file,
            "run"
        ]
        
        self.ssh_tunnel_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        time.sleep(2)
        
        # Check if process is still running
        if self.ssh_tunnel_process.poll() is not None:
            print("❌ SSH tunnel process died!")
            # Try to read error output
            try:
                stdout, stderr = self.ssh_tunnel_process.communicate(timeout=1)
                if stderr:
                    print(f"Error: {stderr.decode()}")
                if stdout:
                    print(f"Output: {stdout.decode()}")
            except:
                pass
            return False
        
        print("✅ SSH tunnel running at {}".format(self.ssh_url))
        return True        
    
    def start(self):
        """Main entry point"""
        try:
            print("="*50)
            print("🌐 Persistent Tunnel with Separate SSH")
            print("Device: {}".format(self.device_id))
            print("Main: {}.{}".format(self.subdomain, self.domain))
            print("SSH: {}.{}".format(self.ssh_subdomain, self.domain))
            print("="*50)
            
            # 1. Create main tunnel for Jupyter/API
            main_cred_file = self.create_main_tunnel()
            if not main_cred_file:
                print("❌ Failed to create main tunnel")
                return False
            
            # 2. Create SSH tunnel
            ssh_cred_file = self.create_ssh_tunnel()
            if not ssh_cred_file:
                print("❌ Failed to create SSH tunnel")
                return False
            
            # 3. Create DNS records for both tunnels
            self.create_dns_records()
            
            # 4. Create Access application for SSH
            self.create_access_application()
            
            # 5. Create config files
            main_config_file = self.create_main_tunnel_config(main_cred_file)
            ssh_config_file = self.create_ssh_tunnel_config(ssh_cred_file)
            
            # 6. Start services (Jupyter and API)
            self.start_jupyter()
            self.start_api()
            
            # 7. Start both tunnels
            if not self.start_main_tunnel(main_config_file):
                return False
            
            if not self.start_ssh_tunnel(ssh_config_file):
                return False
            
            print("\n" + "="*50)
            print("🎉 SUCCESS! All services running:")
            print("📔 Jupyter:   {}".format(self.jupyter_url))
            print("🔧 API:       {}".format(self.api_expose_url))
            print("🔐 SSH:       {}".format(self.ssh_url))
            print("")
            print("SSH Connection Command:")
            import getpass
            current_user = getpass.getuser()
            print("ssh -o ProxyCommand='cloudflared access ssh --hostname {}' {}@{}".format(
                self.ssh_url, current_user, self.ssh_url))
            print("")
            print("Main Tunnel ID: {}".format(self.main_tunnel_id))
            print("SSH Tunnel ID: {}".format(self.ssh_tunnel_id))
            print("="*50)
  
            
            return True
            
        except Exception as e:
            print("❌ Error: {}".format(e))
            import traceback
            traceback.print_exc()
            self.stop()
            return False
    

    
    def stop(self):
        """Stop everything"""
        if self.jupyter_process:
            self.jupyter_process.terminate()
            try:
                self.jupyter_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.jupyter_process.kill()
                self.jupyter_process.wait()
            print("✅ Jupyter stopped")
        
        if self.main_tunnel_process:
            self.main_tunnel_process.terminate()
            try:
                self.main_tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.main_tunnel_process.kill()
                self.main_tunnel_process.wait()
            print("✅ Main tunnel stopped")
        
        if self.ssh_tunnel_process:
            self.ssh_tunnel_process.terminate()
            try:
                self.ssh_tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ssh_tunnel_process.kill()
                self.ssh_tunnel_process.wait()
            print("✅ SSH tunnel stopped")
        
    #     # Optionally delete tunnel when stopping
    #     if self.tunnel_id:
    #         try:
    #             url = "https://api.cloudflare.com/client/v4/accounts/{}/cfd_tunnel/{}".format(
    #                 self.cf_account_id, self.tunnel_id
    #             )
    #             requests.delete(url, headers=self._get_headers())
    #             print("🗑️  Tunnel deleted")
    #         except Exception:
    #             pass  # Ignore cleanup errors
    
    def run(self):
        """Run and keep alive"""
        try:
            if self.start():
                print("\nPress Ctrl+C to stop...")
                while True:
                    time.sleep(1)
                    # Check if processes are still running
                    if self.main_tunnel_process and self.main_tunnel_process.poll() is not None:
                        print("❌ Main tunnel process died!")
                        break
                    if self.ssh_tunnel_process and self.ssh_tunnel_process.poll() is not None:
                        print("❌ SSH tunnel process died!")
                        break
        except KeyboardInterrupt:
            print("\n⏹️  Shutting down...")
            self.stop()


def main():
    import platform
    import uuid
    
    hostname = platform.node().replace('.', '-')[:20]
    device_id = "{}-{}".format(hostname, str(uuid.uuid4())[:8])
    
    print("Device ID: {}".format(device_id))
    
    tunnel = PersistentTunnel(device_id=device_id)
    tunnel.run()


if __name__ == "__main__":
    main()