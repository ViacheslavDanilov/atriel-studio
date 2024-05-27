# Use the official ContinuumIO miniconda3 image
FROM continuumio/miniconda3

# Set the working directory
WORKDIR /atriel-studio

# Set the environment variables
ENV ENV_NAME=atriel
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT=7860
ENV SSH_PORT=7822

# Install dependencies
RUN apt-get update && apt-get install -y git libgl1-mesa-glx libglib2.0-0

# Clone the repository
# RUN git clone https://github.com/ViacheslavDanilov/atriel-studio.git .
RUN git clone --branch docker https://github.com/ViacheslavDanilov/atriel-studio.git .

# Install dependencies
RUN conda env create --file environment.yaml --verbose

# Copy the .env file to the working directory
COPY .env .

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "atriel", "/bin/bash", "-c"]

# Activate environment and install the project as a package
RUN conda run -n atriel pip install -e .

# Expose the port that your app runs on
EXPOSE ${GRADIO_SERVER_PORT}
EXPOSE ${SSH_PORT}

# Run the application
CMD ["conda", "run", "--no-capture-output", "-n", "atriel", "python", "app.py"]
