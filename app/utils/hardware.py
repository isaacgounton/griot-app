"""
Hardware detection and optimization utilities.

This module provides intelligent hardware detection and optimization
for better performance across different deployment environments.
"""
import os
import psutil
from typing import Dict, Any, Optional
from loguru import logger

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available - hardware optimization disabled")

class HardwareOptimizer:
    """Hardware detection and optimization for better performance."""
    
    def __init__(self):
        self.device = self._detect_device()
        self.cpu_info = self._get_cpu_info()
        self.memory_info = self._get_memory_info()
        self.optimization_applied = False
        
    def _detect_device(self) -> str:
        """Detect the best available compute device."""
        if not TORCH_AVAILABLE:
            return "cpu"
            
        # Check CUDA availability
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"CUDA device detected: {device_name}")
            return "cuda"
            
        # Check MPS (Apple Silicon) availability
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("Apple MPS (Metal Performance Shaders) detected")
            return "mps"
            
        # Fallback to CPU
        logger.info("Using CPU device")
        return "cpu"
        
    def _get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information and optimization settings."""
        cpu_count = os.cpu_count()
        
        # Check for container CPU limits (Docker/Kubernetes)
        container_cpu_limit = self._get_container_cpu_limit()
        if container_cpu_limit:
            effective_cores = container_cpu_limit
            logger.info(f"Container CPU limit detected: {effective_cores} cores")
        else:
            effective_cores = cpu_count
            logger.info(f"System CPU count: {effective_cores} cores")
            
        # Calculate optimal thread count
        # Use 1.5x cores for I/O bound operations, but cap at physical cores for CPU bound
        optimal_threads = min(int(effective_cores * 1.5), cpu_count)
        
        return {
            "total_cores": cpu_count,
            "effective_cores": effective_cores,
            "optimal_threads": optimal_threads,
            "container_limited": container_cpu_limit is not None
        }
        
    def _get_container_cpu_limit(self) -> Optional[int]:
        """Detect CPU limits in containerized environments."""
        cpu_max_path = "/sys/fs/cgroup/cpu.max"
        
        if not os.path.exists(cpu_max_path):
            return None
            
        try:
            with open(cpu_max_path, "r") as f:
                line = f.readline().strip()
                
            if not line or len(line.split()) != 2:
                return None
                
            cpu_max, cpu_period = line.split()
            
            if cpu_max == "max":
                return None
                
            cpu_limit = int(cpu_max) // int(cpu_period)
            return max(1, cpu_limit)  # Ensure at least 1 core
            
        except (ValueError, IOError) as e:
            logger.warning(f"Failed to read container CPU limit: {e}")
            return None
            
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get system memory information."""
        memory = psutil.virtual_memory()
        
        return {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": memory.percent
        }
        
    def apply_optimizations(self):
        """Apply hardware-specific optimizations."""
        if self.optimization_applied:
            return
            
        logger.info("Applying hardware optimizations...")
        
        # PyTorch optimizations
        if TORCH_AVAILABLE:
            self._apply_torch_optimizations()
        else:
            logger.info("PyTorch not available - skipping PyTorch optimizations")
            
        # CPU optimizations
        self._apply_cpu_optimizations()
        
        # Log optimization summary
        self._log_optimization_summary()
        
        self.optimization_applied = True
        
    def _apply_torch_optimizations(self):
        """Apply PyTorch-specific optimizations."""
        try:
            # Set number of threads for PyTorch operations
            torch.set_num_threads(self.cpu_info["optimal_threads"])
            
            # Enable optimized attention if available (PyTorch 2.0+)
            if torch.cuda.is_available():
                try:
                    torch.backends.cuda.matmul.allow_tf32 = True
                    torch.backends.cudnn.allow_tf32 = True
                    logger.info("CUDA optimizations enabled (TF32)")
                except AttributeError:
                    logger.warning("CUDA TF32 optimizations not available in this PyTorch version")
                    
            # Patch torch.load to use appropriate device mapping
            if hasattr(torch, 'load'):
                original_load = torch.load
                device_map = torch.device(self.device)
                
                def patched_load(*args, **kwargs):
                    if "map_location" not in kwargs:
                        kwargs["map_location"] = device_map
                    return original_load(*args, **kwargs)
                    
                torch.load = patched_load
                
            logger.info(f"PyTorch optimizations applied for {self.device}")
            
        except Exception as e:
            logger.warning(f"Failed to apply some PyTorch optimizations: {e}")
        
    def _apply_cpu_optimizations(self):
        """Apply CPU-specific optimizations."""
        # Set optimal thread count for CPU-bound operations
        optimal_threads = self.cpu_info["optimal_threads"]
        
        # Set environment variables for various libraries
        os.environ.setdefault("OMP_NUM_THREADS", str(optimal_threads))
        os.environ.setdefault("MKL_NUM_THREADS", str(optimal_threads))
        os.environ.setdefault("NUMEXPR_NUM_THREADS", str(optimal_threads))
        
        logger.info(f"CPU optimizations applied: {optimal_threads} threads")
        
    def _log_optimization_summary(self):
        """Log a summary of applied optimizations."""
        context_logger = logger.bind(
            device=self.device,
            cpu_cores=self.cpu_info["effective_cores"],
            optimal_threads=self.cpu_info["optimal_threads"],
            memory_gb=self.memory_info["total_gb"],
            container_limited=self.cpu_info["container_limited"]
        )
        
        context_logger.info("Hardware optimization summary")
        
    def get_device_info(self) -> Dict[str, Any]:
        """Get comprehensive device information."""
        info = {
            "compute_device": self.device,
            "cpu_info": self.cpu_info,
            "memory_info": self.memory_info,
            "torch_available": TORCH_AVAILABLE,
            "optimizations_applied": self.optimization_applied
        }
        
        if TORCH_AVAILABLE and self.device == "cuda":
            info["cuda_info"] = {
                "device_count": torch.cuda.device_count(),
                "current_device": torch.cuda.current_device(),
                "device_name": torch.cuda.get_device_name(0)
            }
            
        return info
        
    def get_optimal_worker_count(self, io_bound: bool = True) -> int:
        """Get optimal worker count for different workload types."""
        if io_bound:
            # For I/O bound tasks, use more workers
            return min(self.cpu_info["optimal_threads"], 32)
        else:
            # For CPU bound tasks, use fewer workers
            return self.cpu_info["effective_cores"]

# Global hardware optimizer instance
hardware_optimizer = HardwareOptimizer()

def get_device() -> str:
    """Get the optimal compute device."""
    return hardware_optimizer.device

def get_device_info() -> Dict[str, Any]:
    """Get comprehensive device information."""
    return hardware_optimizer.get_device_info()

def apply_hardware_optimizations():
    """Apply all hardware optimizations."""
    hardware_optimizer.apply_optimizations()

def get_optimal_worker_count(io_bound: bool = True) -> int:
    """Get optimal worker count for the current hardware."""
    return hardware_optimizer.get_optimal_worker_count(io_bound)