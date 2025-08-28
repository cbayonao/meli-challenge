variable "environment" {
  description = "Environment name (staging, production)"
  type        = string
  default     = "staging"
  
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
  default     = "meli-crawler-items"
}

variable "sqs_queue_name" {
  description = "SQS queue name"
  type        = string
  default     = "meli-crawler-queue"
}

variable "enable_alb" {
  description = "Enable Application Load Balancer"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "SSL certificate ARN"
  type        = string
  default     = ""
}

variable "ecs_cpu" {
  description = "ECS task CPU units"
  type        = number
  default     = 512
}

variable "ecs_memory" {
  description = "ECS task memory in MiB"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "ECS service desired count"
  type        = number
  default     = 1
}

variable "ecs_max_count" {
  description = "ECS service maximum count"
  type        = number
  default     = 3
}

variable "ecs_min_count" {
  description = "ECS service minimum count"
  type        = number
  default     = 1
}

variable "enable_auto_scaling" {
  description = "Enable ECS auto scaling"
  type        = bool
  default     = true
}

variable "scaling_cpu_target" {
  description = "CPU utilization target for auto scaling"
  type        = number
  default     = 70
}

variable "scaling_memory_target" {
  description = "Memory utilization target for auto scaling"
  type        = number
  default     = 80
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
