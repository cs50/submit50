FROM cs50/cli
ENV PATH /root/opt/cs50/submit50/bin:"$PATH"
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y expect jq util-linux
