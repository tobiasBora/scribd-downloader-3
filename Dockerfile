FROM ubuntu:16.04
# To use the online image, use:
# $ sudo docker run -it --shm-size 2g -v $(pwd):/host -w /host tobiasbora/scribd-downloader:18.01 bash
# And then inside the container (don't forget xvfb):
# $ xvfb-run ./scribd_downloader_3.py "https://www.scribd.com/doc/63942746/chopin-nocturne-n-20-partition" out.pdf

# If you want to build this image, run:
# $ sudo docker build -t scribd-d .
# And to run it:
# $ sudo docker run -it --shm-size 2g -v $(pwd):/host -w /host scribd-d bash
# And then inside the container (don't forget xvfb):
# $ xvfb-run ./scribd_downloader_3.py "https://www.scribd.com/doc/63942746/chopin-nocturne-n-20-partition" out.pdf


RUN apt-get update && apt-get install -y wget python3 python3-pip firefox xvfb

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Make sure we have the latest pip version
RUN pip3 install --upgrade pip

# Install requirements
RUN pip3 install -r requirements.txt

# Make sure the script is executable
RUN chmod +x scribd_downloader_3.py

# Download geckodriver
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.19.0/geckodriver-v0.19.0-linux64.tar.gz
RUN tar zxvf geckodriver-v0.19.0-linux64.tar.gz

# Set-up the environment variables
ENV PATH="/app:${PATH}"

