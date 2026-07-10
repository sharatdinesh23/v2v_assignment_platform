variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 Instance type (use t2.micro or t3.micro for AWS Free Tier)"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "Name of the existing AWS Key Pair to use for SSH access"
  type        = string
}

variable "allowed_ssh_ip" {
  description = "CIDR block allowed to connect via SSH (e.g. 192.168.1.1/32 for single IP)"
  type        = string
  default     = "0.0.0.0/0"
}
