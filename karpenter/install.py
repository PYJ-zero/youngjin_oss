import os
import subprocess
import json

# 사용자가 입력해야 하는 변수들
CLUSTER_NAME = '{your-cluster-name}'  # EKS 클러스터 이름
KARPENTER_VERSION = 'v0.33.0'  #v0.33.0이 2023.12기준 최신

# AWS CLI를 사용하여 필요한 정보를 가져옵니다.
def setup_environment():
    os.environ['CLUSTER_ENDPOINT'] = subprocess.getoutput(
        f"aws eks describe-cluster --name {CLUSTER_NAME} --query 'cluster.endpoint' --output text")
    os.environ['AWS_ACCOUNT_ID'] = subprocess.getoutput(
        "aws sts get-caller-identity --query 'Account' --output text")

# KarpenterInstanceNodeRole IAM 역할 생성 및 정책 연결
def create_karpenter_node_role():
    role_name = 'KarpenterInstanceNodeRole'
    
    # IAM 역할 생성
    create_role_command = [
        'aws', 'iam', 'create-role', '--role-name', role_name,
        '--assume-role-policy-document', json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }]
        })
    ]
    subprocess.run(create_role_command)

    # 필요한 정책 연결
    policies = [
        'AmazonEKSWorkerNodePolicy',
        'AmazonEKS_CNI_Policy',
        'AmazonEC2ContainerRegistryReadOnly',
        'AmazonSSMManagedInstanceCore'
    ]
    for policy in policies:
        attach_policy_command = [
            'aws', 'iam', 'attach-role-policy', '--role-name', role_name,
            '--policy-arn', f'arn:aws:iam::aws:policy/{policy}'
        ]
        subprocess.run(attach_policy_command)
    pass

# KarpenterControllerRole IAM 역할 생성
def create_karpenter_controller_role():
    controller_policy = {
        "Statement": [
        {
            "Action": [
                "ssm:GetParameter",
                "iam:PassRole",
                "ec2:DescribeImages",
                "ec2:RunInstances",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeLaunchTemplates",
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceTypes",
               "ec2:DescribeInstanceTypeOfferings",
                "ec2:DescribeAvailabilityZones",
                "ec2:DeleteLaunchTemplate",
                "ec2:CreateTags",
                "ec2:CreateLaunchTemplate",
                "ec2:CreateFleet",
                "ec2:DescribeSpotPriceHistory",
                "pricing:GetProducts"
            ],
            "Effect": "Allow",
            "Resource": "*",
            "Sid": "Karpenter"
        },
        {
            "Action": "ec2:TerminateInstances",
            "Condition": {
                "StringLike": {
                    "ec2:ResourceTag/Name": "*karpenter*"
                }
            },
            "Effect": "Allow",
            "Resource": "*",
            "Sid": "ConditionalEC2Termination"
        }
        ],
        "Version": "2012-10-17"
    }

    with open('controller-policy.json', 'w') as file:
        json.dump(controller_policy, file)

    # AWS CLI를 사용하여 IAM 정책 생성
    subprocess.run([
        'aws', 'iam', 'create-policy', '--policy-name', f'KarpenterControllerPolicy-{CLUSTER_NAME}',
        '--policy-document', 'file://controller-policy.json'
    ])

    # eksctl을 사용하여 클러스터용 IAM OIDC ID 공급자 생성
    subprocess.run([
        'eksctl', 'utils', 'associate-iam-oidc-provider', '--cluster', CLUSTER_NAME, '--approve'
    ])

    # eksctl을 사용하여 Karpenter 컨트롤러의 IAM 역할 생성
    subprocess.run([
        'eksctl', 'create', 'iamserviceaccount', '--cluster', CLUSTER_NAME, '--name', 'karpenter',
        '--namespace', 'karpenter', '--role-name', f'KarpenterControllerRole-{CLUSTER_NAME}',
        '--attach-policy-arn', f'arn:aws:iam::{os.environ["AWS_ACCOUNT_ID"]}:policy/KarpenterControllerPolicy-{CLUSTER_NAME}',
        '--role-only', '--approve'
    ])

# 서브넷 및 보안 그룹에 태그 추가
def tag_subnets_and_security_groups():
    # 클러스터의 모든 노드 그룹에 대한 서브넷 ID를 얻습니다.
    nodegroups_output = subprocess.getoutput(
        f"aws eks list-nodegroups --cluster-name {CLUSTER_NAME} --query 'nodegroups' --output text")
    nodegroups = nodegroups_output.split()

    # 각 노드 그룹의 서브넷에 태그를 추가합니다.
    for nodegroup in nodegroups:
        subnets_output = subprocess.getoutput(
            f"aws eks describe-nodegroup --cluster-name {CLUSTER_NAME} "
            f"--nodegroup-name {nodegroup} --query 'nodegroup.subnets' --output text")
        subnets = subnets_output.split()
        for subnet in subnets:
            subprocess.run(
                ['aws', 'ec2', 'create-tags', '--tags', f"Key=karpenter.sh/discovery,Value={CLUSTER_NAME}",
                 '--resources', subnet])

    # 첫 번째 노드 그룹을 가져옵니다.
    first_nodegroup = subprocess.getoutput(
        f"aws eks list-nodegroups --cluster-name {CLUSTER_NAME} --query 'nodegroups[0]' --output text")

    # 첫 번째 노드 그룹의 Launch Template 정보를 가져옵니다.
    launch_template_info = subprocess.getoutput(
        f"aws eks describe-nodegroup --cluster-name {CLUSTER_NAME} "
        f"--nodegroup-name {first_nodegroup} --query 'nodegroup.launchTemplate' --output text")
    
    if launch_template_info and 'id' in launch_template_info:
        # Launch Template을 사용하는 경우
        launch_template_id, launch_template_version = launch_template_info.split(',')
        security_groups_output = subprocess.getoutput(
            f"aws ec2 describe-launch-template-versions "
            f"--launch-template-id {launch_template_id} --versions {launch_template_version} "
            f"--query 'LaunchTemplateVersions[0].LaunchTemplateData.NetworkInterfaces[0].Groups' --output text")
    else:
        # Cluster 보안 그룹만 사용하는 경우
        security_groups_output = subprocess.getoutput(
            f"aws eks describe-cluster --name {CLUSTER_NAME} "
            f"--query 'cluster.resourcesVpcConfig.clusterSecurityGroupId' --output text")

    security_groups = security_groups_output.split()
    for sg in security_groups:
        if sg:
            subprocess.run(
                ['aws', 'ec2', 'create-tags', '--tags', f"Key=karpenter.sh/discovery,Value={CLUSTER_NAME}",
                 '--resources', sg])
    pass

def main():
    setup_environment()
#    create_karpenter_node_role()
#    create_karpenter_controller_role()
    tag_subnets_and_security_groups()

    print("Karpenter 배포 자동화 스크립트 완료")

if __name__ == "__main__":
    main()

