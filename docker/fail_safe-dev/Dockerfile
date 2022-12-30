FROM python:3.10-slim
ARG FUNCTION_DIR="/home/app"

RUN apt-get clean

RUN apt-get update && apt-get install -y \
  curl git iputils-ping htop nano iperf3 zsh make

RUN python -m pip install --upgrade pip

# Append any aliases we wanted
ADD ./docker/fail_safe-dev/.bashrc /root/.bashrc_append
RUN cat /root/.bashrc_append >> /root/.bashrc

# Install Python convenience packages
ADD ./docker/fail_safe-dev/requirements.txt /root/app_requirements.txt
RUN python -m pip install -r /root/app_requirements.txt

# Add vscode workspace
ADD ./docker/fail_safe-dev/fail_safe.code-workspace ${FUNCTION_DIR}/fail_safe.code-workspace

# Create the mount point, copy the current repo over, and install editable.
# If pyproject.toml changes sufficiently for this not to work, then
# manually use `make pip_reinstall`.
ADD ./ ${FUNCTION_DIR}/fail_safe
RUN python -m pip install -e "${FUNCTION_DIR}/fail_safe[dev]"
RUN rm -rf ${FUNCTION_DIR}/fail_safe/*

VOLUME ["${FUNCTION_DIR}/fail_safe"]

ENTRYPOINT ["bash"]
