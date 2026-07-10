terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- VPC & Networking ---

resource "aws_vpc" "code_arena_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "code-arena-vpc"
  }
}

resource "aws_internet_gateway" "code_arena_igw" {
  vpc_id = aws_vpc.code_arena_vpc.id

  tags = {
    Name = "code-arena-igw"
  }
}

resource "aws_subnet" "code_arena_subnet" {
  vpc_id                  = aws_vpc.code_arena_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "code-arena-public-subnet"
  }
}

resource "aws_route_table" "code_arena_rt" {
  vpc_id = aws_vpc.code_arena_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.code_arena_igw.id
  }

  tags = {
    Name = "code-arena-route-table"
  }
}

resource "aws_route_table_association" "code_arena_rta" {
  subnet_id      = aws_subnet.code_arena_subnet.id
  route_table_id = aws_route_table.code_arena_rt.id
}

# --- Security Group ---

resource "aws_security_group" "code_arena_sg" {
  name        = "code-arena-security-group"
  description = "Allow inbound SSH, HTTP, and HTTPS traffic"
  vpc_id      = aws_vpc.code_arena_vpc.id

  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_ip]
  }

  ingress {
    description = "HTTP access for web dashboard"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS access for secure dashboard"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "code-arena-sg"
  }
}

# --- AMI Lookup ---

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

# --- EC2 Instance ---

resource "aws_instance" "code_arena_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.code_arena_subnet.id
  vpc_security_group_ids = [aws_security_group.code_arena_sg.id]
  key_name               = var.key_name

  # Provisioning User Data script to install Docker automatically
  user_data = <<-EOF
              #!/bin/bash
              # Update package list and upgrade packages
              apt-get update && apt-get upgrade -y

              # Install dependencies
              apt-get install -y ca-certificates curl gnupg lsb-release git

              # Add Docker's official GPG key
              mkdir -p /etc/apt/keyrings
              curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

              # Set up Docker repository
              echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

              # Install Docker Engine & Docker Compose plugin
              apt-get update
              apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

              # Start and enable Docker service
              systemctl start docker
              systemctl enable docker

              # Allow the ubuntu user to run Docker commands without sudo
              usermod -aG docker ubuntu
              EOF

  tags = {
    Name = "code-arena-server"
  }
}

# --- Static IP (Elastic IP) ---

resource "aws_eip" "code_arena_eip" {
  instance = aws_instance.code_arena_server.id
  domain   = "vpc"

  tags = {
    Name = "code-arena-eip"
  }
}
