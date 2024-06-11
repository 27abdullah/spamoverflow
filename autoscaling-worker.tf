resource "aws_appautoscaling_target" "spamworker" {
    max_capacity = 15
    min_capacity = 5
    resource_id = "service/spamworker/spamworker"
    scalable_dimension = "ecs:service:DesiredCount"
    service_namespace = "ecs"

    depends_on = [
        aws_ecs_service.spamworker
    ]
}

resource "aws_appautoscaling_policy" "spamworker-cpu" {
    name = "spamworker-cpu"
    policy_type = "TargetTrackingScaling"
    resource_id = aws_appautoscaling_target.spamworker.resource_id
    scalable_dimension = aws_appautoscaling_target.spamworker.scalable_dimension
    service_namespace = aws_appautoscaling_target.spamworker.service_namespace
    
    target_tracking_scaling_policy_configuration {
        
        predefined_metric_specification {
            predefined_metric_type = "ECSServiceAverageCPUUtilization"
        }
        
        target_value = 20
    }
}