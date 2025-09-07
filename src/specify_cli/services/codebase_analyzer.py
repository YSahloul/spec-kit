"""
CodebaseAnalyzer service
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class CodebaseAnalyzer:
    """Service for analyzing existing codebases"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)

    def analyze_codebase(
        self,
        path: Optional[str] = None,
        depth: str = "deep"
    ) -> Dict[str, Any]:
        """Analyze an existing codebase"""
        target_path = Path(path) if path else self.base_path

        if not target_path.exists():
            return {
                "error": f"Path {target_path} does not exist",
                "features_found": 0,
                "structure": {},
                "recommendations": []
            }

        # Analyze structure
        structure = self._analyze_structure(target_path, depth)

        # Find features
        features = self._identify_features(target_path, structure)

        # Generate recommendations
        recommendations = self._generate_recommendations(features, structure)

        return {
            "features_found": len(features),
            "structure": structure,
            "recommendations": recommendations,
            "migration_ready": len(features) > 0,
            "analyzed_at": datetime.now().isoformat()
        }

    def _analyze_structure(self, path: Path, depth: str) -> Dict[str, Any]:
        """Analyze the directory structure"""
        structure = {
            "directories": 0,
            "files": 0,
            "languages": {},
            "file_types": {}
        }

        max_depth = 3 if depth == "shallow" else 10 if depth == "deep" else 50

        for root, dirs, files in os.walk(path):
            current_depth = len(Path(root).relative_to(path).parts)
            if current_depth > max_depth:
                continue

            structure["directories"] += len(dirs)
            structure["files"] += len(files)

            # Analyze file types and languages
            for file in files:
                ext = Path(file).suffix.lower()
                if ext:
                    structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1

                # Simple language detection
                if ext in [".py", ".pyw"]:
                    structure["languages"]["python"] = structure["languages"].get("python", 0) + 1
                elif ext in [".js", ".ts", ".jsx", ".tsx"]:
                    structure["languages"]["javascript"] = structure["languages"].get("javascript", 0) + 1
                elif ext in [".java"]:
                    structure["languages"]["java"] = structure["languages"].get("java", 0) + 1
                elif ext in [".go"]:
                    structure["languages"]["go"] = structure["languages"].get("go", 0) + 1

        return structure

    def _identify_features(self, path: Path, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify features in the codebase"""
        features = []

        # Look for common patterns
        if structure["languages"].get("python", 0) > 0:
            features.append({
                "type": "language",
                "name": "Python",
                "files": structure["languages"]["python"]
            })

        if structure["languages"].get("javascript", 0) > 0:
            features.append({
                "type": "language",
                "name": "JavaScript/TypeScript",
                "files": structure["languages"]["javascript"]
            })

        # Look for configuration files
        config_files = ["package.json", "pyproject.toml", "requirements.txt", "Dockerfile"]
        for config in config_files:
            if (path / config).exists():
                features.append({
                    "type": "configuration",
                    "name": config,
                    "path": str(path / config)
                })

        # Look for test directories
        test_dirs = ["tests", "test", "spec", "__tests__"]
        for test_dir in test_dirs:
            if (path / test_dir).exists():
                features.append({
                    "type": "testing",
                    "name": f"{test_dir} directory",
                    "path": str(path / test_dir)
                })

        return features

    def _generate_recommendations(self, features: List[Dict[str, Any]], structure: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        # Language-specific recommendations
        if any(f["name"] == "Python" for f in features):
            recommendations.append("Consider using modern Python patterns and type hints")
            recommendations.append("Set up virtual environment and dependency management")

        if any(f["name"] == "JavaScript/TypeScript" for f in features):
            recommendations.append("Consider using modern JavaScript/TypeScript features")
            recommendations.append("Set up proper build and bundling process")

        # Testing recommendations
        has_tests = any(f["type"] == "testing" for f in features)
        if not has_tests:
            recommendations.append("Add comprehensive test suite")
        else:
            recommendations.append("Expand test coverage and add integration tests")

        # Structure recommendations
        if structure["directories"] > 20:
            recommendations.append("Consider modularizing large directory structure")

        if structure["files"] > 100:
            recommendations.append("Consider breaking down large codebase into smaller modules")

        return recommendations

    def generate_migration_spec(self, analysis_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a migration specification based on analysis"""
        if not analysis_result.get("migration_ready", False):
            return None

        return {
            "title": "Codebase Migration Specification",
            "description": f"Migration specification for analyzed codebase with {analysis_result['features_found']} features",
            "structure": analysis_result["structure"],
            "recommendations": analysis_result["recommendations"],
            "generated_at": datetime.now().isoformat()
        }

    def export_analysis(self, analysis_result: Dict[str, Any], format: str = "markdown") -> str:
        """Export analysis results"""
        if format == "markdown":
            content = "# Codebase Analysis Report\n\n"

            content += f"## Summary\n"
            content += f"- Features Found: {analysis_result['features_found']}\n"
            content += f"- Migration Ready: {analysis_result['migration_ready']}\n"
            content += f"- Analyzed At: {analysis_result.get('analyzed_at', 'Unknown')}\n\n"

            content += "## Structure\n"
            structure = analysis_result.get("structure", {})
            content += f"- Directories: {structure.get('directories', 0)}\n"
            content += f"- Files: {structure.get('files', 0)}\n"

            if structure.get("languages"):
                content += "- Languages:\n"
                for lang, count in structure["languages"].items():
                    content += f"  - {lang}: {count} files\n"

            content += "\n## Recommendations\n"
            for rec in analysis_result.get("recommendations", []):
                content += f"- {rec}\n"

            return content
        else:
            return f"Analysis export in {format} format not implemented"