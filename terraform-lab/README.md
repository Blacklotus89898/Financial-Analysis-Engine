🚀 Setup & Usage
1. Configure Credentials
Run the following command to link your terminal to your AWS account. You will need your Access Key ID and Secret Access Key.

Bash

aws configure
# Default Region: us-east-1
# Default Output: json
2. Generate SSH Keys
Create a local SSH key pair. Terraform will upload the public half to AWS and you will keep the private half to log in.

Bash

# Run this inside the project folder
ssh-keygen -t ed25519 -f my-key
Passphrase: Just hit Enter (leave empty) for this lab.

This generates my-key (Private) and my-key.pub (Public).

3. Initialize Terraform
Download the necessary AWS plugins.

Bash

terraform init
4. Deploy the Infrastructure
Review the plan and create the server.

Bash

terraform apply
Type yes when prompted.

Wait: It takes ~30-60 seconds.

Output: Note the instance_ip printed at the end.

5. Connect to the Server
Use the private key you generated in Step 2 to log in. Replace <IP_ADDRESS> with the IP from the previous step.

Bash

ssh -i my-key ubuntu@<IP_ADDRESS>
📄 The Terraform Code (main.tf)
Save the following code as main.tf in your project folder.

Terraform

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
    cidr_blocks = ["0.0.0.0/0"] 
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
  ami           = "ami-04b4f1a9cf54c11d0" # Ubuntu 24.04 LTS (us-east-1)
  instance_type = "t2.micro"              # Free Tier Eligible

  # Link the Key and the Firewall
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.allow_ssh.id]

  tags = {
    Name = "My-Terraform-Server"
  }
}

# 4. Output the Public IP
output "instance_ip" {
  description = "The public IP of the EC2 instance"
  value       = aws_instance.my_first_server.public_ip
}
🧹 Cleanup (Important!)
To avoid AWS charges, always destroy your infrastructure when you are done.

Bash

terraform destroy
Type yes to confirm.

❓ Troubleshooting
Error: "Permissions 0644 for 'my-key' are too open."

Cause: SSH requires your private key to be secret.

Fix: Run chmod 400 my-key to secure it.

Error: "Error establishing connection"

Cause: The Security Group didn't attach, or the instance is still booting.

Fix: Wait 30 seconds and try again. Ensure terraform apply finished successfully.

Error: "InvalidAMIID.NotFound"

Cause: AMIs are region-specific. The ID ami-04b4f1a9cf54c11d0 is for us-east-1.

Fix: If you changed the region to us-west-2, you must find the matching Ubuntu AMI ID for that region.