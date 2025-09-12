#!/usr/bin/env python3
"""
FalconCore Security Agent - Cross-Platform System Tray Version
Enterprise cybersecurity threat intelligence agent with system tray integration
Monitors system logs, network activity, and security events
Runs as a background system tray application with menu interface
"""

__version__ = "2.1.0"

import os
import sys
import json
import time
import socket
import subprocess
import requests
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import psutil
import platform

# Try to import packaging for version comparison, fallback to simple comparison
try:
    from packaging import version
    PACKAGING_AVAILABLE = True
except ImportError:
    PACKAGING_AVAILABLE = False
    print("⚠️  packaging library not found - using simple version comparison")

# Jaeger Tracing Imports (optional for local development)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    OPENTELEMETRY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  OpenTelemetry/Jaeger not available: {e}")
    print("   Agent will run without distributed tracing")
    OPENTELEMETRY_AVAILABLE = False
    
    # Create minimal trace module for compatibility
    class NoOpTracer:
        def start_as_current_span(self, name):
            return NoOpSpan()
    
    class NoOpSpan:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def set_attribute(self, key, value):
            pass
        def add_event(self, name, attributes=None):
            pass
        def record_exception(self, exception):
            pass
        def set_status(self, status):
            pass
    
    class NoOpTrace:
        def NoOpTracer(self):
            return NoOpTracer()
        def Status(self, code, message=None):
            return None
        StatusCode = type('StatusCode', (), {'ERROR': 'ERROR', 'OK': 'OK'})
    
    trace = NoOpTrace()

try:
    import rumps
    RUMPS_AVAILABLE = True
except ImportError:
    RUMPS_AVAILABLE = False

try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

