# Base image
FROM continuumio/miniconda3:25.3.1-1

# Create app directory
WORKDIR /usr/src/app

# Set env variables to optimise Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY environment.yaml /usr/src/app/
RUN conda env create -f environment.yaml 