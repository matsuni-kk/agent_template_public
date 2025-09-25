from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path

@dataclass
class AgentConfig:
    agent_name: str
    domain: str
    description: str
    framework: str = ""
    directory_structure: Dict[str, Any] = field(default_factory=dict)
    specialized_rules: List[str] = field(default_factory=list)
    primary_workflows: List[Dict[str, Any]] = field(default_factory=list)
    required_scripts: List[str] = field(default_factory=list)
    custom_paths: Dict[str, str] = field(default_factory=dict)
    
    def validate(self):
        if not self.agent_name or not self.agent_name.strip():
            raise ValueError("agent_name is required")
        if not self.domain or not self.domain.strip():
            raise ValueError("domain is required")
        if not self.description or not self.description.strip():
            raise ValueError("description is required")
    
    def get_template_files(self) -> Dict[str, str]:
        return {
            "master_rules": f"00_master_rules_sample_{self.domain}.md",
            "paths": f"{self.domain}_paths_complete.mdc"
        }
    
    def get_directory_model(self) -> str:
        return self.directory_structure.get("model", "flow_stock")
    
    def get_stock_subdirs(self) -> List[str]:
        return self.directory_structure.get("stock_subdirs", [])

PRESET_CONFIGS = {
    "babok": AgentConfig(
        agent_name="BABOK",
        domain="babok", 
        description="BABOK (Business Analysis Body of Knowledge)に基づいたビジネスアナリシス業務を支援するエージェント",
        framework="BABOK v3",
        directory_structure={
            "model": "flow_stock",
            "stock_subdirs": [
                "documents/1_planning",
                "documents/2_elicitation",
                "documents/3_rlcm", 
                "documents/4_strategy",
                "documents/5_analysis_design",
                "documents/6_evaluation",
                "backlog/stories"
            ]
        },
        specialized_rules=[
            "babok_initialization",
            "planning_monitoring",
            "elicitation_collaboration",
            "rlcm", 
            "strategy_analysis",
            "analysis_design",
            "solution_evaluation"
        ],
        primary_workflows=[
            {
                "trigger": "BA計画書作成|ビジネスアナリシス計画書作成",
                "document_type": "BA計画書",
                "rule_reference": "planning_monitoring"
            },
            {
                "trigger": "要求仕様書作成|SRS作成",
                "document_type": "要求仕様書(SRS)", 
                "rule_reference": "analysis_design"
            }
        ],
        required_scripts=["yaml_to_stories.py"],
        custom_paths={"backlog_yaml": "{{patterns.backlog_root}}/backlog.yaml"}
    ),
    "knowledge": AgentConfig(
        agent_name="Knowledge",
        domain="knowledge",
        description="ナレッジベースの構築と管理を支援するエージェント",
        framework="Knowledge Management Framework",
        directory_structure={
            "model": "flow_stock",
            "stock_subdirs": ["articles/published", "articles/drafts", "media"]
        },
        specialized_rules=["knowledge_capture", "knowledge_curation"],
        primary_workflows=[{
            "trigger": "新規ナレッジ作成",
            "document_type": "ナレッジ記事",
            "rule_reference": "knowledge_capture"
        }]
    )
}

def get_agent_config(preset: str) -> AgentConfig:
    if preset not in PRESET_CONFIGS:
        raise ValueError(f"Preset '{preset}' not found. Available presets: {list(PRESET_CONFIGS.keys())}")
    return PRESET_CONFIGS[preset]

def list_available_configs() -> List[str]:
    return list(PRESET_CONFIGS.keys())

def create_custom_agent_config(
    agent_name: str,
    domain: str,
    description: str,
    framework: str = "",
    stock_subdirs: List[str] = None,
    specialized_rules: List[str] = None,
    primary_workflows: List[Dict[str, Any]] = None,
    required_scripts: List[str] = None,
    custom_paths: Dict[str, str] = None
) -> AgentConfig:
    stock_subdirs = stock_subdirs or [f"documents/{i}_{domain}_area_{i}" for i in range(1, 4)]
    specialized_rules = specialized_rules or [f"{domain}_initialization"]
    primary_workflows = primary_workflows or []
    required_scripts = required_scripts or []
    custom_paths = custom_paths or {}
    
    config = AgentConfig(
        agent_name=agent_name,
        domain=domain,
        description=description, 
        framework=framework,
        directory_structure={
            "model": "flow_stock",
            "stock_subdirs": stock_subdirs
        },
        specialized_rules=specialized_rules,
        primary_workflows=primary_workflows,
        required_scripts=required_scripts,
        custom_paths=custom_paths
    )
    config.validate()
    return config

def register_agent_config(preset_name: str, config: AgentConfig):
    PRESET_CONFIGS[preset_name] = config

def has_template_files(domain: str, cursor_bank_path: Path) -> bool:
    master_rules = cursor_bank_path / f"00_master_rules_sample_{domain}.md"
    paths_file = cursor_bank_path / f"{domain}_paths_complete.mdc" 
    return master_rules.exists() and paths_file.exists() 