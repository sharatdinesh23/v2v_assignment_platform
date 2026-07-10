# AWS region where resources will be created
aws_region = "us-east-1"

# Instance size (change if not using the free tier or self-hosting Appwrite)
instance_type = "t2.micro"

# NAME of your existing EC2 Key Pair (do not include the .pem extension)
key_name = "access_ssh"

# Restrict SSH access to your public IP for better security (optional but recommended)
# Get your public IP from https://ifconfig.me and append /32 (e.g. "203.0.113.50/32")
allowed_ssh_ip = "0.0.0.0/0"
