provider "aws" {
  region = "us-east-1"
}

# 1. Upload your local public key to AWS
resource "aws_key_pair" "deployer" {
  key_name   = "terraform-key"
  public_key = file("my-key.pub")
}

# 2. Create a Firewall (Security Group)
resource "aws_security_group" "allow_ssh" {
  name        = "allow_ssh"
  description = "Allow SSH inbound traffic"

  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: In prod, replace this with your IP
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # Allow all outbound traffic
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 3. Create the Server
resource "aws_instance" "my_first_server" {
  ami           = "ami-04b4f1a9cf54c11d0" # Ubuntu 24.04
  instance_type = "t2.micro"

  # Link the Key and the Firewall here
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.allow_ssh.id]

  tags = {
    Name = "My-Terraform-Server"
  }
}

# 4. Output the IP address automatically
output "instance_ip" {
  value = aws_instance.my_first_server.public_ip
}