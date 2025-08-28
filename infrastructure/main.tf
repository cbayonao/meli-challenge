terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "meli-challenge-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "meli-challenge"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"
  
  environment = var.environment
  vpc_cidr   = var.vpc_cidr
  azs        = var.availability_zones
}

# ECS Cluster
module "ecs" {
  source = "./modules/ecs"
  
  environment = var.environment
  vpc_id     = module.vpc.vpc_id
  subnets    = module.vpc.private_subnets
}

# DynamoDB
module "dynamodb" {
  source = "./modules/dynamodb"
  
  environment = var.environment
  table_name = var.dynamodb_table_name
}

# SQS
module "sqs" {
  source = "./modules/sqs"
  
  environment = var.environment
  queue_name = var.sqs_queue_name
}

# IAM Roles
module "iam" {
  source = "./modules/iam"
  
  environment = var.environment
  account_id = data.aws_caller_identity.current.account_id
}

# Secrets Manager
module "secrets" {
  source = "./modules/secrets"
  
  environment = var.environment
  account_id = data.aws_caller_identity.current.account_id
}

# CloudWatch Logs
module "cloudwatch" {
  source = "./modules/cloudwatch"
  
  environment = var.environment
}

# Application Load Balancer (if needed)
module "alb" {
  source = "./modules/alb"
  count  = var.enable_alb ? 1 : 0
  
  environment = var.environment
  vpc_id     = module.vpc.vpc_id
  subnets    = module.vpc.public_subnets
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "ecs_cluster_name" {
  description = "ECS Cluster Name"
  value       = module.ecs.cluster_name
}

output "dynamodb_table_name" {
  description = "DynamoDB Table Name"
  value       = module.dynamodb.table_name
}

output "sqs_queue_url" {
  description = "SQS Queue URL"
  value       = module.sqs.queue_url
}

output "ecs_service_name" {
  description = "ECS Service Name"
  value       = module.ecs.service_name
}

output "alb_dns_name" {
  description = "ALB DNS Name"
  value       = var.enable_alb ? module.alb[0].dns_name : null
}
