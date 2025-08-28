output "cluster_id" {
  description = "ECS Cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "ECS Cluster Name"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ECS Cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

output "service_id" {
  description = "ECS Service ID"
  value       = aws_ecs_service.main.id
}

output "service_name" {
  description = "ECS Service Name"
  value       = aws_ecs_service.main.name
}

output "service_arn" {
  description = "ECS Service ARN"
  value       = aws_ecs_service.main.id
}

output "task_definition_arn" {
  description = "ECS Task Definition ARN"
  value       = aws_ecs_task_definition.main.arn
}

output "task_definition_family" {
  description = "ECS Task Definition Family"
  value       = aws_ecs_task_definition.main.family
}

output "log_group_name" {
  description = "CloudWatch Log Group Name"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "log_group_arn" {
  description = "CloudWatch Log Group ARN"
  value       = aws_cloudwatch_log_group.ecs.arn
}

output "security_group_id" {
  description = "ECS Security Group ID"
  value       = aws_security_group.ecs.id
}

output "security_group_arn" {
  description = "ECS Security Group ARN"
  value       = aws_security_group.ecs.arn
}
