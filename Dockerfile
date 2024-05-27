# Use the official ContinuumIO miniconda3 image
FROM continuumio/miniconda3

# Set the working directory
WORKDIR /atriel-studio

# Install dependencies
RUN apt-get update && apt-get install -y git libgl1-mesa-glx libglib2.0-0

# Clone the repository
RUN git clone --branch main https://github.com/ViacheslavDanilov/atriel-studio.git .

# Install dependencies
RUN conda env create --file environment.yaml --verbose

# Copy the .env file to the working directory
COPY .env .

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "atriel", "/bin/bash", "-c"]

# Activate environment and install the project as a package
RUN pip install -e .

# Run the application
CMD ["conda", "run", "--no-capture-output", "-n", "atriel", "python", "app.py"]
