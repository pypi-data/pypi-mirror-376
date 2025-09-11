"""Jira connector implementation."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
from urllib.parse import urlparse  # noqa: F401 - may be used in URL handling

import requests
from requests.auth import HTTPBasicAuth  # noqa: F401 - compatibility

from qdrant_loader.config.types import SourceType
from qdrant_loader.connectors.base import BaseConnector
from qdrant_loader.connectors.jira.auth import (
    auto_detect_deployment_type as _auto_detect_type,
)
from qdrant_loader.connectors.jira.auth import setup_authentication as _setup_auth
from qdrant_loader.connectors.jira.config import JiraDeploymentType, JiraProjectConfig
from qdrant_loader.connectors.jira.mappers import (
    parse_attachment as _parse_attachment_helper,
)
from qdrant_loader.connectors.jira.mappers import parse_comment as _parse_comment_helper
from qdrant_loader.connectors.jira.mappers import parse_issue as _parse_issue_helper
from qdrant_loader.connectors.jira.mappers import parse_user as _parse_user_helper
from qdrant_loader.connectors.jira.models import (
    JiraAttachment,
    JiraComment,
    JiraIssue,
    JiraUser,
)
from qdrant_loader.connectors.shared.attachments import AttachmentReader
from qdrant_loader.connectors.shared.attachments.metadata import (
    jira_attachment_to_metadata,
)
from qdrant_loader.connectors.shared.http import (
    RateLimiter,
)
from qdrant_loader.connectors.shared.http import (
    request_with_policy as _http_request_with_policy,
)
from qdrant_loader.core.attachment_downloader import (
    AttachmentDownloader,
    AttachmentMetadata,
)
from qdrant_loader.core.document import Document
from qdrant_loader.core.file_conversion import (
    FileConversionConfig,
    FileConverter,
    FileDetector,
)
from qdrant_loader.utils.logging import LoggingConfig

logger = LoggingConfig.get_logger(__name__)


class JiraConnector(BaseConnector):
    """Jira connector for fetching and processing issues."""

    def __init__(self, config: JiraProjectConfig):
        """Initialize the Jira connector.

        Args:
            config: The Jira configuration.

        Raises:
            ValueError: If required authentication parameters are not set.
        """
        super().__init__(config)
        self.config = config
        self.base_url = str(config.base_url).rstrip("/")

        # Initialize session
        self.session = requests.Session()

        # Set up authentication based on deployment type
        self._setup_authentication()

        self._last_sync: datetime | None = None
        self._rate_limiter = RateLimiter.per_minute(self.config.requests_per_minute)
        self._initialized = False

        # Initialize file conversion components if enabled
        self.file_converter: FileConverter | None = None
        self.file_detector: FileDetector | None = None
        self.attachment_reader: AttachmentReader | None = None

        if config.enable_file_conversion:
            self.file_detector = FileDetector()
            # FileConverter will be initialized when file_conversion_config is set

        if config.download_attachments:
            self.attachment_reader = AttachmentReader(
                session=self.session,
                downloader=AttachmentDownloader(session=self.session),
            )

    def _setup_authentication(self):
        """Set up authentication based on deployment type."""
        _setup_auth(self.session, self.config)

    def _auto_detect_deployment_type(self) -> JiraDeploymentType:
        """Auto-detect the Jira deployment type based on the base URL.

        Returns:
            JiraDeploymentType: Detected deployment type
        """
        return _auto_detect_type(str(self.base_url))

    def set_file_conversion_config(self, config: FileConversionConfig) -> None:
        """Set the file conversion configuration.

        Args:
            config: File conversion configuration
        """
        if self.config.enable_file_conversion and self.file_detector:
            self.file_converter = FileConverter(config)
            if self.config.download_attachments:
                # Clean up any existing attachment reader to avoid resource leaks
                old_reader = self.attachment_reader
                if old_reader is not None:
                    try:
                        close_callable = None
                        if hasattr(old_reader, "aclose"):
                            close_callable = old_reader.aclose
                        elif hasattr(old_reader, "close"):
                            close_callable = old_reader.close
                        elif hasattr(old_reader, "cleanup"):
                            close_callable = old_reader.cleanup

                        if close_callable is not None:
                            result = close_callable()
                            if asyncio.iscoroutine(result):
                                try:
                                    # Try to schedule/await coroutine cleanup safely
                                    try:
                                        loop = asyncio.get_running_loop()
                                    except RuntimeError:
                                        loop = None
                                    if loop and not loop.is_closed():
                                        loop.create_task(result)
                                    else:
                                        asyncio.run(result)
                                except Exception:
                                    # Ignore cleanup errors to not block reconfiguration
                                    pass
                    except Exception:
                        # Ignore cleanup errors to avoid masking the config update
                        pass

                # Drop reference before creating a new reader
                self.attachment_reader = None

                # Reinitialize reader with new downloader config
                self.attachment_reader = AttachmentReader(
                    session=self.session,
                    downloader=AttachmentDownloader(
                        session=self.session,
                        file_conversion_config=config,
                        enable_file_conversion=True,
                        max_attachment_size=config.max_file_size,
                    ),
                )

    async def __aenter__(self):
        """Async context manager entry."""
        if not self._initialized:
            self._initialized = True
        return self

    async def __aexit__(self, exc_type, exc_val, _exc_tb):
        """Async context manager exit."""
        self._initialized = False

    def _get_api_url(self, endpoint: str) -> str:
        """Construct the full API URL for an endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            str: Full API URL
        """
        return f"{self.base_url}/rest/api/2/{endpoint}"

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an authenticated request to the Jira API.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            dict: Response data

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = self._get_api_url(endpoint)

        if "timeout" not in kwargs:
            kwargs["timeout"] = 60

        try:
            logger.debug(
                "Making JIRA API request",
                method=method,
                endpoint=endpoint,
                url=url,
                timeout=kwargs.get("timeout"),
            )

            if not self.session.headers.get("Authorization"):
                kwargs["auth"] = self.session.auth

            response = await _http_request_with_policy(
                self.session,
                method,
                url,
                rate_limiter=self._rate_limiter,
                retries=3,
                backoff_factor=0.5,
                status_forcelist=(429, 500, 502, 503, 504),
                overall_timeout=90.0,
                **kwargs,
            )

            response.raise_for_status()

            logger.debug(
                "JIRA API request completed successfully",
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                response_size=(
                    len(response.content) if hasattr(response, "content") else 0
                ),
            )

            return response.json()

        except TimeoutError:
            logger.error(
                "JIRA API request timed out",
                method=method,
                url=url,
                timeout=kwargs.get("timeout"),
            )
            raise requests.exceptions.Timeout(
                f"Request to {url} timed out after {kwargs.get('timeout')} seconds"
            )

        except requests.exceptions.RequestException as e:
            logger.error(
                "Failed to make request to JIRA API",
                method=method,
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )
            logger.error(
                "Request details",
                deployment_type=self.config.deployment_type,
                has_auth_header=bool(self.session.headers.get("Authorization")),
                has_session_auth=bool(self.session.auth),
            )
            raise

    def _make_sync_request(self, jql: str, **kwargs):
        """
        Make a synchronous request to the Jira API, converting parameters as needed:
        - Format datetime values in JQL to 'yyyy-MM-dd HH:mm' format
        """
        # Format datetime values in JQL query
        for key, value in kwargs.items():
            if isinstance(value, datetime):
                formatted_date = value.strftime("%Y-%m-%d %H:%M")
                jql = jql.replace(f"{{{key}}}", f"'{formatted_date}'")

        # Use the new _make_request method for consistency
        params = {
            "jql": jql,
            "startAt": kwargs.get("start", 0),
            "maxResults": kwargs.get("limit", self.config.page_size),
            "expand": "changelog",
            "fields": "*all",
        }

        return asyncio.run(self._make_request("GET", "search", params=params))

    async def get_issues(
        self, updated_after: datetime | None = None
    ) -> AsyncGenerator[JiraIssue, None]:
        """
        Get all issues from Jira.

        Args:
            updated_after: Optional datetime to filter issues updated after this time

        Yields:
            JiraIssue objects
        """
        start_at = 0
        page_size = self.config.page_size
        total_issues = 0

        logger.info(
            "🎫 Starting JIRA issue retrieval",
            project_key=self.config.project_key,
            page_size=page_size,
            updated_after=updated_after.isoformat() if updated_after else None,
        )

        while True:
            jql = f'project = "{self.config.project_key}"'
            if updated_after:
                jql += f" AND updated >= '{updated_after.strftime('%Y-%m-%d %H:%M')}'"

            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": page_size,
                "expand": "changelog",
                "fields": "*all",
            }

            logger.debug(
                "Fetching JIRA issues page",
                start_at=start_at,
                page_size=page_size,
                jql=jql,
            )

            try:
                response = await self._make_request("GET", "search", params=params)
            except Exception as e:
                logger.error(
                    "Failed to fetch JIRA issues page",
                    start_at=start_at,
                    page_size=page_size,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

            if not response or not response.get("issues"):
                logger.debug(
                    "No more JIRA issues found, stopping pagination",
                    start_at=start_at,
                    total_processed=start_at,
                )
                break

            issues = response["issues"]

            # Update total count if not set
            if total_issues == 0:
                total_issues = response.get("total", 0)
                logger.info(f"🎫 Found {total_issues} JIRA issues to process")

            # Log progress every 100 issues instead of every 50
            progress_log_interval = 100

            for i, issue in enumerate(issues):
                try:
                    parsed_issue = self._parse_issue(issue)
                    yield parsed_issue

                    if (start_at + i + 1) % progress_log_interval == 0:
                        progress_percent = (
                            round((start_at + i + 1) / total_issues * 100, 1)
                            if total_issues > 0
                            else 0
                        )
                        logger.info(
                            f"🎫 Progress: {start_at + i + 1}/{total_issues} issues ({progress_percent}%)"
                        )

                except Exception as e:
                    logger.error(
                        "Failed to parse JIRA issue",
                        issue_id=issue.get("id"),
                        issue_key=issue.get("key"),
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    # Continue processing other issues instead of failing completely
                    continue

            # Check if we've processed all issues
            start_at += len(issues)
            if start_at >= total_issues:
                logger.info(
                    f"✅ Completed JIRA issue retrieval: {start_at} issues processed"
                )
                break

    def _parse_issue(self, raw_issue: dict) -> JiraIssue:
        return _parse_issue_helper(raw_issue)

    def _parse_user(
        self, raw_user: dict | None, required: bool = False
    ) -> JiraUser | None:
        return _parse_user_helper(raw_user, required)

    def _parse_attachment(self, raw_attachment: dict) -> JiraAttachment:
        return _parse_attachment_helper(raw_attachment)

    def _parse_comment(self, raw_comment: dict) -> JiraComment:
        return _parse_comment_helper(raw_comment)

    def _get_issue_attachments(self, issue: JiraIssue) -> list[AttachmentMetadata]:
        """Convert JIRA issue attachments to AttachmentMetadata objects.

        Args:
            issue: JIRA issue with attachments

        Returns:
            List of attachment metadata objects
        """
        if not self.config.download_attachments or not issue.attachments:
            return []

        attachment_metadata = [
            jira_attachment_to_metadata(att, parent_id=issue.id)
            for att in issue.attachments
        ]

        return attachment_metadata

    async def get_documents(self) -> list[Document]:
        """Fetch and process documents from Jira.

        Returns:
            List[Document]: List of processed documents
        """
        documents = []

        # Collect all issues
        issues = []
        async for issue in self.get_issues():
            issues.append(issue)

        # Convert issues to documents
        for issue in issues:
            # Build content including comments
            content_parts = [issue.summary]
            if issue.description:
                content_parts.append(issue.description)

            # Add comments to content
            for comment in issue.comments:
                content_parts.append(
                    f"\nComment by {comment.author.display_name} on {comment.created.strftime('%Y-%m-%d %H:%M')}:"
                )
                content_parts.append(comment.body)

            content = "\n\n".join(content_parts)

            base_url = str(self.config.base_url).rstrip("/")
            document = Document(
                id=issue.id,
                content=content,
                content_type="text",
                source=self.config.source,
                source_type=SourceType.JIRA,
                created_at=issue.created,
                url=f"{base_url}/browse/{issue.key}",
                title=issue.summary,
                updated_at=issue.updated,
                is_deleted=False,
                metadata={
                    "project": self.config.project_key,
                    "issue_type": issue.issue_type,
                    "status": issue.status,
                    "key": issue.key,
                    "priority": issue.priority,
                    "labels": issue.labels,
                    "reporter": issue.reporter.display_name if issue.reporter else None,
                    "assignee": issue.assignee.display_name if issue.assignee else None,
                    "created": issue.created.isoformat(),
                    "updated": issue.updated.isoformat(),
                    "parent_key": issue.parent_key,
                    "subtasks": issue.subtasks,
                    "linked_issues": issue.linked_issues,
                    "comments": [
                        {
                            "id": comment.id,
                            "body": comment.body,
                            "created": comment.created.isoformat(),
                            "updated": (
                                comment.updated.isoformat() if comment.updated else None
                            ),
                            "author": (
                                comment.author.display_name if comment.author else None
                            ),
                        }
                        for comment in issue.comments
                    ],
                    "attachments": (
                        [
                            {
                                "id": att.id,
                                "filename": att.filename,
                                "size": att.size,
                                "mime_type": att.mime_type,
                                "created": att.created.isoformat(),
                                "author": (
                                    att.author.display_name if att.author else None
                                ),
                            }
                            for att in issue.attachments
                        ]
                        if issue.attachments
                        else []
                    ),
                },
            )
            documents.append(document)
            logger.debug(
                "Jira document created",
                document_id=document.id,
                source_type=document.source_type,
                source=document.source,
                title=document.title,
            )

            # Process attachments if enabled
            if self.config.download_attachments and self.attachment_reader:
                attachment_metadata = self._get_issue_attachments(issue)
                if attachment_metadata:
                    logger.info(
                        "Processing attachments for JIRA issue",
                        issue_key=issue.key,
                        attachment_count=len(attachment_metadata),
                    )

                    attachment_documents = (
                        await self.attachment_reader.fetch_and_process(
                            attachment_metadata, document
                        )
                    )
                    documents.extend(attachment_documents)

                    logger.debug(
                        "Processed attachments for JIRA issue",
                        issue_key=issue.key,
                        processed_count=len(attachment_documents),
                    )

        return documents
