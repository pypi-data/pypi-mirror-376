from aws_cdk import (
    aws_ecs as ecs,
    Stack,
    Fn,
    CfnOutput,
)
from constructs import Construct

class ECSServiceStack(Construct):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        *,
        ecs_stack_name: str,
        desired_count: int,
        task_definition_arn: str,
        health_check_grace_period_seconds: int,    
        container_port: int,
        target_group_arn: str,
        containername: str,
        maximum_percent: int,
        minimum_healthy_percent: int,
        **kwargs
    ):
        super().__init__(scope, construct_id, **kwargs)
        cluster_arn = Fn.import_value(Fn.sub("${ECSStackName}-ECSCluster", {"ECSStackName": ecs_stack_name}))
        if not cluster_arn:
            raise ValueError("Cluster ARN not found in CloudFormation exports")
        

        self.service = ecs.CfnService(
            self, "Service",
            cluster=cluster_arn,
            desired_count=desired_count,
            task_definition=task_definition_arn,
            health_check_grace_period_seconds=health_check_grace_period_seconds,
            placement_constraints=[
                ecs.CfnService.PlacementConstraintProperty(
                    type="distinctInstance"
                )
            ],
            placement_strategies=[
                ecs.CfnService.PlacementStrategyProperty(
                    type="spread",
                    field="attribute:ecs.availability-zone"
                ),
                ecs.CfnService.PlacementStrategyProperty(
                    type="binpack",
                    field="memory"
                )
            ],
            deployment_configuration=ecs.CfnService.DeploymentConfigurationProperty(
                maximum_percent=maximum_percent, 
                minimum_healthy_percent=minimum_healthy_percent,
                deployment_circuit_breaker=ecs.CfnService.DeploymentCircuitBreakerProperty(
                    enable=True,
                    rollback=True
                )
            ),
            deployment_controller=ecs.CfnService.DeploymentControllerProperty(
                type="ECS"
            ),
            enable_execute_command=True,
            load_balancers=[
                ecs.CfnService.LoadBalancerProperty(
                    container_name=containername,
                    container_port=container_port,
                    target_group_arn=target_group_arn
                )
            ]
        )
        CfnOutput(
            self, "ECSServiceARN",
            value=str(self.service.attr_service_arn),
            export_name=f"{Stack.of(self).stack_name}-ECSServiceARN",
            description="ARN of the ECS Service"
        )