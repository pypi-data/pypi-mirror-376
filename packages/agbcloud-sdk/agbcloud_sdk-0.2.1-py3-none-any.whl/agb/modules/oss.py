import json
from typing import Any, Dict, Optional

from agb.api.base_service import BaseService
from agb.model.response import ApiResponse


class OSSClientResult(ApiResponse):
    """Result of OSS client creation operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        client_config: Optional[Dict[str, Any]] = None,
        error_message: str = "",
    ):
        """
        Initialize an OSSClientResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            client_config (Dict[str, Any], optional): OSS client configuration.
                Defaults to None.
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.client_config = client_config or {}
        self.error_message = error_message


class OSSUploadResult(ApiResponse):
    """Result of OSS upload operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        content: str = "",
        error_message: str = "",
    ):
        """
        Initialize an OSSUploadResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            content (str, optional): Result of the upload operation. Defaults to "".
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.content = content
        self.error_message = error_message


class OSSDownloadResult(ApiResponse):
    """Result of OSS download operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        content: str = "",
        error_message: str = "",
    ):
        """
        Initialize an OSSDownloadResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            content (string, optional): Defaults to "Download success"
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.content = content
        self.error_message = error_message


class Oss(BaseService):
    """
    Handles Object Storage Service operations in the AGB cloud environment.
    """

    def __init__(self, session):
        """
        Initialize an Oss object.

        Args:
            session: The Session instance that this Oss belongs to.
        """
        super().__init__(session)

    def env_init(
        self,
        access_key_id: str,
        access_key_secret: str,
        securityToken: Optional[str] = None,
        endpoint: Optional[str] = None,
        region: Optional[str] = None,
    ) -> OSSClientResult:
        """
        Create an OSS client with the provided credentials.

        Args:
            access_key_id: The Access Key ID for OSS authentication.
            access_key_secret: The Access Key Secret for OSS authentication.
            securityToken: Optional security token for temporary credentials.
            endpoint: The OSS service endpoint. If not specified, the default is used.
            region: The OSS region. If not specified, the default is used.

        Returns:
            OSSClientResult: Result object containing client configuration and error
                message if any.
        """
        try:
            args = {
                "access_key_id": access_key_id,
                "access_key_secret": access_key_secret,
                "security_token": securityToken,
            }

            # Add optional parameters if provided
            if endpoint:
                args["endpoint"] = endpoint
            if region:
                args["region"] = region

            result = self._call_mcp_tool("oss_env_init", args)
            try:
                print("Response body:")
                print(
                    json.dumps(
                        getattr(result, "body", result), ensure_ascii=False, indent=2
                    )
                )
            except Exception:
                print(f"Response: {result}")

            if result.success:
                try:
                    client_config = result.data
                    return OSSClientResult(
                        request_id=result.request_id,
                        success=True,
                        client_config=client_config,
                    )
                except json.JSONDecodeError:
                    return OSSClientResult(
                        request_id=result.request_id,
                        success=False,
                        error_message="Failed to parse client configuration JSON",
                    )
            else:
                return OSSClientResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message
                    or "Failed to initialize OSS environment",
                )
        except Exception as e:
            return OSSClientResult(
                request_id="",
                success=False,
                error_message=f"Failed to initialize OSS environment: {e}",
            )

    def upload(self, bucket: str, object: str, path: str) -> OSSUploadResult:
        """
        Upload a local file or directory to OSS.

        Args:
            bucket: OSS bucket name.
            object: Object key in OSS.
            path: Local file or directory path to upload.

        Returns:
            OSSUploadResult: Result object containing upload result and error message
                if any.
        """
        try:
            args = {"bucket": bucket, "object": object, "path": path}

            result = self._call_mcp_tool("oss_upload", args)
            print("response =", result)

            if result.success:
                return OSSUploadResult(
                    request_id=result.request_id,
                    success=True,
                    content=result.data,
                )
            else:
                return OSSUploadResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message or "Failed to upload to OSS",
                )
        except Exception as e:
            return OSSUploadResult(
                request_id="",
                success=False,
                error_message=f"Failed to upload to OSS: {e}",
            )

    def upload_anonymous(self, url: str, path: str) -> OSSUploadResult:
        """
        Upload a local file or directory to a URL anonymously.

        Args:
            url: The HTTP/HTTPS URL to upload the file to.
            path: Local file or directory path to upload.

        Returns:
            OSSUploadResult: Result object containing upload result and error message
                if any.
        """
        try:
            args = {"url": url, "path": path}

            result = self._call_mcp_tool("oss_upload_annon", args)
            print("response =", result)

            if result.success:
                return OSSUploadResult(
                    request_id=result.request_id,
                    success=True,
                    content=result.data,
                )
            else:
                return OSSUploadResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message
                    or "Failed to upload anonymously",
                )
        except Exception as e:
            return OSSUploadResult(
                request_id="",
                success=False,
                error_message=f"Failed to upload anonymously: {e}",
            )

    def download(self, bucket: str, object: str, path: str) -> OSSDownloadResult:
        """
        Download an object from OSS to a local file or directory.

        Args:
            bucket: OSS bucket name.
            object: Object key in OSS.
            path: Local file or directory path to download to.

        Returns:
            OSSDownloadResult: Result object containing download status and error
                message if any.
        """
        try:
            args = {"bucket": bucket, "object": object, "path": path}

            result = self._call_mcp_tool("oss_download", args)
            print("response =", result)

            if result.success:
                return OSSDownloadResult(
                    request_id=result.request_id,
                    success=True,
                    content=result.data,
                )
            else:
                return OSSDownloadResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message or "Failed to download from OSS",
                )
        except Exception as e:
            return OSSDownloadResult(
                request_id="",
                success=False,
                error_message=f"Failed to download from OSS: {e}",
            )

    def download_anonymous(self, url: str, path: str) -> OSSDownloadResult:
        """
        Download a file from a URL anonymously to a local file path.

        Args:
            url: The HTTP/HTTPS URL to download the file from.
            path: Local file or directory path to download to.

        Returns:
            OSSDownloadResult: Result object containing download status and error
                message if any.
        """
        try:
            args = {"url": url, "path": path}

            result = self._call_mcp_tool("oss_download_annon", args)
            print("response =", result)

            if result.success:
                return OSSDownloadResult(
                    request_id=result.request_id,
                    success=True,
                    content=result.data,
                )
            else:
                return OSSDownloadResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message
                    or "Failed to download anonymously",
                )
        except Exception as e:
            return OSSDownloadResult(
                request_id="",
                success=False,
                error_message=f"Failed to download anonymously: {e}",
            )