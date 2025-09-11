from ..util import is_fuzzy_key
import json
import yaml
import os
from pathlib import Path

ASSET_MAP = {}

def get_request_path(asset_type, method):
    path = asset_type
    data = {}
    req_method = method
    
    # 获取当前的资源映射（可能来自YAML或原有配置）
    asset_map = get_resources()
    
    key = is_fuzzy_key(asset_type, value_map=asset_map)
    if key is None:
        return asset_type, req_method, data
    if "methods" in asset_map[key] and method in asset_map[key]["methods"]:
        if isinstance(asset_map[key]["methods"][method], dict):
            path = asset_map.get(key)["methods"][method]["path"]
            req_method = asset_map.get(key)["methods"][method]["method"]
            data = asset_map.get(key)["methods"][method].get("data", {})
        else:
            path = asset_map.get(key)["methods"][method]
    else:
        path = asset_map.get(key)["path"]
    return path, req_method, data


def load_yaml_config():
    """从YAML配置文件加载资源映射"""
    try:
        # 获取当前文件所在目录的上级目录，然后找到config目录
        current_dir = Path(__file__).parent
        config_dir = current_dir / "api"
        
        if not config_dir.exists():
            print(f"配置目录不存在: {config_dir}")
            return ASSET_MAP
        
        # 直接扫描配置目录中的所有YAML文件并合并
        merged_config = {}
        
        # 获取所有.yaml文件（排除config.yaml）
        yaml_files = [f for f in config_dir.glob('*.yaml') if f.name != 'config.yaml']
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    module_config = yaml.safe_load(f)
                    if module_config:
                        # 将模块配置合并到总配置中
                        merged_config.update(module_config)
            except Exception as e:
                print(f"加载配置文件 {yaml_file.name} 时出错: {e}")
        
        # 如果成功加载了YAML配置，则使用它；否则使用原有的ASSET_MAP
        if merged_config:
            return merged_config
        else:
            return ASSET_MAP
            
    except Exception as e:
        print(f"加载YAML配置时出错: {e}")
        return ASSET_MAP


def get_resources():
    """获取资源映射，优先使用YAML配置，如果加载失败则使用原有配置"""
    return load_yaml_config()


def get_resource(asset_type):
    """获取指定类型的资源配置"""
    resources = get_resources()
    return resources.get(asset_type)
