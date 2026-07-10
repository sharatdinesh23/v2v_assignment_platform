output "public_ip" {
  description = "The static public Elastic IP address assigned to the EC2 instance"
  value       = aws_eip.code_arena_eip.public_ip
}

output "ssh_connection_string" {
  description = "Convenience SSH command to connect to the instance"
  value       = "ssh -i /path/to/your-key.pem ubuntu@${aws_eip.code_arena_eip.public_ip}"
}
