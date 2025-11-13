import torch
import numpy as np
import time

def continuous_gpu_work():
    # Check if GPU is available
    if not torch.cuda.is_available():
        print("CUDA not available. Exiting.")
        return

    print("GPU is available. Starting continuous random work on GPU...")
    print("Press Ctrl+C to stop the script.")

    try:
        while True:
            # Generate random data directly on the GPU
            # Using a large size to ensure significant GPU utilization
            size = (4096, 4096) 
            a = torch.randn(size, device='cuda')
            b = torch.randn(size, device='cuda')

            # Perform a matrix multiplication (a common GPU-intensive task)
            c = torch.matmul(a, b)

            # Optional: Add a small delay to prevent the system from becoming completely unresponsive
            # time.sleep(0.01) 
            
            # Note: The operations are asynchronous. To ensure the GPU is actually busy, 
            # we can add a synchronization call, though it might not be necessary for continuous
            # background usage.
            # torch.cuda.synchronize() 

    except KeyboardInterrupt:
        # Graceful exit on Ctrl+C
        print("\nScript stopped by user (Ctrl+C).")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    continuous_gpu_work()
