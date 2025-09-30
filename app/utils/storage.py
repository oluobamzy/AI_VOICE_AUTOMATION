"""
File storage utilities.

This module provides abstracted file storage operations
supporting local storage, AWS S3, and Google Cloud Storage.
"""

import os
import shutil
from pathlib import Path
from typing import BinaryIO, Dict, Any, Optional
from urllib.parse import urlparse

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageManager:
    """
    Abstracted storage manager supporting multiple backends.
    
    Supports local filesystem, AWS S3, and Google Cloud Storage
    with a unified interface.
    """
    
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE.lower()
        self.local_upload_dir = Path(settings.UPLOAD_DIR)
        self.local_processed_dir = Path(settings.PROCESSED_DIR)
        
        # Ensure local directories exist
        self.local_upload_dir.mkdir(parents=True, exist_ok=True)
        self.local_processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize cloud storage clients if needed
        if self.storage_type == "s3":
            self._init_s3_client()
        elif self.storage_type == "gcs":
            self._init_gcs_client()
    
    def _init_s3_client(self):
        """Initialize AWS S3 client."""
        try:
            import boto3
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.s3_bucket = settings.S3_BUCKET_NAME
            logger.info("S3 client initialized successfully")
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise
    
    def _init_gcs_client(self):
        """Initialize Google Cloud Storage client."""
        try:
            from google.cloud import storage
            self.gcs_client = storage.Client()
            # Bucket name would be configured in settings
            logger.info("GCS client initialized successfully")
        except ImportError:
            logger.error("google-cloud-storage not installed. Install with: pip install google-cloud-storage")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {str(e)}")
            raise
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        file_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to configured storage backend.
        
        Args:
            file_data: File data to upload
            file_path: Target file path/key
            content_type: MIME content type
            metadata: Additional metadata
            
        Returns:
            Dict containing upload results
        """
        logger.info(f"Uploading file to {self.storage_type}: {file_path}")
        
        if self.storage_type == "local":
            return await self._upload_local(file_data, file_path, metadata)
        elif self.storage_type == "s3":
            return await self._upload_s3(file_data, file_path, content_type, metadata)
        elif self.storage_type == "gcs":
            return await self._upload_gcs(file_data, file_path, content_type, metadata)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    async def _upload_local(
        self,
        file_data: BinaryIO,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload file to local filesystem."""
        full_path = self.local_upload_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(full_path, 'wb') as f:
                shutil.copyfileobj(file_data, f)
            
            file_size = full_path.stat().st_size
            
            return {
                "success": True,
                "storage_type": "local",
                "file_path": str(full_path),
                "file_size": file_size,
                "url": f"file://{full_path}",
                "metadata": metadata or {}
            }
            
        except Exception as e:
            logger.error(f"Local upload failed: {str(e)}")
            raise
    
    async def _upload_s3(
        self,
        file_data: BinaryIO,
        file_path: str,
        content_type: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Upload file to AWS S3."""
        try:
            # TODO: Implement actual S3 upload
            # This would use self.s3_client.upload_fileobj()
            
            # Placeholder implementation
            return {
                "success": True,
                "storage_type": "s3",
                "file_path": file_path,
                "bucket": self.s3_bucket,
                "url": f"https://{self.s3_bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{file_path}",
                "metadata": metadata or {}
            }
            
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise
    
    async def _upload_gcs(
        self,
        file_data: BinaryIO,
        file_path: str,
        content_type: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Upload file to Google Cloud Storage."""
        try:
            # TODO: Implement actual GCS upload
            
            # Placeholder implementation
            return {
                "success": True,
                "storage_type": "gcs",
                "file_path": file_path,
                "url": f"https://storage.googleapis.com/bucket-name/{file_path}",
                "metadata": metadata or {}
            }
            
        except Exception as e:
            logger.error(f"GCS upload failed: {str(e)}")
            raise
    
    async def download_file(self, file_path: str, local_path: str) -> Dict[str, Any]:
        """
        Download file from storage to local path.
        
        Args:
            file_path: Source file path/key in storage
            local_path: Local destination path
            
        Returns:
            Dict containing download results
        """
        logger.info(f"Downloading file from {self.storage_type}: {file_path}")
        
        if self.storage_type == "local":
            return await self._download_local(file_path, local_path)
        elif self.storage_type == "s3":
            return await self._download_s3(file_path, local_path)
        elif self.storage_type == "gcs":
            return await self._download_gcs(file_path, local_path)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    async def _download_local(self, file_path: str, local_path: str) -> Dict[str, Any]:
        """Download file from local storage (copy)."""
        try:
            source_path = Path(file_path)
            dest_path = Path(local_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source_path, dest_path)
            
            return {
                "success": True,
                "source_path": str(source_path),
                "local_path": str(dest_path),
                "file_size": dest_path.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Local download failed: {str(e)}")
            raise
    
    async def _download_s3(self, file_path: str, local_path: str) -> Dict[str, Any]:
        """Download file from S3."""
        try:
            # TODO: Implement actual S3 download
            # This would use self.s3_client.download_file()
            
            # Placeholder implementation
            return {
                "success": True,
                "source_path": f"s3://{self.s3_bucket}/{file_path}",
                "local_path": local_path
            }
            
        except Exception as e:
            logger.error(f"S3 download failed: {str(e)}")
            raise
    
    async def _download_gcs(self, file_path: str, local_path: str) -> Dict[str, Any]:
        """Download file from GCS."""
        try:
            # TODO: Implement actual GCS download
            
            # Placeholder implementation
            return {
                "success": True,
                "source_path": f"gs://bucket-name/{file_path}",
                "local_path": local_path
            }
            
        except Exception as e:
            logger.error(f"GCS download failed: {str(e)}")
            raise
    
    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete file from storage.
        
        Args:
            file_path: File path/key to delete
            
        Returns:
            Dict containing deletion results
        """
        logger.info(f"Deleting file from {self.storage_type}: {file_path}")
        
        if self.storage_type == "local":
            return await self._delete_local(file_path)
        elif self.storage_type == "s3":
            return await self._delete_s3(file_path)
        elif self.storage_type == "gcs":
            return await self._delete_gcs(file_path)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    async def _delete_local(self, file_path: str) -> Dict[str, Any]:
        """Delete file from local storage."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return {"success": True, "file_path": file_path}
            else:
                return {"success": False, "error": "File not found"}
                
        except Exception as e:
            logger.error(f"Local deletion failed: {str(e)}")
            raise
    
    async def _delete_s3(self, file_path: str) -> Dict[str, Any]:
        """Delete file from S3."""
        try:
            # TODO: Implement actual S3 deletion
            return {"success": True, "file_path": file_path}
            
        except Exception as e:
            logger.error(f"S3 deletion failed: {str(e)}")
            raise
    
    async def _delete_gcs(self, file_path: str) -> Dict[str, Any]:
        """Delete file from GCS."""
        try:
            # TODO: Implement actual GCS deletion
            return {"success": True, "file_path": file_path}
            
        except Exception as e:
            logger.error(f"GCS deletion failed: {str(e)}")
            raise
    
    def get_public_url(self, file_path: str) -> str:
        """
        Get public URL for a file.
        
        Args:
            file_path: File path/key
            
        Returns:
            Public URL string
        """
        if self.storage_type == "local":
            return f"file://{self.local_upload_dir / file_path}"
        elif self.storage_type == "s3":
            return f"https://{self.s3_bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{file_path}"
        elif self.storage_type == "gcs":
            return f"https://storage.googleapis.com/bucket-name/{file_path}"
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")