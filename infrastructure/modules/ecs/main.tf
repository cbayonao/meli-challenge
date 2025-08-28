# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "meli-crawler-cluster-${var.environment}"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = merge(var.tags, {
    Name = "meli-crawler-cluster-${var.environment}"
  })
}

# ECS Service
resource "aws_ecs_service" "main" {
  name            = "meli-crawler-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = var.subnets
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
  
  # Auto scaling
  dynamic "capacity_provider_strategy" {
    for_each = var.enable_auto_scaling ? [1] : []
    content {
      capacity_provider = "FARGATE_SPOT"
      weight           = 1
    }
  }
  
  # Load balancer configuration (if ALB is enabled)
  dynamic "load_balancer" {
    for_each = var.load_balancer_target_group_arn != null ? [1] : []
    content {
      target_group_arn = var.load_balancer_target_group_arn
      container_name   = "meli-crawler"
      container_port   = 8000
    }
  }
  
  depends_on = [aws_ecs_task_definition.main]
  
  tags = merge(var.tags, {
    Name = "meli-crawler-service-${var.environment}"
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "main" {
  family                   = "meli-crawler-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn           = var.task_role_arn
  
  container_definitions = jsonencode([
    {
      name  = "meli-crawler"
      image = var.container_image
      
      essential = true
      
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "SCRAPY_LOG_LEVEL"
          value = var.environment == "production" ? "INFO" : "DEBUG"
        },
        {
          name  = "SCRAPY_CONCURRENT_REQUESTS"
          value = var.environment == "production" ? "16" : "8"
        },
        {
          name  = "SCRAPY_DOWNLOAD_DELAY"
          value = var.environment == "production" ? "1" : "2"
        },
        {
          name  = "MAX_PAGES"
          value = var.environment == "production" ? "20" : "5"
        },
        {
          name  = "MAX_ITEMS"
          value = var.environment == "production" ? "2000" : "100"
        },
        {
          name  = "MAX_BATCHES"
          value = var.environment == "production" ? "100" : "10"
        },
        {
          name  = "MAX_MESSAGES_PER_BATCH"
          value = var.environment == "production" ? "10" : "5"
        },
        {
          name  = "MAX_RETRIES"
          value = var.environment == "production" ? "3" : "2"
        }
      ]
      
      secrets = [
        {
          name      = "AWS_ACCESS_KEY_ID"
          valueFrom = "${var.secrets_arn_prefix}/aws-access-key-id"
        },
        {
          name      = "AWS_SECRET_ACCESS_KEY"
          valueFrom = "${var.secrets_arn_prefix}/aws-secret-access-key"
        },
        {
          name      = "DYNAMODB_TABLE_NAME"
          valueFrom = "${var.secrets_arn_prefix}/dynamodb-table-name"
        },
        {
          name      = "SQS_QUEUE_URL"
          valueFrom = "${var.secrets_arn_prefix}/sqs-queue-url"
        },
        {
          name      = "ZYTE_API_KEY"
          valueFrom = "${var.secrets_arn_prefix}/zyte-api-key"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "python healthcheck.py"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 40
      }
    }
  ])
  
  tags = merge(var.tags, {
    Name = "meli-crawler-task-def-${var.environment}"
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/meli-crawler-${var.environment}"
  retention_in_days = var.environment == "production" ? 30 : 7
  
  tags = merge(var.tags, {
    Name = "meli-crawler-logs-${var.environment}"
  })
}

# Security Group for ECS
resource "aws_security_group" "ecs" {
  name_prefix = "meli-crawler-ecs-${var.environment}-"
  vpc_id      = var.vpc_id
  
  # Allow outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.tags, {
    Name = "meli-crawler-ecs-sg-${var.environment}"
  })
}

# Auto Scaling (if enabled)
resource "aws_appautoscaling_target" "ecs" {
  count              = var.enable_auto_scaling ? 1 : 0
  
  max_capacity       = var.max_count
  min_capacity       = var.min_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# CPU-based auto scaling
resource "aws_appautoscaling_policy" "cpu" {
  count              = var.enable_auto_scaling ? 1 : 0
  
  name               = "cpu-auto-scaling-${var.environment}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs[0].service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = var.scaling_cpu_target
  }
}

# Memory-based auto scaling
resource "aws_appautoscaling_policy" "memory" {
  count              = var.enable_auto_scaling ? 1 : 0
  
  name               = "memory-auto-scaling-${var.environment}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs[0].service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = var.scaling_memory_target
  }
}

# Data sources
data "aws_region" "current" {}
