# Use official CUDA-enabled Python image
FROM nvidia/cuda:12.2.0-base-ubuntu22.04

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Install torch and torchvision with CUDA support
RUN pip3 install torch torchvision

# Copy your CUDA test script
COPY app/cuda_test.py /app/cuda_test.py

WORKDIR /app

# Run the CUDA test script
CMD ["python3", "cuda_test.py"]
