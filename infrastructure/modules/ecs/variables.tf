variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnets" {
  description = "Subnet IDs for ECS service"
  type        = list(string)
}

variable "container_image" {
  description = "Container image URI"
  type        = string
  default     = "ghcr.io/OWNER/meli-challenge:latest"
}

variable "cpu" {
  description = "CPU units for the task"
  type        = number
  default     = 512
}

variable "memory" {
  description = "Memory for the task in MiB"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 1
}

variable "min_count" {
  description = "Minimum number of tasks for auto scaling"
  type        = number
  default     = 1
}

variable "max_count" {
  description = "Maximum number of tasks for auto scaling"
  type        = number
  default     = 3
}

variable "execution_role_arn" {
  description = "ECS execution role ARN"
  type        = string
}

variable "task_role_arn" {
  description = "ECS task role ARN"
  type        = string
}

variable "secrets_arn_prefix" {
  description = "Secrets Manager ARN prefix"
  type        = string
}

variable "enable_auto_scaling" {
  description = "Enable auto scaling"
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

variable "load_balancer_target_group_arn" {
  description = "Load balancer target group ARN"
  type        = string
  default     = null
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
