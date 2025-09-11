"""Multi-project configuration parser.

This module provides parsing functionality for multi-project configurations.
"""

import re
from typing import Any

from pydantic import ValidationError

from ..utils.logging import LoggingConfig
from .global_config import GlobalConfig
from .models import ParsedConfig, ProjectConfig, ProjectsConfig
from .sources import SourcesConfig
from .validator import ConfigValidator


def _get_logger():
    return LoggingConfig.get_logger(__name__)


class MultiProjectConfigParser:
    """Parser for multi-project configurations."""

    def __init__(self, validator: ConfigValidator):
        """Initialize the parser with a validator.

        Args:
            validator: Configuration validator instance
        """
        self.validator = validator

    def parse(
        self, config_data: dict[str, Any], skip_validation: bool = False
    ) -> ParsedConfig:
        """Parse configuration with multi-project support.

        Args:
            config_data: Raw configuration data from YAML
            skip_validation: Whether to skip validation during parsing

        Returns:
            ParsedConfig: Parsed configuration with project information

        Raises:
            ValidationError: If configuration is invalid
        """
        _get_logger().debug("Starting configuration parsing")

        # Validate configuration structure
        self.validator.validate_structure(config_data)

        # Parse global configuration
        global_config = self._parse_global_config(
            config_data.get("global", {}), skip_validation
        )

        # Parse projects
        projects_config = self._parse_projects(config_data, global_config)

        _get_logger().debug(
            "Configuration parsing completed",
            project_count=len(projects_config.projects),
        )

        return ParsedConfig(
            global_config=global_config,
            projects_config=projects_config,
        )

    def _parse_global_config(
        self, global_data: dict[str, Any], skip_validation: bool = False
    ) -> GlobalConfig:
        """Parse global configuration section.

        Args:
            global_data: Global configuration data
            skip_validation: Whether to skip validation during parsing

        Returns:
            GlobalConfig: Parsed global configuration
        """
        try:
            return GlobalConfig(**global_data, skip_validation=skip_validation)
        except ValidationError as e:
            _get_logger().error("Failed to parse global configuration", error=str(e))
            raise

    def _parse_projects(
        self, config_data: dict[str, Any], global_config: GlobalConfig
    ) -> ProjectsConfig:
        """Parse project configurations.

        Args:
            config_data: Raw configuration data
            global_config: Parsed global configuration

        Returns:
            ProjectsConfig: Parsed projects configuration
        """
        projects_config = ProjectsConfig()

        # Handle multi-project format
        projects_data = config_data.get("projects", {})
        for project_id, project_data in projects_data.items():
            project_config = self._parse_project_config(
                project_id, project_data, global_config
            )
            projects_config.add_project(project_config)
            _get_logger().debug("Parsed project configuration", project_id=project_id)

        return projects_config

    def _parse_project_config(
        self, project_id: str, project_data: dict[str, Any], global_config: GlobalConfig
    ) -> ProjectConfig:
        """Parse individual project configuration.

        Args:
            project_id: Project identifier
            project_data: Project configuration data
            global_config: Global configuration

        Returns:
            ProjectConfig: Parsed project configuration
        """
        # Validate project ID
        if not self._is_valid_project_id(project_id):
            raise ValueError(
                f"Invalid project ID '{project_id}'. "
                "Project IDs must be valid Python identifiers (alphanumeric + underscores)."
            )

        # Extract basic project information
        display_name = project_data.get("display_name", project_id)
        description = project_data.get("description")
        project_data.get("collection_name")

        # Parse project-specific sources with automatic field injection
        sources_data = project_data.get("sources", {})
        enhanced_sources_data = self._inject_source_metadata(sources_data)
        sources_config = SourcesConfig(**enhanced_sources_data)

        # Extract configuration overrides
        overrides = project_data.get("overrides", {})

        # Merge project-specific overrides with global config
        merged_overrides = self._merge_configs(global_config, overrides)

        return ProjectConfig(
            project_id=project_id,
            display_name=display_name,
            description=description,
            sources=sources_config,
            overrides=merged_overrides,
        )

    def _inject_source_metadata(self, sources_data: dict[str, Any]) -> dict[str, Any]:
        """Inject source_type and source fields into source configurations.

        Args:
            sources_data: Raw sources configuration data

        Returns:
            Dict[str, Any]: Enhanced sources data with injected metadata
        """
        enhanced_data = {}

        for source_type, source_configs in sources_data.items():
            if not isinstance(source_configs, dict):
                enhanced_data[source_type] = source_configs
                continue

            enhanced_source_configs = {}
            for source_name, source_config in source_configs.items():
                if isinstance(source_config, dict):
                    # Create a copy to avoid modifying the original
                    enhanced_config = source_config.copy()

                    # Always inject source_type and source fields
                    enhanced_config["source_type"] = source_type
                    enhanced_config["source"] = source_name

                    enhanced_source_configs[source_name] = enhanced_config
                else:
                    enhanced_source_configs[source_name] = source_config

            enhanced_data[source_type] = enhanced_source_configs

        return enhanced_data

    def _is_valid_project_id(self, project_id: str) -> bool:
        """Validate project ID format.

        Args:
            project_id: Project identifier to validate

        Returns:
            bool: True if valid, False otherwise
        """
        # Project IDs must be valid Python identifiers
        # Allow alphanumeric characters, underscores, and hyphens
        pattern = r"^[a-zA-Z][a-zA-Z0-9_-]*$"
        return bool(re.match(pattern, project_id))

    def _merge_configs(
        self, global_config: GlobalConfig, project_overrides: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge project-specific overrides with global configuration.

        Args:
            global_config: Global configuration
            project_overrides: Project-specific overrides

        Returns:
            Dict[str, Any]: Merged configuration
        """
        # Convert global config to dict
        global_dict = global_config.to_dict()

        # Deep merge project overrides
        merged = self._deep_merge_dicts(global_dict, project_overrides)

        return merged

    def _deep_merge_dicts(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Dict[str, Any]: Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                result[key] = value

        return result
