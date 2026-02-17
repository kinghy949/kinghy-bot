"""提示词构建器"""


def build_feature_prompt(software_name: str, description: str) -> str:
    return (
        "为Web管理系统生成6个功能模块，返回JSON数组，每个元素包含"
        "name, description, page_type, operation_steps。"
        f"软件名：{software_name}。项目描述：{description}。"
    )
