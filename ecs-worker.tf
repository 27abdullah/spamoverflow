resource "aws_ecs_cluster" "spamworker" {
  name = "spamworker"
}

resource "aws_ecs_task_definition" "spamworker" {
  family                   = "spamworker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = data.aws_iam_role.lab.arn

  container_definitions = <<DEFINITION
[
  {
    "image": "${aws_ecr_repository.spamoverflow.repository_url}:worker",
    "cpu": 1024,
    "memory": 2048,
    "name": "spamworker",
    "networkMode": "awsvpc",
    "portMappings": [
      {
        "containerPort": 6400,
        "hostPort": 6400
      }
    ],
    "environment": [
      {
        "name": "SQLALCHEMY_DATABASE_URI",
        "value": "postgresql://${local.database_username}:${local.database_password}@${aws_db_instance.database.address}:${aws_db_instance.database.port}/${aws_db_instance.database.db_name}"
      }, 
      {
        "name": "CELERY_BROKER_URL",
        "value": "sqs://"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/spamworker/spamworker",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs",
        "awslogs-create-group": "true"
      }
    }
  }
]
DEFINITION
}

resource "aws_ecs_service" "spamworker" {
  name            = "spamworker"
  cluster         = aws_ecs_cluster.spamworker.id
  task_definition = aws_ecs_task_definition.spamworker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets             = data.aws_subnets.private.ids
    security_groups     = [aws_security_group.spamoverflow.id]
    assign_public_ip    = true
  }

  # load_balancer {
  #   target_group_arn = aws_lb_target_group.spamoverflow.arn
  #   container_name = "spamoverflow"
  #   container_port = 6400
  # }
  # TODO: Should this be kept
}

