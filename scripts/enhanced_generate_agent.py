#!/usr/bin/env python3
"""
Enhanced LLM-Driven Agent Generation Script
高度な柔軟性とスクリプト自動生成機能付き

Usage:
    # 事前定義済みエージェント
    python enhanced_generate_agent.py --preset babok
    python enhanced_generate_agent.py --preset knowledge
    
    # カスタムエージェント（柔軟設定）
    python enhanced_generate_agent.py --config-file legal_config.yaml
    
    # 完全カスタム（対話形式）
    python enhanced_generate_agent.py --interactive
"""

import os
import sys
import re
import shutil
import argparse
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field

@dataclass
class AgentConfig:
    agent_name: str = "Custom"
    domain: str = "custom"
    description: str = "Custom Domain Agent"
    directory_structure: Dict[str, Any] = field(default_factory=lambda: {"model": "flow_stock"})
    primary_workflows: List[Dict[str, Any]] = field(default_factory=list)
    specialized_rules: List[str] = field(default_factory=list)
    
    def validate(self):
        """設定の妥当性を検証"""
        if not self.agent_name or not self.domain:
            raise ValueError("Agent name and domain are required")
        if not isinstance(self.directory_structure, dict):
            raise ValueError("Directory structure must be a dictionary")

def get_agent_config(preset: str) -> AgentConfig:
    """事前定義された設定を取得"""
    presets = {
        "babok": AgentConfig(
            agent_name="BABOK",
            domain="babok", 
            description="Business Analysis Body of Knowledge Agent"
        ),
        "knowledge": AgentConfig(
            agent_name="Knowledge",
            domain="knowledge",
            description="Knowledge Management Agent"
        )
    }
    if preset not in presets:
        raise ValueError(f"Unknown preset: {preset}")
    return presets[preset]

def list_available_configs() -> List[str]:
    """利用可能な設定プリセットのリストを返す"""
    return ["babok", "knowledge"]

def create_custom_agent_config(agent_name: str, domain: str, description: str) -> AgentConfig:
    """カスタム設定を作成"""
    return AgentConfig(
        agent_name=agent_name,
        domain=domain,
        description=description
    )

