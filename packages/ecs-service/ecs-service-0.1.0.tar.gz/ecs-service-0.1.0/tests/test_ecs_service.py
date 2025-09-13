import pytest
import sys
import os
from aws_cdk import App, Stack
from aws_cdk.assertions import Template, Match
from ecs_service import ECSServiceStack


def test_ecs_service_stack_template(monkeypatch):
    class DummyFn:
        @staticmethod
        def import_value(val):
            return "dummy-cluster-arn"
        @staticmethod
        def sub(template, mapping=None):
            return template.replace("${ECSStackName}", mapping["ECSStackName"])
    monkeypatch.setattr("aws_cdk.Fn", DummyFn)

    app = App()
    stack = Stack(app, "TestStack")
    ecs_service = ECSServiceStack(
        stack, "ECSService",
        ecs_stack_name="MyStack",
        desired_count=1,
        task_definition_arn="dummy-task-def-arn",
        health_check_grace_period_seconds=60,
        container_port=80,
        target_group_arn="dummy-tg-arn",
        containername="test-container",
        maximum_percent=200,
        minimum_healthy_percent=100
    )

    template = Template.from_stack(stack)

    template.has_resource_properties("AWS::ECS::Service", {
        "Cluster": Match.any_value(),
        "DesiredCount": 1,
        "TaskDefinition": "dummy-task-def-arn",
        "HealthCheckGracePeriodSeconds": 60,
        "EnableExecuteCommand": True,
        "LoadBalancers": Match.array_with([
            Match.object_like({
                "ContainerName": "test-container",
                "ContainerPort": 80,
                "TargetGroupArn": "dummy-tg-arn"
            })
        ])
    })

    template.has_output("*", {
        "Export": Match.object_like({"Name": "TestStack-ECSServiceARN"}),
        "Description": "ARN of the ECS Service"
    })