class FalconCoreAgent:
    def __init__(self, config_file="falconcore-agent.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.agent_id = self.config.get('agent_id')
        self.api_key = self.config.get('api_key')
        self.server_url = self.config.get('server_url', 'http://localhost:5000')
        self.scan_interval = self.config.get('scan_interval', 300)  # 5 minutes
        self.running = False
        
        # System information
        self.os_type = platform.system().lower()
        self.os_version = platform.release()
        self.os_arch = platform.machine()
        self.hostname = socket.gethostname()
        self.mac_address = self.get_mac_address()
        
        # Security monitoring data
        self.file_hashes = {}
        self.known_processes = set()
        self.network_connections = []
        self.last_scan_time = None
        self.threat_count = 0
        self.status = "Initializing..."
        
        # System tray state
        self.is_scanning = False
        self.alerts = []
        self.scan_logs = []  # Detailed scan logs for analysis
        self.false_positive_count = 0
        self.legitimate_threat_count = 0
        
        # DLP (Data Loss Prevention)
        self.dlp_config = {}
        self.dlp_rules = []
        self.dlp_enabled = False
        self.last_dlp_config_update = None
        
        # File Quarantine System
        self.quarantine_dir = os.path.expanduser("~/FalconCore/Quarantine")
        self.quarantine_metadata_file = os.path.expanduser("~/FalconCore/quarantine_metadata.json")
        self.quarantined_files = {}  # Cache of quarantined file metadata
        self.setup_quarantine_directory()
        
        # Update Management
        self.current_version = __version__
        self.update_check_interval = 3600  # Check every hour
        self.last_update_check = None
        self.update_available = False
        self.latest_version = None
        
        # Initialize Jaeger Tracing
        self.setup_jaeger_tracing()
        
        print(f"🦅 FalconCore Agent v{self.current_version} - System Tray Edition")
        print(f"🖥️  OS: {self.os_type} {self.os_version} ({self.os_arch})")
        print(f"🏠 Host: {self.hostname}")
        if OPENTELEMETRY_AVAILABLE:
            print(f"📊 Jaeger tracing enabled")
        else:
            print(f"📊 Running in basic mode (no tracing)")
        print(f"🔄 Auto-update system enabled")

    def setup_jaeger_tracing(self):
        """Initialize Jaeger distributed tracing"""
        if not OPENTELEMETRY_AVAILABLE:
            print("⚠️  Skipping Jaeger tracing - OpenTelemetry not available")
            self.tracer = NoOpTracer()
            return
            
        try:
            # Configure resource with service information
            resource = Resource.create({
                "service.name": "falconcore-agent",
                "service.version": "2.1.0",
                "deployment.environment": "production",
                "host.name": self.hostname,
                "host.arch": self.os_arch,
                "os.type": self.os_type,
                "os.version": self.os_version,
                "agent.id": getattr(self, 'agent_id', 'unknown')
            })

            # Set up the tracer provider
            trace.set_tracer_provider(TracerProvider(resource=resource))
            tracer_provider = trace.get_tracer_provider()

            # Configure Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name="localhost",
                agent_port=6831,
                collector_endpoint="http://localhost:14268/api/traces",
            )

            # Create and configure span processor
            span_processor = BatchSpanProcessor(jaeger_exporter)
            tracer_provider.add_span_processor(span_processor)

            # Get tracer instance
            self.tracer = trace.get_tracer(__name__)
            
            # Instrument HTTP requests automatically
            RequestsInstrumentor().instrument()
            
            print("✅ Jaeger tracing configured successfully")
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to initialize Jaeger tracing: {e}")
            print("   Continuing without distributed tracing")
            # Create a no-op tracer if Jaeger fails
            self.tracer = NoOpTracer()

    def check_for_updates(self):
        """Check PyPI for new agent versions"""
        with self.tracer.start_as_current_span("check_for_updates") as span:
            try:
                span.set_attribute("update.current_version", self.current_version)
                
                # Check if enough time has passed since last check
                if self.last_update_check:
                    time_since_check = time.time() - self.last_update_check
                    if time_since_check < self.update_check_interval:
                        span.add_event("update_check_skipped", {"time_remaining": self.update_check_interval - time_since_check})
                        return False
                
                print("🔄 Checking for agent updates...")
                
                # Query PyPI for package information
                response = requests.get(
                    "https://pypi.org/pypi/falconcore-agent/json",
                    timeout=10
                )
                
                if response.status_code == 200:
                    package_info = response.json()
                    latest_version = package_info['info']['version']
                    self.latest_version = latest_version
                    
                    span.set_attribute("update.latest_version", latest_version)
                    span.set_attribute("update.pypi_status", "success")
                    
                    # Compare versions
                    if self._compare_versions(latest_version, self.current_version):
                        self.update_available = True
                        print(f"🆕 Update available: v{self.current_version} → v{latest_version}")
                        span.add_event("update_available", {
                            "current": self.current_version,
                            "latest": latest_version
                        })
                        return True
                    else:
                        print(f"✅ Agent is up to date (v{self.current_version})")
                        span.add_event("up_to_date")
                        self.update_available = False
                        return False
                else:
                    print(f"⚠️  Failed to check for updates: HTTP {response.status_code}")
                    span.set_attribute("update.pypi_status", "failed")
                    span.set_status(trace.Status(trace.StatusCode.ERROR, f"HTTP {response.status_code}"))
                    return False
                    
            except Exception as e:
                print(f"❌ Update check error: {e}")
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return False
            finally:
                self.last_update_check = time.time()

    def install_update(self):
        """Install the latest version using pip"""
        with self.tracer.start_as_current_span("install_update") as span:
            try:
                if not self.update_available or not self.latest_version:
                    print("⚠️  No update available")
                    span.add_event("no_update_available")
                    return False
                
                print(f"📦 Installing update v{self.latest_version}...")
                span.set_attribute("update.target_version", self.latest_version)
                span.add_event("update_started")
                
                # Use pip to upgrade the package
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "--upgrade", "falconcore-agent"
                ], capture_output=True, text=True, timeout=300)
                
                span.set_attribute("update.exit_code", result.returncode)
                
                if result.returncode == 0:
                    print(f"✅ Successfully updated to v{self.latest_version}")
                    print("🔄 Agent will restart to apply update...")
                    span.add_event("update_successful")
                    
                    # Schedule restart after brief delay
                    threading.Timer(5.0, self.restart_agent).start()
                    return True
                else:
                    print(f"❌ Update failed: {result.stderr}")
                    span.add_event("update_failed", {"error": result.stderr})
                    span.set_status(trace.Status(trace.StatusCode.ERROR, result.stderr))
                    return False
                    
            except subprocess.TimeoutExpired:
                print("❌ Update timed out after 5 minutes")
                span.add_event("update_timeout")
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Update timeout"))
                return False
            except Exception as e:
                print(f"❌ Update installation error: {e}")
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return False

    def _compare_versions(self, latest, current):
        """Compare version strings with or without packaging library"""
        try:
            if PACKAGING_AVAILABLE:
                return version.parse(latest) > version.parse(current)
            else:
                # Simple version comparison for basic semantic versioning
                latest_parts = [int(x) for x in latest.split('.')]
                current_parts = [int(x) for x in current.split('.')]
                
                # Pad shorter version with zeros
                max_len = max(len(latest_parts), len(current_parts))
                latest_parts.extend([0] * (max_len - len(latest_parts)))
                current_parts.extend([0] * (max_len - len(current_parts)))
                
                return latest_parts > current_parts
        except Exception as e:
            print(f"⚠️  Version comparison error: {e}")
            return False

    def restart_agent(self):
        """Restart the agent to apply updates"""
        try:
            print("🔄 Restarting agent...")
            # Stop current operations
            self.running = False
            
            # On Unix systems, replace current process
            if hasattr(os, 'execv'):
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                # Fallback for Windows
                subprocess.Popen([sys.executable] + sys.argv)
                sys.exit(0)
                
        except Exception as e:
            print(f"❌ Restart failed: {e}")

    def load_config(self):
        """Load agent configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return {}
        return {}
    
    def save_config(self):
        """Save agent configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_mac_address(self):
        """Get MAC address of the machine"""
        try:
            import uuid
            return ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0,48,8)][::-1])
        except:
            return "00:00:00:00:00:00"
    
    def setup_quarantine_directory(self):
        """Set up quarantine directory and load existing metadata with enhanced security"""
        try:
            # Create quarantine directory with secure permissions
            os.makedirs(self.quarantine_dir, mode=0o700, exist_ok=True)
            
            # Ensure directory has proper restrictive permissions (owner only)
            try:
                os.chmod(self.quarantine_dir, 0o700)
                print(f"🔐 Quarantine directory secured with 0o700 permissions")
            except Exception as e:
                print(f"⚠️  Warning: Could not set secure permissions on quarantine directory: {e}")
            
            # Verify directory ownership and warn if not owned by current user
            try:
                dir_stat = os.stat(self.quarantine_dir)
                current_uid = os.getuid() if hasattr(os, 'getuid') else None
                if current_uid is not None and dir_stat.st_uid != current_uid:
                    print(f"⚠️  Warning: Quarantine directory not owned by current user (uid: {current_uid} vs {dir_stat.st_uid})")
            except Exception as e:
                print(f"⚠️  Warning: Could not verify quarantine directory ownership: {e}")
            
            # Create parent directory for metadata if needed with secure permissions
            metadata_parent = os.path.dirname(self.quarantine_metadata_file)
            os.makedirs(metadata_parent, mode=0o700, exist_ok=True)
            
            # Secure the metadata file location
            try:
                os.chmod(metadata_parent, 0o700)
            except Exception as e:
                print(f"⚠️  Warning: Could not secure metadata directory: {e}")
            
            # Load existing quarantine metadata
            self.load_quarantine_metadata()
            
            # Verify integrity of existing quarantined files
            self.verify_quarantine_integrity()
            
            print(f"🔒 Quarantine system initialized: {self.quarantine_dir}")
            print(f"📋 Quarantine metadata: {len(self.quarantined_files)} files tracked")
            
            # Create a quarantine manifest for integrity checking
            self.create_quarantine_manifest()
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to initialize quarantine system: {e}")
            print("   Quarantine functionality will be disabled")
            
    def verify_quarantine_integrity(self):
        """Verify the integrity of existing quarantined files"""
        if not self.quarantined_files:
            return
            
        print(f"🔍 Verifying integrity of {len(self.quarantined_files)} quarantined files...")
        
        corrupted_files = []
        missing_files = []
        
        for file_id, metadata in self.quarantined_files.items():
            quarantine_path = metadata.get('quarantine_path')
            if not quarantine_path:
                continue
                
            try:
                if not os.path.exists(quarantine_path):
                    missing_files.append(file_id)
                    print(f"⚠️  Missing quarantined file: {quarantine_path}")
                    continue
                
                # Check file size matches metadata
                current_size = os.path.getsize(quarantine_path)
                original_metadata = metadata.get('original_metadata', {})
                expected_size = original_metadata.get('size', metadata.get('file_size', 0))
                
                if current_size != expected_size:
                    corrupted_files.append(file_id)
                    print(f"⚠️  Size mismatch for quarantined file: {quarantine_path}")
                    print(f"     Expected: {expected_size} bytes, Found: {current_size} bytes")
                
                # Verify file permissions are secure
                file_stat = os.stat(quarantine_path)
                if file_stat.st_mode & 0o077:  # Check if group/other have any permissions
                    print(f"⚠️  Insecure permissions on quarantined file: {quarantine_path}")
                    try:
                        os.chmod(quarantine_path, 0o600)
                        print(f"   Fixed permissions for: {quarantine_path}")
                    except Exception as e:
                        print(f"   Could not fix permissions: {e}")
                        
            except Exception as e:
                print(f"⚠️  Error verifying quarantined file {quarantine_path}: {e}")
                corrupted_files.append(file_id)
        
        # Report integrity status
        if missing_files or corrupted_files:
            print(f"⚠️  Quarantine integrity issues found:")
            if missing_files:
                print(f"   Missing files: {len(missing_files)}")
            if corrupted_files:
                print(f"   Corrupted files: {len(corrupted_files)}")
        else:
            print(f"✅ All quarantined files verified successfully")
    
    def create_quarantine_manifest(self):
        """Create a manifest file for quarantine integrity checking"""
        try:
            manifest_path = os.path.join(self.quarantine_dir, "quarantine_manifest.json")
            
            manifest = {
                'created_at': datetime.now().isoformat(),
                'agent_id': self.agent_id,
                'hostname': self.hostname,
                'total_files': len(self.quarantined_files),
                'integrity_verification': {
                    'last_verified': datetime.now().isoformat(),
                    'status': 'verified'
                }
            }
            
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Secure the manifest file
            os.chmod(manifest_path, 0o600)
            
        except Exception as e:
            print(f"⚠️  Warning: Could not create quarantine manifest: {e}")
    
    def load_quarantine_metadata(self):
        """Load quarantine metadata from file"""
        try:
            if os.path.exists(self.quarantine_metadata_file):
                with open(self.quarantine_metadata_file, 'r') as f:
                    self.quarantined_files = json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Failed to load quarantine metadata: {e}")
            self.quarantined_files = {}
    
    def save_quarantine_metadata(self):
        """Save quarantine metadata to file"""
        try:
            with open(self.quarantine_metadata_file, 'w') as f:
                json.dump(self.quarantined_files, f, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Failed to save quarantine metadata: {e}")
    
    def quarantine_file(self, file_path, violation_info):
        """Actually quarantine a file by moving it to the quarantine directory"""
        with self.tracer.start_as_current_span("quarantine_file") as span:
            try:
                span.set_attribute("quarantine.file_path", file_path)
                span.set_attribute("quarantine.rule_id", violation_info.get('ruleId', 'unknown'))
                
                if not os.path.exists(file_path):
                    error_msg = "File not found"
                    print(f"⚠️  File not found for quarantine: {file_path}")
                    span.add_event("quarantine_failed", {"reason": "file_not_found"})
                    span.set_status(trace.Status(trace.StatusCode.ERROR, error_msg))
                    return False, error_msg
                
                if not os.path.exists(self.quarantine_dir):
                    error_msg = "Quarantine directory not available"
                    print(f"⚠️  Quarantine directory not available: {self.quarantine_dir}")
                    span.add_event("quarantine_failed", {"reason": "quarantine_dir_unavailable"})
                    span.set_status(trace.Status(trace.StatusCode.ERROR, error_msg))
                    return False, error_msg
                
                # Capture complete file metadata BEFORE moving
                file_stat = os.stat(file_path)
                is_symlink = os.path.islink(file_path)
                is_hardlink = file_stat.st_nlink > 1
                
                # Get file ownership and permissions (cross-platform)
                file_metadata = {
                    'size': file_stat.st_size,
                    'mode': oct(file_stat.st_mode),
                    'uid': file_stat.st_uid,
                    'gid': file_stat.st_gid,
                    'ctime': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    'mtime': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'atime': datetime.fromtimestamp(file_stat.st_atime).isoformat(),
                    'is_symlink': is_symlink,
                    'is_hardlink': is_hardlink,
                    'inode': file_stat.st_ino,
                    'nlinks': file_stat.st_nlink
                }
                
                # For symlinks, also capture the target
                if is_symlink:
                    try:
                        symlink_target = os.readlink(file_path)
                        file_metadata['symlink_target'] = symlink_target
                        print(f"🔗 Symlink detected: {file_path} -> {symlink_target}")
                        span.add_event("symlink_detected", {"target": symlink_target})
                    except Exception as e:
                        file_metadata['symlink_target'] = f"Error reading target: {e}"
                        print(f"⚠️  Warning: Could not read symlink target: {e}")
                
                # Cross-platform owner information
                try:
                    import pwd
                    import grp
                    file_metadata['owner_name'] = pwd.getpwuid(file_stat.st_uid).pw_name
                    file_metadata['group_name'] = grp.getgrgid(file_stat.st_gid).gr_name
                except (ImportError, KeyError, OSError):
                    # Windows or when user/group doesn't exist
                    file_metadata['owner_name'] = f"uid:{file_stat.st_uid}"
                    file_metadata['group_name'] = f"gid:{file_stat.st_gid}"
                
                span.set_attribute("quarantine.file_size", file_metadata['size'])
                span.set_attribute("quarantine.is_symlink", is_symlink)
                span.set_attribute("quarantine.is_hardlink", is_hardlink)
                
                # Generate unique quarantine filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = os.path.basename(file_path)
                quarantine_filename = f"{timestamp}_{file_name}"
                quarantine_path = os.path.join(self.quarantine_dir, quarantine_filename)
                
                # Handle filename collisions
                counter = 1
                while os.path.exists(quarantine_path):
                    quarantine_filename = f"{timestamp}_{counter}_{file_name}"
                    quarantine_path = os.path.join(self.quarantine_dir, quarantine_filename)
                    counter += 1
                
                # Move file to quarantine (preserves metadata when possible)
                import shutil
                if is_symlink:
                    # For symlinks, copy the link itself, not the target
                    shutil.copy2(file_path, quarantine_path, follow_symlinks=False)
                    os.remove(file_path)
                else:
                    shutil.move(file_path, quarantine_path)
                
                # Set secure permissions on quarantined file (read-only)
                try:
                    os.chmod(quarantine_path, 0o600)  # Only owner can read/write
                except Exception as e:
                    print(f"⚠️  Warning: Could not set secure permissions on quarantined file: {e}")
                
                # Verify file integrity after move
                try:
                    post_move_size = os.path.getsize(quarantine_path)
                    if post_move_size != file_metadata['size']:
                        print(f"⚠️  Warning: File size mismatch after quarantine move")
                        span.add_event("integrity_warning", {"size_mismatch": True})
                except Exception as e:
                    print(f"⚠️  Warning: Could not verify quarantined file integrity: {e}")
                
                # Create comprehensive metadata entry
                quarantine_metadata = {
                    'original_path': file_path,
                    'quarantine_path': quarantine_path,
                    'quarantine_filename': quarantine_filename,
                    'quarantined_at': datetime.now().isoformat(),
                    'file_hash': violation_info.get('fileHash', 'unknown'),
                    'rule_id': violation_info.get('ruleId', 'unknown'),
                    'rule_name': violation_info.get('ruleName', 'unknown'),
                    'violation_type': violation_info.get('violationType', 'unknown'),
                    'severity': violation_info.get('severity', 'medium'),
                    'user_context': violation_info.get('userContext', 'unknown'),
                    'agent_id': self.agent_id,
                    'hostname': self.hostname,
                    # Original file metadata
                    'original_metadata': file_metadata
                }
                
                # Store metadata
                file_id = str(uuid.uuid4())
                self.quarantined_files[file_id] = quarantine_metadata
                self.save_quarantine_metadata()
                
                print(f"🔒 QUARANTINED: {file_name}")
                print(f"   Original: {file_path}")
                print(f"   Quarantine: {quarantine_path}")
                print(f"   Rule: {violation_info.get('ruleName', 'Unknown')}")
                print(f"   Original size: {file_metadata['size']} bytes")
                print(f"   Owner: {file_metadata.get('owner_name', 'unknown')}")
                if is_symlink:
                    print(f"   Symlink target: {file_metadata.get('symlink_target', 'unknown')}")
                if is_hardlink:
                    print(f"   Warning: File has {file_metadata['nlinks']} hard links")
                
                span.add_event("file_quarantined_successfully", {
                    "quarantine_path": quarantine_path,
                    "file_size": file_metadata['size']
                })
                span.set_attribute("quarantine.success", True)
                
                return True, quarantine_path
                
            except Exception as e:
                error_msg = f"Failed to quarantine file: {e}"
                print(f"❌ {error_msg}")
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return False, error_msg

    def register_agent(self):
        """Register agent with FalconCore server"""
        try:
            # The server generates its own agent_id, so we don't send one
            response = requests.post(
                f"{self.server_url}/api/agent/register",
                json={
                    'hostname': self.hostname,
                    'mac_address': self.mac_address,
                    'os_version': f"{self.os_type} {self.os_version}",
                    'agent_version': '2.1-systray'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.agent_id = result.get('agent_id')  # Server returns agent_id
                self.api_key = result.get('api_key')   # Server returns api_key
                
                # Save config
                self.config.update({
                    'agent_id': self.agent_id,
                    'api_key': self.api_key,
                    'server_url': self.server_url,
                    'registered_at': datetime.now().isoformat()
                })
                self.save_config()
                
                print(f"✅ Agent registered successfully (ID: {self.agent_id})")
                return True
            else:
                print(f"❌ Registration failed: HTTP {response.status_code}")
                try:
                    error_msg = response.json().get('error', 'Unknown error')
                    print(f"   Error: {error_msg}")
                except:
                    print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False

    def send_heartbeat(self):
        """Send heartbeat to server"""
        with self.tracer.start_as_current_span("send_heartbeat") as span:
            try:
                span.set_attribute("api.operation", "heartbeat")
                span.set_attribute("api.endpoint", f"{self.server_url}/api/agent/heartbeat")
                span.set_attribute("agent.status", self.status)
                span.set_attribute("agent.threat_count", self.threat_count)
                
                response = requests.post(
                    f"{self.server_url}/api/agent/heartbeat",
                    json={
                        'agent_id': self.agent_id,
                        'status': self.status,
                        'lastScan': self.last_scan_time,
                        'threatCount': self.threat_count
                    },
                    headers={'x-agent-api-key': self.api_key},
                    timeout=10
                )
                
                span.set_attribute("http.status_code", response.status_code)
                success = response.status_code == 200
                
                if success:
                    span.add_event("heartbeat_sent_successfully")
                else:
                    span.add_event("heartbeat_failed", {"status_code": response.status_code})
                    span.set_status(trace.Status(trace.StatusCode.ERROR, f"HTTP {response.status_code}"))
                
                return success
                
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return False

    def fetch_dlp_config(self):
        """Fetch DLP configuration from server"""
        try:
            response = requests.get(
                f"{self.server_url}/api/agent/dlp/config",
                timeout=10
            )
            
            if response.status_code == 200:
                self.dlp_config = response.json()
                self.dlp_rules = self.dlp_config.get('rules', [])
                self.dlp_enabled = self.dlp_config.get('enabled', False)
                self.last_dlp_config_update = datetime.now()
                
                print(f"🛡️  DLP Config updated: {len(self.dlp_rules)} rules, enabled: {self.dlp_enabled}")
                
                # Log DLP rules for debugging
                for rule in self.dlp_rules:
                    print(f"   📋 Rule: {rule.get('description', 'Unknown')} ({rule.get('action', 'log')})")
            else:
                print(f"⚠️  Failed to fetch DLP config: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error fetching DLP config: {e}")

    def check_dlp_violations(self, file_path, file_hash, operation_type="file_access"):
        """Check if file hash violates any DLP rules and perform appropriate actions"""
        if not self.dlp_enabled or not self.dlp_rules:
            return None
            
        for rule in self.dlp_rules:
            if rule.get('ruleType') == 'file_hash' and rule.get('ruleValue') == file_hash:
                action = rule.get('action', 'log').lower()
                
                violation = {
                    'ruleId': rule.get('id'),
                    'ruleName': rule.get('description', 'Unknown Rule'),
                    'agentId': self.agent_id,
                    'filePath': file_path,
                    'fileName': os.path.basename(file_path),
                    'fileHash': file_hash,
                    'violationType': operation_type,
                    'actionTaken': action,
                    'severity': rule.get('severity', 'medium'),
                    'userContext': os.getenv('USER', 'unknown'),
                    'detectedAt': datetime.now().isoformat(),
                    'actionStatus': 'pending',
                    'actionMessage': '',
                    'quarantinePath': None
                }
                
                print(f"🚨 DLP VIOLATION: {violation['fileName']} matches rule '{violation['ruleName']}'")
                print(f"   Action: {action.upper()}")
                
                # Perform the action based on rule
                success, message = self.perform_dlp_action(file_path, action, violation)
                
                # Update violation with action results
                violation['actionStatus'] = 'success' if success else 'failed'
                violation['actionMessage'] = message
                
                if success and action in ['quarantine', 'block']:
                    violation['quarantinePath'] = message  # message contains quarantine path on success
                
                # Add enhanced metadata for comprehensive violation reporting
                violation.update({
                    'agentVersion': getattr(self, 'current_version', '2.1.0'),
                    'osType': self.os_type,
                    'reportedAt': datetime.now().isoformat(),
                    'actionDuration': None  # Could be enhanced to track timing
                })
                
                # Report violation to server with updated status (resilient to failures)
                try:
                    reporting_success = self.report_dlp_violation(violation)
                    if reporting_success:
                        print(f"✅ Violation reported to server successfully")
                    else:
                        print(f"⚠️  Violation report failed, but agent continues running")
                        # Store violation locally for later retry if needed
                        self.store_failed_violation_report(violation)
                except Exception as e:
                    print(f"❌ Exception during violation reporting: {e}")
                    print(f"   Agent continues running - violation stored locally")
                    self.store_failed_violation_report(violation)
                
                return violation
        
        return None
    
    def perform_dlp_action(self, file_path, action, violation_info):
        """Perform the specified DLP action on a file"""
        try:
            if action == 'quarantine':
                success, result = self.quarantine_file(file_path, violation_info)
                if success:
                    return True, result  # result is quarantine path
                else:
                    return False, f"Quarantine failed: {result}"
                    
            elif action == 'block':
                # For now, we treat 'block' the same as quarantine
                # In a full implementation, this might delete the file or prevent access
                print(f"⛔ BLOCKING file: {os.path.basename(file_path)}")
                success, result = self.quarantine_file(file_path, violation_info)
                if success:
                    return True, f"File blocked and quarantined: {result}"
                else:
                    return False, f"Block/quarantine failed: {result}"
                    
            elif action == 'warn':
                print(f"⚠️  WARNING: File {os.path.basename(file_path)} violates DLP rule but action is WARN only")
                return True, "Warning issued - no file action taken"
                
            elif action == 'log':
                print(f"📝 LOGGED: DLP violation for {os.path.basename(file_path)} - no action taken")
                return True, "Violation logged - no file action taken"
                
            else:
                print(f"❓ Unknown DLP action '{action}' for file {os.path.basename(file_path)}")
                return False, f"Unknown action type: {action}"
                
        except Exception as e:
            error_msg = f"DLP action '{action}' failed for {os.path.basename(file_path)}: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def report_dlp_violation(self, violation):
        """Report DLP violation to server"""
        with self.tracer.start_as_current_span("report_dlp_violation") as span:
            try:
                span.set_attribute("api.operation", "report_dlp_violation")
                span.set_attribute("api.endpoint", f"{self.server_url}/api/agent/dlp/violation")
                span.set_attribute("violation.rule_id", violation.get('ruleId', 'unknown'))
                span.set_attribute("violation.severity", violation.get('severity', 'unknown'))
                span.set_attribute("violation.action_status", violation.get('actionStatus', 'unknown'))
                
                response = requests.post(
                    f"{self.server_url}/api/agent/dlp/violation",
                    json=violation,
                    headers={'x-agent-api-key': self.api_key},
                    timeout=10
                )
                
                span.set_attribute("http.status_code", response.status_code)
                
                if response.status_code == 200:
                    print(f"✅ DLP violation reported successfully")
                    span.add_event("violation_reported_successfully")
                    return True
                else:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_detail = response.json().get('error', error_msg)
                        print(f"⚠️  Failed to report DLP violation: {error_detail}")
                        span.add_event("violation_report_failed", {"error": error_detail})
                    except:
                        print(f"⚠️  Failed to report DLP violation: {error_msg}")
                        span.add_event("violation_report_failed", {"error": error_msg})
                    span.set_status(trace.Status(trace.StatusCode.ERROR, error_msg))
                    return False
                    
            except Exception as e:
                error_msg = f"Error reporting DLP violation: {e}"
                print(f"❌ {error_msg}")
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return False

    def store_failed_violation_report(self, violation):
        """Store failed violation reports locally for potential retry"""
        try:
            failed_reports_file = os.path.expanduser("~/FalconCore/failed_violation_reports.json")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(failed_reports_file), mode=0o700, exist_ok=True)
            
            # Load existing failed reports
            failed_reports = []
            if os.path.exists(failed_reports_file):
                try:
                    with open(failed_reports_file, 'r') as f:
                        failed_reports = json.load(f)
                except Exception as e:
                    print(f"⚠️  Warning: Could not load existing failed reports: {e}")
                    failed_reports = []
            
            # Add new failed report with timestamp
            failed_report_entry = {
                'failed_at': datetime.now().isoformat(),
                'retry_count': 0,
                'violation': violation
            }
            
            failed_reports.append(failed_report_entry)
            
            # Keep only the last 100 failed reports to prevent unlimited growth
            if len(failed_reports) > 100:
                failed_reports = failed_reports[-100:]
            
            # Save updated failed reports
            with open(failed_reports_file, 'w') as f:
                json.dump(failed_reports, f, indent=2)
            
            # Secure the failed reports file
            os.chmod(failed_reports_file, 0o600)
            
            print(f"📋 Stored failed violation report locally for later retry")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not store failed violation report: {e}")

    def analyze_false_positive(self, detection_type, item_name, details):
        """Analyze if a detection is likely a false positive"""
        false_positive_indicators = {
            'process': {
                # Legitimate software that might trigger alerts
                'crypto': ['CryptoTokenKit', 'cryptography', 'OpenSSL', 'LibreSSL'],
                'arturia': ['ArturiaSoftwareCenterAgent', 'ArturiaCenter'],
                'system': ['authd', 'kernelmanagerd', 'dasd', 'coreauthd'],
                'development': ['node', 'python', 'java', 'npm', 'gradle'],
                'browsers': ['Chrome', 'Firefox', 'Safari', 'Edge'],
                'music_software': ['Logic', 'GarageBand', 'ProTools', 'Ableton']
            },
            'network': {
                'development_ports': [3000, 8000, 8080, 3001, 5000, 9000],
                'legitimate_services': [22, 80, 443, 993, 995, 587]
            },
            'file': {
                'safe_locations': ['/Applications/', '/System/', '/usr/bin/', '~/Applications/'],
                'development_files': ['.js', '.py', '.java', '.cpp', '.go', '.rb']
            }
        }
        
        if detection_type == 'process':
            name_lower = item_name.lower()
            
            # Check for legitimate software patterns
            for category, patterns in false_positive_indicators['process'].items():
                for pattern in patterns:
                    if pattern.lower() in name_lower:
                        return True, f"Legitimate {category.replace('_', ' ')} software"
            
            # Check if it's a signed Apple process
            if any(sys_indicator in name_lower for sys_indicator in ['apple', 'com.apple', 'system']):
                return True, "Apple system process"
                
            # Check for development tools
            if any(dev_indicator in name_lower for dev_indicator in ['dev', 'debug', 'test', 'build']):
                return True, "Development/debugging tool"
                
        elif detection_type == 'network':
            port = details.get('port', 0)
            
            # Check for development ports
            if port in false_positive_indicators['network']['development_ports']:
                return True, f"Development server (port {port})"
                
            # Check for legitimate services
            if port in false_positive_indicators['network']['legitimate_services']:
                return True, f"Standard service (port {port})"
                
        elif detection_type == 'file':
            file_path = details.get('path', '')
            
            # Check for safe locations
            for safe_location in false_positive_indicators['file']['safe_locations']:
                if safe_location in file_path:
                    return True, f"File in trusted location ({safe_location})"
        
        return False, "Potential security concern"

    def scan_processes(self):
        """Scan running processes for threats"""
        with self.tracer.start_as_current_span("scan_processes") as span:
            try:
                current_processes = set()
                suspicious_processes = []
                process_logs = []
                total_processes = 0
                
                span.set_attribute("scan.component", "process_monitor")
                
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
                    total_processes += 1
                    try:
                        proc_info = proc.info
                        proc_name = proc_info['name']
                        current_processes.add(proc_name)
                        
                        # Check for suspicious process names
                        suspicious_keywords = ['miner', 'crypto', 'botnet', 'keylog', 'trojan']
                        if any(keyword in proc_name.lower() for keyword in suspicious_keywords):
                            # Analyze if this is a false positive
                            is_false_positive, reason = self.analyze_false_positive('process', proc_name, proc_info)
                            
                            process_entry = {
                                'pid': proc_info['pid'],
                                'name': proc_name,
                                'cmdline': ' '.join(proc_info['cmdline'] or [])[:100],
                                'cpu_percent': proc_info['cpu_percent'] or 0,
                                'is_false_positive': is_false_positive,
                                'analysis': reason
                            }
                            
                            suspicious_processes.append(process_entry)
                            
                            # Add to detailed logs
                            process_logs.append({
                                'type': 'Process Detection',
                                'item': proc_name,
                                'status': 'False Positive' if is_false_positive else 'Potential Threat',
                                'reason': reason,
                                'details': f"PID: {proc_info['pid']}, CPU: {proc_info['cpu_percent'] or 0}%"
                            })
                            
                            if is_false_positive:
                                self.false_positive_count += 1
                            else:
                                self.legitimate_threat_count += 1
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Detect new processes (non-suspicious)
                new_processes = current_processes - self.known_processes
                if new_processes:
                    for new_proc in list(new_processes)[:5]:
                        process_logs.append({
                            'type': 'New Process',
                            'item': new_proc,
                            'status': 'Normal Activity',
                            'reason': 'Standard process startup',
                            'details': 'No suspicious indicators detected'
                        })
                    print(f"🔍 New processes detected: {', '.join(list(new_processes)[:5])}")
                
                # Add to scan logs for summary report
                self.scan_logs.extend(process_logs)
                # Keep only last 50 logs to prevent memory bloat
                if len(self.scan_logs) > 50:
                    self.scan_logs = self.scan_logs[-50:]
                
                self.known_processes = current_processes
                
                # Add metrics to span
                span.set_attribute("scan.total_processes", total_processes)
                span.set_attribute("scan.suspicious_processes", len(suspicious_processes))
                span.set_attribute("scan.new_processes", len(new_processes))
                span.set_attribute("scan.false_positives", self.false_positive_count)
                span.set_attribute("scan.legitimate_threats", self.legitimate_threat_count)
                span.add_event("process_scan_completed", {
                    "total_processes": total_processes,
                    "suspicious_count": len(suspicious_processes),
                    "new_processes": len(new_processes)
                })
                
                return suspicious_processes
                
            except Exception as e:
                print(f"❌ Process scan error: {e}")
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return []

    def scan_network(self):
        """Scan network connections for threats"""
        with self.tracer.start_as_current_span("scan_network") as span:
            try:
                # On macOS, we may need special permissions for network scanning
                # Try with restricted permissions first
                connections = psutil.net_connections(kind='inet')
                suspicious_connections = []
                total_connections = 0
                
                span.set_attribute("scan.component", "network_monitor")
                
                for conn in connections:
                    total_connections += 1
                    try:
                        if conn.status == 'ESTABLISHED' and conn.raddr:
                            # Check for suspicious ports or IPs
                            remote_port = conn.raddr.port
                            remote_ip = conn.raddr.ip
                            
                            # Common malware ports
                            suspicious_ports = [6667, 6668, 6669, 8080, 1337, 31337]
                            if remote_port in suspicious_ports:
                                suspicious_connections.append({
                                    'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}",
                                    'remote_addr': f"{remote_ip}:{remote_port}",
                                    'status': conn.status,
                                    'pid': conn.pid if conn.pid else 'unknown'
                                })
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        # Skip connections we can't access (common on macOS)
                        continue
                
                # Add metrics to span
                span.set_attribute("scan.total_connections", total_connections)
                span.set_attribute("scan.suspicious_connections", len(suspicious_connections))
                span.add_event("network_scan_completed", {
                    "total_connections": total_connections,
                    "suspicious_count": len(suspicious_connections)
                })
                
                return suspicious_connections
                
            except psutil.AccessDenied:
                print("⚠️  Network scan requires elevated permissions on macOS")
                span.add_event("network_scan_access_denied")
                return []
            except Exception as e:
                print(f"❌ Network scan error: {e}")
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return []

    def scan_files(self):
        """Scan Downloads folder for potentially malicious files"""
        with self.tracer.start_as_current_span("scan_files") as span:
            try:
                downloads_folder = os.path.expanduser("~/Downloads")
                span.set_attribute("scan.component", "file_monitor")
                span.set_attribute("scan.directory", downloads_folder)
                
                if not os.path.exists(downloads_folder):
                    span.add_event("downloads_folder_not_found")
                    return []
                
                suspicious_files = []
                total_files = 0
                dlp_violations = 0
                dangerous_extensions = ['.exe', '.scr', '.bat', '.cmd', '.com', '.vbs', '.js']
                span.set_attribute("scan.dangerous_extensions", len(dangerous_extensions))
                
                for file_path in Path(downloads_folder).rglob('*'):
                    if file_path.is_file():
                        total_files += 1
                        file_ext = file_path.suffix.lower()
                        if file_ext in dangerous_extensions:
                            file_size = file_path.stat().st_size
                            file_hash = self.calculate_file_hash(str(file_path))
                            
                            # Check for DLP violations
                            dlp_violation = self.check_dlp_violations(str(file_path), file_hash, "file_scan")
                            if dlp_violation:
                                dlp_violations += 1
                            
                            suspicious_files.append({
                                'path': str(file_path),
                                'size': file_size,
                                'hash': file_hash,
                                'extension': file_ext,
                                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                                'dlp_violation': dlp_violation is not None,
                                'dlp_action': dlp_violation.get('actionTaken') if dlp_violation else None
                            })
                
                # Add metrics to span
                span.set_attribute("scan.total_files", total_files)
                span.set_attribute("scan.suspicious_files", len(suspicious_files))
                span.set_attribute("scan.dlp_violations", dlp_violations)
                span.add_event("file_scan_completed", {
                    "total_files": total_files,
                    "suspicious_count": len(suspicious_files),
                    "dlp_violations": dlp_violations
                })
                
                return suspicious_files
                
            except Exception as e:
                print(f"❌ File scan error: {e}")
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return []

    def calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except:
            return None

    def submit_scan_results(self, scan_data):
        """Submit scan results to server"""
        with self.tracer.start_as_current_span("submit_scan_results") as span:
            try:
                span.set_attribute("api.operation", "submit_scan_results")
                span.set_attribute("api.endpoint", f"{self.server_url}/api/agent/logs")
                
                if not self.api_key:
                    print("❌ No API key available for authentication")
                    span.add_event("api_key_missing")
                    span.set_status(trace.Status(trace.StatusCode.ERROR, "No API key"))
                    return False
                
                # Convert scan data to logs format expected by server
                logs = []
                
                # Limit logs to prevent payload too large errors
                max_logs_per_type = 20
                
                if scan_data.get('processes'):
                    # Only send the most significant process detections
                    significant_processes = [p for p in scan_data['processes'] if not p.get('is_false_positive', True)][:max_logs_per_type]
                    for proc in significant_processes:
                        logs.append({
                            'timestamp': datetime.now().isoformat(),
                            'level': 'WARN',
                            'check_type': 'process_monitoring',
                            'message': f"Process detected: {proc['name']}",
                            'threat_score': 75,
                            'details': {
                                'pid': proc['pid'],
                                'name': proc['name'],
                                'analysis': proc.get('analysis', 'Unknown')
                            }
                        })
                
                if scan_data.get('network'):
                    # Limit network connections to prevent large payloads
                    for conn in scan_data['network'][:max_logs_per_type]:
                        logs.append({
                            'timestamp': datetime.now().isoformat(),
                            'level': 'WARN',
                            'check_type': 'network_monitoring',
                            'message': f"Suspicious network connection: {conn.get('remote_addr', 'unknown')}",
                            'threat_score': 65,
                            'details': {
                                'remote_addr': conn.get('remote_addr', 'unknown'),
                                'port': conn.get('port', 0),
                                'status': conn.get('status', 'unknown')
                            }
                        })
                        
                if scan_data.get('files'):
                    # Limit file entries to prevent large payloads
                    for file_item in scan_data['files'][:max_logs_per_type]:
                        logs.append({
                            'timestamp': datetime.now().isoformat(),
                            'level': 'ERROR',
                            'check_type': 'file_monitoring',
                            'message': f"Suspicious file detected: {file_item.get('path', 'unknown')}",
                            'threat_score': 80,
                            'details': {
                                'path': file_item.get('path', 'unknown'),
                                'size': file_item.get('size', 0),
                                'modified': file_item.get('modified', 'unknown')
                            }
                        })
                
                # Add summary log entry
                if logs:
                    logs.append({
                        'timestamp': datetime.now().isoformat(),
                        'level': 'INFO',
                        'check_type': 'scan_summary',
                        'message': f"Security scan completed - {len(self.scan_logs)} events analyzed",
                        'threat_score': 0,
                        'details': {
                            'false_positives': self.false_positive_count,
                            'potential_threats': self.legitimate_threat_count,
                            'total_events': len(self.scan_logs)
                        }
                    })
                    
                response = requests.post(
                    f"{self.server_url}/api/agent/logs",
                    json={
                        'agent_id': self.agent_id,
                        'logs': logs
                    },
                    headers={'x-agent-api-key': self.api_key},
                    timeout=30
                )
                
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("logs.count", len(logs))
                
                if response.status_code == 200:
                    span.add_event("scan_results_submitted")
                    return True
                else:
                    print(f"❌ Submit failed: HTTP {response.status_code}")
                    span.add_event("scan_results_failed", {"status_code": response.status_code})
                    try:
                        error_msg = response.json().get('error', 'Unknown error')
                        print(f"   Error: {error_msg}")
                    except:
                        pass
                    return False
                    
            except Exception as e:
                print(f"❌ Submit error: {e}")
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return False

    def run_security_scan(self):
        """Run complete security scan"""
        if self.is_scanning:
            return
            
        self.is_scanning = True
        self.status = "Scanning..."
        
        with self.tracer.start_as_current_span("security_scan") as span:
            try:
                # Add custom attributes to the span
                span.set_attribute("agent.id", self.agent_id or "unknown")
                span.set_attribute("host.name", self.hostname)
                span.set_attribute("scan.type", "full_security_scan")
                span.set_attribute("scan.start_time", datetime.now().isoformat())
                
                print(f"🔍 Starting security scan at {datetime.now()}")
                
                # Perform scans with individual spans
                suspicious_processes = self.scan_processes()
                suspicious_connections = self.scan_network()
                suspicious_files = self.scan_files()
                
                # Calculate threat count
                threat_count = len(suspicious_processes) + len(suspicious_connections) + len(suspicious_files)
                self.threat_count = threat_count
                
                # Add metrics to span
                span.set_attribute("scan.processes_found", len(suspicious_processes))
                span.set_attribute("scan.connections_found", len(suspicious_connections))
                span.set_attribute("scan.files_found", len(suspicious_files))
                span.set_attribute("scan.total_threats", threat_count)
                
                # Prepare scan data
                scan_data = {
                    'scanTime': datetime.now().isoformat(),
                    'processes': suspicious_processes,
                    'network': suspicious_connections,
                    'files': suspicious_files,
                    'threatCount': threat_count
                }
                
                # Submit results
                submit_success = self.submit_scan_results(scan_data)
                span.set_attribute("scan.submit_success", submit_success)
                
                if submit_success:
                    print(f"✅ Scan completed - {threat_count} threats detected")
                    span.add_event("scan_completed_successfully")
                else:
                    print(f"⚠️  Scan completed - failed to submit results")
                    span.add_event("scan_submit_failed")
                
                self.last_scan_time = datetime.now().isoformat()
                self.status = f"Active - {threat_count} threats"
                
                # Add alerts for threats
                if threat_count > 0:
                    alert = f"⚠️ {threat_count} security threats detected"
                    if alert not in self.alerts:
                        self.alerts.append(alert)
                        if len(self.alerts) > 10:  # Keep last 10 alerts
                            self.alerts.pop(0)
                    span.add_event("threats_detected", {"threat_count": threat_count})
                            
            except Exception as e:
                print(f"❌ Scan error: {e}")
                self.status = f"Error: {str(e)[:50]}"
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            finally:
                self.is_scanning = False

    def start_monitoring(self):
        """Start continuous monitoring in background thread"""
        self.running = True
        
        # Fetch DLP configuration
        self.fetch_dlp_config()
        
        def monitor_loop():
            while self.running:
                if not self.is_scanning:
                    self.run_security_scan()
                    self.send_heartbeat()
                    
                    # Check for agent updates (respects hourly interval)
                    self.check_for_updates()
                    
                    # Refresh DLP config every hour
                    if (not self.last_dlp_config_update or 
                        (datetime.now() - self.last_dlp_config_update).total_seconds() > 3600):
                        self.fetch_dlp_config()
                
                time.sleep(self.scan_interval)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        print(f"✅ Monitoring started with {self.scan_interval}s interval")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        self.status = "Stopped"
        print("🛑 Monitoring stopped")

    def generate_security_summary(self):
        """Generate intelligent security summary with false positive analysis"""
        if not self.scan_logs:
            return "No recent security activity detected."
        
        # Count different types of activity
        false_positives = sum(1 for log in self.scan_logs if log['status'] == 'False Positive')
        potential_threats = sum(1 for log in self.scan_logs if log['status'] == 'Potential Threat')
        normal_activity = sum(1 for log in self.scan_logs if log['status'] == 'Normal Activity')
        
        # Generate summary text
        summary_lines = [
            "🔍 SECURITY ANALYSIS SUMMARY",
            "=" * 30,
            f"Total Events: {len(self.scan_logs)}",
            f"False Positives: {false_positives} ✅",
            f"Potential Threats: {potential_threats} ⚠️",
            f"Normal Activity: {normal_activity} 👍",
            "",
            "📋 RECENT ACTIVITY:"
        ]
        
        # Show recent events with analysis
        recent_logs = self.scan_logs[-10:]  # Last 10 events
        for log in recent_logs:
            status_icon = "✅" if log['status'] == 'False Positive' else "⚠️" if log['status'] == 'Potential Threat' else "👍"
            summary_lines.append(f"{status_icon} {log['type']}: {log['item']}")
            summary_lines.append(f"   Reason: {log['reason']}")
            if log['details']:
                summary_lines.append(f"   Details: {log['details']}")
            summary_lines.append("")
        
        # Add recommendations
        if false_positives > potential_threats:
            summary_lines.extend([
                "💡 ASSESSMENT:",
                "Your system shows mostly false positives from",
                "legitimate software. This is normal for active",
                "development machines with music/creative software."
            ])
        elif potential_threats > 0:
            summary_lines.extend([
                "⚠️  ASSESSMENT:",
                f"Found {potential_threats} items requiring attention.",
                "Review the potential threats above."
            ])
        else:
            summary_lines.extend([
                "✅ ASSESSMENT:",
                "All activity appears normal. No threats detected."
            ])
        
        return "\n".join(summary_lines)


class FalconCoreTrayApp:
    """System tray application wrapper"""
    
    def __init__(self):
        self.agent = FalconCoreAgent()
        
        # Initialize system tray based on platform and available libraries
        self.os_system = platform.system()
        
        if self.os_system == 'Darwin' and RUMPS_AVAILABLE:
            print("🍎 Using native macOS system tray (rumps)")
            self.use_rumps()
        elif PYSTRAY_AVAILABLE:
            print(f"🖥️  Using cross-platform system tray for {self.os_system}")
            self.use_pystray()
        else:
            print(f"❌ No system tray library available for {self.os_system}. Running in console mode...")
            self.run_console_mode()

    def use_rumps(self):
        """Use rumps for macOS system tray"""
        app = rumps.App("FalconCore", "🦅")
        
        @rumps.clicked("Status")
        def show_status(sender):
            rumps.alert(f"FalconCore Agent Status", self.agent.status)
        
        @rumps.clicked("Start Scan")
        def start_scan(sender):
            if not self.agent.is_scanning:
                threading.Thread(target=self.agent.run_security_scan, daemon=True).start()
        
        @rumps.clicked("View Alerts")
        def view_alerts(sender):
            if self.agent.alerts:
                rumps.alert("Recent Alerts", "\n".join(self.agent.alerts[-5:]))
            else:
                rumps.alert("No Alerts", "No security alerts detected")
        
        def security_summary(sender):
            summary = self.agent.generate_security_summary()
            rumps.alert("Security Summary", summary)
        
        @rumps.clicked("Settings")
        def settings(sender):
            response = rumps.Window(
                message="Enter scan interval (seconds):",
                default_text=str(self.agent.scan_interval),
                ok="Save",
                cancel="Cancel"
            ).run()
            
            if response.clicked:
                try:
                    new_interval = int(response.text)
                    if new_interval >= 60:  # Minimum 1 minute
                        self.agent.scan_interval = new_interval
                        self.agent.config['scan_interval'] = new_interval
                        self.agent.save_config()
                        rumps.alert("Settings Saved", f"Scan interval updated to {new_interval} seconds")
                except ValueError:
                    rumps.alert("Invalid Input", "Please enter a valid number")
        
        @rumps.clicked("Security Summary")
        def security_summary(sender):
            summary = self.agent.generate_security_summary()
            rumps.alert("Security Summary", summary)
        
        app.menu = [
            "Status",
            "Security Summary",
            rumps.separator,
            "Start Scan",
            "View Alerts",
            rumps.separator,
            "Settings"
        ]
        
        # Register and start monitoring
        if self.agent.register_agent():
            self.agent.start_monitoring()
        
        app.run()

    def use_pystray(self):
        """Use pystray for cross-platform system tray"""
        def create_image():
            # Create a falcon-like icon
            image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw falcon head/beak shape
            draw.ellipse([10, 15, 50, 45], fill='#2D5A27', outline='#1A3D1A')  # Head
            draw.polygon([(50, 30), (60, 25), (60, 35)], fill='#FFA500')  # Beak
            draw.ellipse([35, 22, 42, 29], fill='#FFD700')  # Eye
            
            # Add threat indicator if threats detected
            if self.agent.threat_count > 0:
                draw.ellipse([45, 10, 60, 25], fill='#FF4444', outline='#CC0000')  # Red alert
                
            return image

        def show_status(icon, item):
            if TKINTER_AVAILABLE:
                self.show_status_dialog()
            else:
                print(f"📊 Status: {self.agent.status}")
                print(f"🕐 Last scan: {self.agent.last_scan_time}")
                print(f"⚠️  Threats: {self.agent.threat_count}")

        def start_scan(icon, item):
            if not self.agent.is_scanning:
                threading.Thread(target=self.agent.run_security_scan, daemon=True).start()

        def view_alerts(icon, item):
            if self.agent.alerts:
                if TKINTER_AVAILABLE:
                    alert_text = "\n".join(self.agent.alerts[-10:])
                    self.show_alert_dialog("Recent Alerts", alert_text)
                else:
                    print("📋 Recent Alerts:")
                    for alert in self.agent.alerts[-10:]:
                        print(f"  • {alert}")
            else:
                if TKINTER_AVAILABLE:
                    self.show_alert_dialog("No Alerts", "No security alerts detected")
                else:
                    print("✅ No security alerts detected")

        def open_dashboard(icon, item):
            import webbrowser
            dashboard_url = f"{self.agent.server_url}"
            try:
                webbrowser.open(dashboard_url)
            except:
                if TKINTER_AVAILABLE:
                    self.show_alert_dialog("Error", f"Could not open dashboard at {dashboard_url}")

        def open_settings(icon, item):
            if TKINTER_AVAILABLE:
                self.show_settings_dialog()
            else:
                print(f"⚙️  Current scan interval: {self.agent.scan_interval} seconds")

        def show_security_summary(icon, item):
            summary = self.agent.generate_security_summary()
            if TKINTER_AVAILABLE:
                self.show_summary_dialog(summary)
            else:
                print(summary)

        def quit_app(icon, item):
            self.agent.stop_monitoring()
            icon.stop()

        def check_updates_manual(icon, item):
            """Manual update check from menu"""
            threading.Thread(target=self.agent.check_for_updates, daemon=True).start()

        def install_update_manual(icon, item):
            """Manual update installation from menu"""
            if self.agent.update_available:
                threading.Thread(target=self.agent.install_update, daemon=True).start()
            else:
                print("⚠️ No update available")

        # Create menu
        menu = pystray.Menu(
            item('Status', show_status),
            item('Security Summary', show_security_summary),
            pystray.Menu.SEPARATOR,
            item('Start Scan', start_scan),
            item('View Alerts', view_alerts),
            pystray.Menu.SEPARATOR,
            item('Dashboard', open_dashboard),
            item('Settings', open_settings),
            pystray.Menu.SEPARATOR,
            item('Check Updates', check_updates_manual),
            item('Install Update', install_update_manual, enabled=lambda _: self.agent.update_available),
            pystray.Menu.SEPARATOR,
            item('Quit', quit_app)
        )

        # Create and run tray icon
        icon = pystray.Icon("FalconCore", create_image(), menu=menu)
        
        # Register and start monitoring
        if self.agent.register_agent():
            self.agent.start_monitoring()
        
        icon.run()

    def show_status_dialog(self):
        """Show detailed status in GUI dialog"""
        if not TKINTER_AVAILABLE:
            return
            
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        status_text = f"""FalconCore Security Agent
        
Status: {self.agent.status}
Last Scan: {self.agent.last_scan_time or 'Never'}
Threats Detected: {self.agent.threat_count}
Scan Interval: {self.agent.scan_interval} seconds
Agent ID: {self.agent.agent_id[:8] if self.agent.agent_id else 'None'}...
Server: {self.agent.server_url}
OS: {self.agent.os_type} {self.agent.os_version}"""
        
        messagebox.showinfo("FalconCore Status", status_text)
        root.destroy()

    def show_summary_dialog(self, summary):
        """Show security summary in GUI dialog"""
        if not TKINTER_AVAILABLE:
            return
            
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        # Create a scrollable text window for long summaries
        top = tk.Toplevel(root)
        top.title("FalconCore Security Summary")
        top.geometry("600x500")
        
        # Add scrollable text widget
        text_frame = tk.Frame(top)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap=tk.WORD, font=("Monaco", 10))
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=text_widget.yview)
        
        # Insert summary text
        text_widget.insert(tk.END, summary)
        text_widget.config(state=tk.DISABLED)  # Make read-only
        
        # Add close button
        close_button = tk.Button(top, text="Close", command=lambda: [top.destroy(), root.destroy()])
        close_button.pack(pady=5)
        
        # Center the window
        top.transient(root)
        top.grab_set()
        root.wait_window(top)

    def show_alert_dialog(self, title, message):
        """Show alert dialog"""
        if not TKINTER_AVAILABLE:
            return
            
        root = tk.Tk()
        root.withdraw()  # Hide main window
        messagebox.showinfo(title, message)
        root.destroy()

    def show_settings_dialog(self):
        """Show settings configuration dialog"""
        if not TKINTER_AVAILABLE:
            return
            
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        new_interval = tk.simpledialog.askinteger(
            "Settings",
            f"Enter scan interval in seconds\n(Current: {self.agent.scan_interval}s, Minimum: 60s):",
            initialvalue=self.agent.scan_interval,
            minvalue=60,
            maxvalue=3600
        )
        
        if new_interval and new_interval != self.agent.scan_interval:
            self.agent.scan_interval = new_interval
            self.agent.config['scan_interval'] = new_interval
            self.agent.save_config()
            messagebox.showinfo("Settings", f"Scan interval updated to {new_interval} seconds")
            
        root.destroy()

    def run_console_mode(self):
        """Fallback console mode"""
        print("🖥️  Running in console mode (system tray not available)")
        
        if self.agent.register_agent():
            self.agent.start_monitoring()
            
            try:
                while True:
                    command = input("\nCommands: [s]can, [q]uit, [status]: ").strip().lower()
                    
                    if command in ['q', 'quit', 'exit']:
                        break
                    elif command in ['s', 'scan']:
                        if not self.agent.is_scanning:
                            self.agent.run_security_scan()
                        else:
                            print("Scan already in progress...")
                    elif command in ['status']:
                        print(f"Status: {self.agent.status}")
                        print(f"Last scan: {self.agent.last_scan_time}")
                        print(f"Threat count: {self.agent.threat_count}")
                    else:
                        print("Unknown command")
                        
            except KeyboardInterrupt:
                pass
            finally:
                self.agent.stop_monitoring()
                print("\n🛑 Agent stopped")


def main():
    """Main entry point"""
    print("🦅 FalconCore Security Agent - System Tray Edition")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
        print(f"🌐 Using server URL: {server_url}")
    else:
        print("ℹ️  Usage: python falconcore-agent-systray.py [SERVER_URL]")
        print("ℹ️  Example: python falconcore-agent-systray.py http://localhost:5000")
        server_url = "http://localhost:5000"
    
    try:
        app = FalconCoreTrayApp()
        app.agent.server_url = server_url
        app.agent.config['server_url'] = server_url
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()