class EnhancedAgentGenerator:
    def __init__(self, template_dir: str, output_base_dir: str):
        self.template_dir = Path(template_dir)
        self.output_base_dir = Path(output_base_dir)
        self.config: AgentConfig = None
        self.agent_dir: Path = None
        self.template_rules_copied: bool = False
        
    def generate_agent(self, preset: str = None, config_file: str = None, interactive: bool = False,
                         agent_name: str = None, domain: str = None, description: str = None,
                         dir_model: str = 'flow_stock'):
        """エージェント生成のメインフロー"""
        print("🚀 Starting Enhanced Agent Generation...")

        try:
            # 1. 設定のロードまたは対話的作成
            if interactive:
                self.interactive_config()
            else:
                self.load_config(preset, config_file, agent_name, domain, description, dir_model)

            if not self.config:
                raise ValueError("Agent configuration could not be loaded or created.")
            
            # 設定の検証
            self._validate_config()
            
            self.agent_dir = self.output_base_dir / f"{self.config.domain}_agent"
            
            # 既存ディレクトリのチェック
            if self.agent_dir.exists():
                response = input(f"⚠️  Directory {self.agent_dir} already exists. Overwrite? (y/n): ")
                if response.lower() != 'y':
                    print("Aborted.")
                    return None
                    
            print(f"Target directory: {self.agent_dir}")

            # 2. ディレクトリ構造の作成
            self.create_enhanced_directory_structure()
            print("✓ Directory structure created.")

            # 3. テンプレート（template/agent_base）から必要資材をコピー
            self.copy_from_template_manifest()
            print("✓ Template assets applied.")

            # 5. 自動化スクリプトの生成・コピー
            self.generate_automation_scripts()
            print("✓ Automation scripts generated/copied.")

            # 6. 必須ルールファイルの生成
            self.generate_essential_rules()
            print("✓ Essential rules ready in .cursor/rules.")
            
            # 7. ドメイン固有ルールの生成
            self.generate_domain_specific_rules()
            print("✓ Domain-specific rules generated.")
            
            # 7. root.mdの生成
            self.generate_root_md()
            print("✓ root.md generated for agent.")
            
            # 8. README.mdの生成
            self.generate_readme()
            print("✓ README.md generated for agent.")

            print("\n🎉 Enhanced Agent Generation Completed Successfully!")
            return self.agent_dir
            
        except Exception as e:
            print(f"\n❌ Error during agent generation: {e}")
            raise

    def load_config(self, preset: str = None, config_file: str = None, 
                   agent_name: str = None, domain: str = None, description: str = None,
                   dir_model: str = 'flow_stock') -> AgentConfig:
        """設定をロード（柔軟な指定方法対応）"""
        if preset:
            self.config = get_agent_config(preset)
            print(f"✓ Loaded preset config: {preset}")
            
        elif config_file:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            self.config = self._dict_to_config(config_data)
            print(f"✓ Loaded custom config: {config_file}")
            
        else:
            # 基本パラメータから設定作成
            self.config = create_custom_agent_config(
                agent_name=agent_name or "Custom",
                domain=domain or "custom",
                description=description or "Custom Domain Agent"
            )
            self.config.directory_structure['model'] = dir_model
            print(f"✓ Created basic config for {agent_name} with '{dir_model}' model")
            
        return self.config
    
    def _dict_to_config(self, data: Dict[str, Any]) -> AgentConfig:
        """辞書からAgentConfigオブジェクトを作成"""
        return AgentConfig(**data)
    
    def _validate_config(self):
        if not self.config:
            raise ValueError("Configuration is not loaded")
        self.config.validate()
        if not re.match(r'^[a-zA-Z0-9_]+$', self.config.domain):
            raise ValueError(f"Domain '{self.config.domain}' must contain only alphanumeric characters and underscores")
        print("✓ Configuration validated successfully")
    
    def interactive_config(self) -> AgentConfig:
        """対話的な設定作成"""
        print("\n🔧 Interactive Agent Configuration")
        print("=" * 50)
        
        agent_name = input("Agent Name (e.g., 'Legal'): ").strip() or "Legal"
        domain = input(f"Domain identifier (e.g., 'legal'): ").strip().lower() or "legal"
        description = input("Agent description: ").strip() or f"{agent_name} Domain Agent"
        
        # ディレクトリモデル選択
        print("\n📂 Directory Model Selection")
        dir_model = input("Directory model ('flow_stock' or 'input_output') [flow_stock]: ").strip().lower() or 'flow_stock'

        # ディレクトリ構造設定
        print("\n📁 Directory Structure Configuration")
        if dir_model == 'flow_stock':
            print("Enter subdirectories for Stock (empty line to finish):")
            stock_subdirs = []
            while True:
                subdir = input("  Subdir: ").strip()
                if not subdir:
                    break
                stock_subdirs.append(subdir)
            dir_structure = {"model": dir_model, "stock_subdirs": stock_subdirs}
        else:
            dir_structure = {"model": dir_model}

        # ワークフロー設定
        print("\n🔄 Primary Workflow Configuration")
        workflows = []
        while True:
            add_workflow = input("Add workflow? (y/n) [n]: ").strip().lower()
            if add_workflow != 'y':
                break
                
            trigger = input("  Trigger pattern (e.g., '契約書レビュー依頼'): ").strip()
            doc_type = input("  Document type (e.g., '契約書レビュー結果'): ").strip()
            rule_ref_input = input(f"  Rule reference (e.g., 'contract_review'): ").strip()

            if not all([trigger, doc_type, rule_ref_input]):
                print("Skipping incomplete workflow.")
                continue

            workflows.append({
                "trigger": trigger,
                "document_type": doc_type,
                "rule_reference": rule_ref_input,
                "priority": "high"
            })
        
        # 特化ルール
        print("\n📘 Specialized Rules Configuration")
        specialized_rules = []
        print("Enter specialized rule names (e.g., 'contract_review', 'compliance_check', empty line to finish):")
        while True:
            rule_name = input("  Rule name: ").strip()
            if not rule_name:
                break
            specialized_rules.append(rule_name)

        self.config = AgentConfig(
            agent_name=agent_name,
            domain=domain,
            description=description,
            directory_structure=dir_structure,
            primary_workflows=workflows,
            specialized_rules=specialized_rules,
        )
        
        return self.config
    
    def create_enhanced_directory_structure(self) -> Path:
        """設定に基づいた拡張ディレクトリ構造作成"""
        agent_dir = self.agent_dir
        dir_model = self.config.directory_structure.get("model", "flow_stock")
        
        # 基本構造
        if dir_model == "input_output":
            base_dirs = ["Input", "Output", "Archived", "scripts", ".cursor/rules", ".cursor/templates"]
        else: # Default to flow_stock
            base_dirs = [
                "Flow/Public",
                "Flow/Private", 
                "Stock",
                "Archived",
                "scripts",
                ".cursor/rules",
                ".cursor/templates"
            ]
        
        for dir_path in base_dirs:
            (agent_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        # カスタムディレクトリ構造
        if dir_model == "flow_stock" and "stock_subdirs" in self.config.directory_structure:
            for subdir in self.config.directory_structure["stock_subdirs"]:
                # 変数を実際の値に置換（例: {project_id} → sample_project）
                expanded_subdir = subdir.replace("{project_id}", "sample_project")
                expanded_subdir = expanded_subdir.replace("{campaign_id}", "sample_campaign")
                expanded_subdir = expanded_subdir.replace("{contract_type}", "sample_contract")
                (agent_dir / "Stock" / expanded_subdir).mkdir(parents=True, exist_ok=True)
        
        if "areas_subdirs" in self.config.directory_structure:
            for subdir in self.config.directory_structure["areas_subdirs"]:
                expanded_subdir = subdir.replace("{industry_type}", "sample_industry")
                (agent_dir / "02_Areas" / expanded_subdir).mkdir(parents=True, exist_ok=True)
        
        # keep ファイル作成
        if dir_model == "input_output":
            keep_dirs = ["Input", "Output", "Archived"]
        else:
            keep_dirs = ["Flow", "Stock", "Archived"]
            
        for keep_dir in keep_dirs:
            if (agent_dir / keep_dir).exists():
                (agent_dir / keep_dir / "keep").touch()
            
        return agent_dir
    
    def generate_enhanced_paths_file(self):
        """現状: pathsはテンプレ配布のrules内（agent_paths.mdc等）を使用"""
        return
    
    def generate_specialized_rules(self):
        """特化ルールはテンプレ`rules`に含める方針のため、この段階では生成しない"""
        return
    
    def generate_automation_scripts(self):
        """テンプレコピーのみを尊重し、追加配布/自動生成は行わない"""
        # 以前はリポジトリ直下`scripts`から汎用スクリプトを追加コピーしていたが、
        # テンプレート厳守のため本関数は何もしない。
        # 既存の変換スクリプトカスタマイズもテンプレに存在しない限り行わない。
        return

    def generate_essential_rules(self):
        target_rules_dir = self.agent_dir / ".cursor" / "rules"
        target_rules_dir.mkdir(parents=True, exist_ok=True)
        # テンプレ側ルールをコピー済みなら生成をスキップ
        if self.template_rules_copied or (target_rules_dir / "00_master_rules.mdc").exists():
            print("✓ Essential rules detected from template. Generation skipped.")
            return
        
        domain = self.config.domain
        agent_name = self.config.agent_name
        
        # 00_master_rules.mdc (Rules Master Spec)
        master_rules_content = f"""---
description: "{agent_name} Agent Master Rules"
globs:
alwaysApply: true
---
path_reference: "{domain}_paths.mdc"

# =========================
# AI注意事項 - AIが確実に守るべき指示
# =========================
ai_instructions:
  - "定義済みのステップとパスを変更せず正確に実行すること"
  - "execute_shellコマンドは改変せず、そのまま実行すること"
  - ".cursor/rules と paths の整合性を保ち、構造を勝手に変えないこと"
  - "失敗時は代替せず、失敗内容を報告しユーザー指示を仰ぐこと"

# ==========================================================
# 00_master_rules.mdc - {agent_name} マスタールール
# ==========================================================

master_triggers:
  # 例: ドメイン固有ルールはここに追加
  # - trigger: "({domain}特有のトリガー)"
  #   priority: high
  #   steps:
  #     - name: "collect_existing_info"
  #       action: "gather_existing_info"
  #     - name: "ask_questions"
  #       action: "call 01_{domain}_something.mdc => something_questions"

  # =========================
  # A-01-90. Task Management Rules
  # =========================
  - trigger: "(今日のタスク作成|daily task|task作成)"
    priority: medium
    steps:
      - name: "create_daily_task"
        action: "call 90_task_management.mdc => create_daily_task"

  # =========================
  # A-01-97. Flow to Stock Rules
  # =========================
  - trigger: "(Flow確定|Stock移動|確定版作成)"
    priority: medium
    steps:
      - name: "move_to_stock"
        action: "call 97_flow_to_stock_rules.mdc => flow_to_stock_process"

  # =========================
  # A-01-98. Flow Assist Rules
  # =========================
  - trigger: "(Flow支援|作業支援|draft支援)"
    priority: low
    steps:
      - name: "flow_assist"
        action: "call 98_flow_assist.mdc => provide_flow_assistance"

  # =========================
  # A-01-99. Rule Maintenance
  # =========================
  - trigger: "(ルール更新|rule update|ルールメンテナンス)"
    priority: low
    steps:
      - name: "rule_maintenance"
        action: "call 99_rule_maintenance.mdc => maintain_rules"
"""
        
        # パスファイル
        paths_content = f"""---
description: "{agent_name} Agent Path Dictionary"
globs:
alwaysApply: true
---

# {agent_name} Agent Paths

root: "/Users/username/workspace/{domain}_agent"

dirs:
  flow: "{{{{root}}}}/Flow"
  flow_public: "{{{{flow}}}}/Public"
  flow_private: "{{{{flow}}}}/Private"
  stock: "{{{{root}}}}/Stock"
  archived: "{{{{root}}}}/Archived"
  docs_root: "{{{{stock}}}}/documents"

patterns:
  flow_public_date: "{{{{flow_public}}}}/{{{{env.NOW:date:YYYY-MM-DD}}}}"
  draft_document: "{{{{flow_public_date}}}}/draft_{{{{document_name}}}}.md"
  stock_document: "{{{{docs_root}}}}/{{{{document_name}}}}.md"

meta:
  agent_name: "{agent_name}"
  domain: "{domain}"
"""
        
        (target_rules_dir / "00_master_rules.mdc").write_text(master_rules_content, encoding='utf-8')
        (target_rules_dir / f"{domain}_paths.mdc").write_text(paths_content, encoding='utf-8')
        
        # 他の必須ルール
        self._generate_common_rules(target_rules_dir, domain, agent_name)
    
    def generate_domain_specific_rules(self):
        """ドメイン固有ルールを生成しない（01〜のファイルは作成しない）"""
        # 01〜のルールファイルは作成しないように変更
        pass
    
    def _generate_common_rules(self, target_dir: Path, domain: str, agent_name: str):
        # 90_task_management.mdc
        task_mgmt = f"""---
description: "{agent_name} Task Management"
globs:
alwaysApply: true
---

# Task Management

create_daily_task:
  template_reference: "templates/common_templates.mdc => daily_task_template"
"""
        
        # 97_flow_to_stock_rules.mdc
        flow_stock = f"""---
description: "{agent_name} Flow to Stock Rules"
globs:
alwaysApply: true
---

# Flow to Stock Movement

flow_to_stock_process:
  steps:
    - validate_document
    - add_version_info
    - move_to_stock
    - archive_previous
  template_reference: "templates/common_templates.mdc => flow_to_stock_template"
"""
        
        # 98_flow_assist.mdc
        flow_assist = f"""---
description: "{agent_name} Flow Assistance"
globs:
alwaysApply: true
---

# Flow Assistance

provide_flow_assistance:
  template_reference: "templates/common_templates.mdc => flow_assist_template"
"""
        
        # 99_rule_maintenance.mdc
        rule_maint = f"""---
description: "{agent_name} Rule Maintenance"
globs:
alwaysApply: true
---

# Rule Maintenance

maintain_rules:
  template_reference: "templates/common_templates.mdc => rule_maintenance_template"
"""
        
        (target_dir / "90_task_management.mdc").write_text(task_mgmt, encoding='utf-8')
        (target_dir / "97_flow_to_stock_rules.mdc").write_text(flow_stock, encoding='utf-8')
        (target_dir / "98_flow_assist.mdc").write_text(flow_assist, encoding='utf-8')
        (target_dir / "99_rule_maintenance.mdc").write_text(rule_maint, encoding='utf-8')
    
    def generate_root_md(self):
        """エージェント用のroot.mdを生成"""
        domain = self.config.domain
        agent_name = self.config.agent_name
        
        root_content = f'''---
doc_type: root_directory
project_id: {domain}
created_at: {{{{env.NOW:date:YYYY-MM-DD}}}}
version: v1.0
---

# Root Directory - {agent_name} Agent

このファイルは{agent_name}エージェントのルートディレクトリを示します。

## Root Directory Path
このエージェントは独立したリポジトリとして設計されています。
クローン先のディレクトリがルートディレクトリとなります。

- Mac/Linux: `~/workspace/{domain}_agent`
- Windows: `C:\\workspace\\{domain}_agent`

## Agent Information
- **Agent Name**: {agent_name}
- **Domain**: {domain}
- **Description**: {self.config.description}

## Directory Structure
```
{domain}_agent/
├── Flow/           # 作業中のドキュメント
│   ├── Public/     # 公開可能な作業ドキュメント
│   └── Private/    # 非公開の作業ドキュメント
├── Stock/          # 確定済みドキュメント
├── Archived/       # アーカイブ
├── scripts/        # 自動化スクリプト
└── .cursor/        # Cursor設定
    └── rules/      # ルール（.mdc形式）
```

## Quick Start
1. このリポジトリをクローン
2. Cursorでこのディレクトリを開く
3. 必要に応じて `.cursor/rules/` を直接編集してルールを更新

## Specialized Features
{self._generate_specialized_features()}
'''
        
        # 追加ファイルをscripts配下に増やさない方針に合わせ、
        # root.mdはエージェント直下に出力する。
        root_file = self.agent_dir / "root.md"
        with open(root_file, 'w', encoding='utf-8') as f:
            f.write(root_content)
    
    def _generate_specialized_features(self) -> str:
        """ドメイン特化機能の説明を生成"""
        domain = self.config.domain
        
        if domain == "babok":
            return '''### BABOK特化機能
- **BA計画書作成**: `BABOKプロジェクト開始` でプロジェクトを初期化
- **要求仕様書作成**: `要求仕様書作成` で自動テンプレート生成
- **6つのナレッジエリア**: Planning, Elicitation, RLCM, Strategy, Analysis & Design, Evaluation
- **バックログ管理**: YAML形式でのストーリー管理'''
        elif domain == "knowledge":
            return '''### ナレッジ管理特化機能
- **記事作成**: `新規ナレッジ作成` で構造化された記事を作成
- **自動カテゴリ分類**: 記事を適切なディレクトリに自動配置
- **公開/下書き管理**: ドラフトから公開への昇格ワークフロー'''
        else:
            return f'''### {self.config.agent_name}特化機能
- ドメイン固有のワークフロー
- 専用のドキュメントテンプレート
- 自動化されたタスク管理'''
    
    def _customize_conversion_scripts(self):
        """変換スクリプトをエージェント用にカスタマイズ"""
        scripts_dir = self.agent_dir / "scripts"
        
        # convert_md_to_mdc.pyとconvert_mdc_to_md.pyの修正
        for script_name in ["convert_md_to_mdc.py", "convert_mdc_to_md.py"]:
            script_path = scripts_dir / script_name
            if script_path.exists():
                content = script_path.read_text(encoding='utf-8')
                
                # root.mdの参照を修正（相対パスに）
                content = content.replace(
                    'default_root_dir = os.path.dirname(script_dir)',
                    'default_root_dir = os.path.dirname(script_dir)  # Agent root directory'
                )
                
                # コメントを更新
                content = content.replace(
                    '# NOTE: テンプレート用スクリプトです。設定値を空欄のままにせず必ず更新してください。',
                    f'# {self.config.agent_name} Agent - {"MD to MDC" if "md_to_mdc" in script_name else "MDC to MD"} Conversion Script'
                )
                
                script_path.write_text(content, encoding='utf-8')
    
    def generate_readme(self):
        """エージェント用のREADME.mdを生成"""
        domain = self.config.domain
        agent_name = self.config.agent_name
        
        readme_content = f'''# {agent_name} Agent

{self.config.description}

## 概要

このリポジトリは、{agent_name}ドメインに特化したLLMエージェントシステムです。
Cursor IDEと統合して、{domain}関連のタスクを効率的に実行します。

## 主な機能

{self._generate_specialized_features()}

## セットアップ

### 1. リポジトリのクローン
```bash
git clone <repository-url> {domain}_agent
cd {domain}_agent
```

### 2. Cursor IDEでの利用
1. Cursor IDEでこのディレクトリを開く
2. `.cursor/rules/`ディレクトリに変換済みのルールが配置されています
3. エージェントが自動的に有効になります

### 3. ルールの更新（必要に応じて）
`.cursor/rules/` 配下の`.mdc`を直接編集してください。

## 使い方

### 基本的なトリガー
{self._generate_trigger_examples()}

### ディレクトリ構成
- `Flow/`: 作業中のドキュメント
- `Stock/`: 確定済みドキュメント
- `.cursor/rules/`: ルール（Cursor用）

## カスタマイズ

### ルールの追加・編集
1. `.cursor/rules/`内の`.mdc`ファイルを編集
2. Cursorを再起動

### 新しいワークフローの追加
`.cursor/rules/`に新しいルールファイルを作成し、必要なトリガーとアクションを定義してください。

## ライセンス

[ライセンス情報を追加]

## 貢献

[貢献ガイドラインを追加]
'''
        
        readme_file = self.agent_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def _generate_trigger_examples(self) -> str:
        """ドメイン特有のトリガー例を生成"""
        if self.config.primary_workflows:
            examples = []
            for workflow in self.config.primary_workflows[:3]:  # 最初の3つ
                trigger = workflow.get('trigger', '')
                doc_type = workflow.get('document_type', '')
                examples.append(f"- `{trigger}`: {doc_type}を作成")
            return '\n'.join(examples)
        else:
            return f"- `{self.config.domain}初期化`: プロジェクトをセットアップ"

    def copy_from_template_manifest(self, template_name: str = "agent_base"):
        """template/<name>/MANIFEST.yaml を読み取り、記載の資材をコピー"""
        template_root = self.template_dir / "template" / template_name
        manifest_path = template_root / "MANIFEST.yaml"

        # フォールバック: マニフェストなしなら既定のディレクトリをコピー（cursor_bank除外）
        copy_targets = [
            {"path": ".claude", "type": "dir"},
            {"path": "scripts", "type": "dir"},
            {"path": ".cursor/templates", "type": "dir"}
        ]
        try:
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                    copy_targets = data.get('copy_targets', copy_targets)
        except Exception as e:
            print(f"⚠️  Warning: Failed to read manifest {manifest_path}: {e}. Using defaults.")

        for entry in copy_targets:
            rel = entry.get('path')
            etype = entry.get('type', 'dir')
            src = template_root / rel
            dst = self.agent_dir / rel
            try:
                if not src.exists():
                    print(f"⚠️  Skipped: template path not found: {src}")
                    continue
                if dst.exists():
                    # 既存は削除してコピー（テンプレ側が真）
                    if dst.is_dir():
                        shutil.rmtree(dst)
                    else:
                        dst.unlink()
                if etype == 'dir':
                    shutil.copytree(src, dst)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                print(f"✓ Copied from template: {rel}")
            except Exception as e:
                print(f"⚠️  Warning: Could not copy {rel} from template: {e}")

        # 追加: テンプレのルール実体がある場合は .cursor/rules に配置
        rules_dst = self.agent_dir / ".cursor" / "rules"
        primary_rules_src = template_root / ".cursor" / "templates" / "rules"
        fallback_rules_src = template_root / ".cursor" / "rules"

        rules_sources = [primary_rules_src, fallback_rules_src]
        for rules_src in rules_sources:
            if not rules_src.exists():
                continue
            try:
                if rules_dst.exists():
                    shutil.rmtree(rules_dst)
                shutil.copytree(rules_src, rules_dst)
                self.template_rules_copied = True
                self._normalize_rule_flags(rules_dst)
                print(f"✓ Copied rules from template: {rules_src} -> {rules_dst}")
                break
            except Exception as e:
                print(f"⚠️  Warning: Could not copy rules dir: {e}")

    def _normalize_rule_flags(self, rules_dir: Path):
        """テンプレートからコピーしたルールのalwaysApply設定を整える"""
        # 直接のmdcファイルとサブディレクトリ内のmdcファイルの両方を処理
        for rule_path in rules_dir.rglob('*.mdc'):
            name = rule_path.name
            target = 'true' if (name.startswith('00_') or name.endswith('_paths.mdc')) else 'false'
            lines = rule_path.read_text(encoding='utf-8').splitlines()
            
            # フロントマター内にalwaysApplyが既に存在するかチェック
            has_always_apply = False
            frontmatter_end = -1
            for idx, line in enumerate(lines):
                if line.strip() == '---' and idx > 0:
                    frontmatter_end = idx
                    break
                if idx < frontmatter_end or frontmatter_end == -1:
                    if 'alwaysApply:' in line:
                        has_always_apply = True
                        break
            if has_always_apply:
                continue
                
            for idx, line in enumerate(lines):
                if line.strip().startswith('globs:'):
                    lines.insert(idx + 1, f'alwaysApply: {target}')
                    break
            rule_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced LLM-Driven Agent Generation Script")
    parser.add_argument("--preset", choices=list_available_configs(), help="Use predefined agent configuration")
    parser.add_argument("--config-file", help="Path to custom configuration file (YAML or JSON)")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode for creating configuration")
    parser.add_argument("--agent-name", help="Agent name (e.g., 'Legal')")
    parser.add_argument("--domain", help="Domain identifier (e.g., 'legal')")
    parser.add_argument("--description", help="Agent description")
    parser.add_argument("--dir-model", choices=['flow_stock', 'input_output'], default='flow_stock', 
                       help="Directory model to use")
    
    args = parser.parse_args()
    
    # デフォルトのパス設定
    template_dir = Path(__file__).parent.parent  # agent_template directory
    output_base_dir = template_dir / "output"  # output directory
    
    generator = EnhancedAgentGenerator(template_dir, output_base_dir)
    
    try:
        agent_dir = generator.generate_agent(
            preset=args.preset,
            config_file=args.config_file,
            interactive=args.interactive,
            agent_name=args.agent_name,
            domain=args.domain,
            description=args.description,
            dir_model=args.dir_model
        )
        print(f"\n✨ Agent successfully generated at: {agent_dir}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
