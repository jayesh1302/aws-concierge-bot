# Image for a Python 3 development environment
FROM python:3.9-slim

# Add any tools that are needed beyond Python 3.11
RUN apt-get update && \
    apt-get install -y sudo vim make git zip tree curl wget jq procps net-tools && \
    apt-get install -y gcc libpq-dev && \
    apt-get autoremove -y && \
    apt-get clean -y

# Create a user for VSCode development
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user with passwordless sudo privileges
RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash && \
    usermod -aG sudo $USERNAME && \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME && \
    chown -R $USERNAME:$USERNAME /home/$USERNAME

## install terraform
ENV TERRAFORM_VERSION 1.5.7
RUN apt-get install unzip wget -y \
    && wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    && unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    && mv terraform /usr/local/bin/ \
    && terraform --version  # Display version for debugging purposes only

## install aws CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && sudo ./aws/install

# Set up the Python development environment
WORKDIR /app
RUN python -m pip install --upgrade pip wheel poetry
COPY .devcontainer/scripts/requirements.txt .
RUN pip install -r requirements.txt

ENV PORT 8080
EXPOSE $PORT

# Force color terminal for docker exec bash
ENV TERM=xterm-256color

# Become a regular user for development
USER $USERNAME