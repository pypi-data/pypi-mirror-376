---
title: File Upload Service
description: Handle file uploads with validation, processing, and cloud storage
---


## Overview

This example demonstrates building a comprehensive file upload service with Zenith, featuring:

- **Multiple Upload Methods** - Single file, multiple files, chunked uploads
- **File Validation** - Type, size, and content validation
- **Image Processing** - Automatic thumbnails and resizing
- **Cloud Storage** - S3-compatible storage integration
- **Progress Tracking** - Real-time upload progress
- **Metadata Extraction** - EXIF data, file analysis
- **Virus Scanning** - Optional malware detection

## Project Structure

<FileTree>
- file-upload-service/
  - app/
    - __init__.py
    - main.py              **Entry point**
    - config.py            **Configuration**
    - models/
      - file.py            **File metadata model**
      - upload.py          **Upload session model**
    - contexts/
      - uploads.py         **Upload business logic**
      - storage.py         **Storage backends**
      - processing.py      **File processing**
    - routes/
      - uploads.py         **Upload endpoints**
      - files.py           **File management**
    - services/
      - storage/
        - s3.py            **AWS S3 storage**
        - local.py         **Local file storage**
      - processing/
        - images.py        **Image processing**
        - documents.py     **Document processing**
      - validation.py      **File validation**
      - virus_scan.py      **Virus scanning**
    - static/
      - upload.html        **Upload interface**
      - upload.js          **Client code**
  - uploads/               **Local storage directory**
  - tests/
  - requirements.txt
</FileTree>

## File Models

### File Metadata Model

```python
# app/models/file.py
from zenith.db import SQLModel, Field
from sqlmodel import Relationship
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import json

class FileStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"

class FileType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    OTHER = "other"

class File(SQLModel, table=True):
    """File metadata model."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # File identification
    filename: str
    original_filename: str
    file_path: str  # Storage path/key
    file_type: FileType
    mime_type: str
    
    # File properties
    size: int = Field(ge=0)
    checksum_md5: Optional[str] = None
    checksum_sha256: Optional[str] = None
    
    # Status
    status: FileStatus = Field(default=FileStatus.UPLOADING)
    error_message: Optional[str] = None
    
    # Metadata
    metadata_json: Optional[str] = None  # JSON string of metadata
    
    # Processing results
    thumbnail_path: Optional[str] = None
    processed_variants: Optional[str] = None  # JSON array of variants
    
    # Access control
    is_public: bool = Field(default=False)
    access_token: Optional[str] = None  # For private file access
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Relationships
    uploader_id: Optional[int] = Field(foreign_key="user.id")
    uploader: Optional["User"] = Relationship()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get metadata as dict."""
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        """Set metadata from dict."""
        self.metadata_json = json.dumps(value) if value else None
    
    @property
    def variants(self) -> List[Dict[str, Any]]:
        """Get processed variants."""
        if self.processed_variants:
            return json.loads(self.processed_variants)
        return []
    
    def add_variant(self, variant: Dict[str, Any]):
        """Add a processed variant."""
        variants = self.variants
        variants.append(variant)
        self.processed_variants = json.dumps(variants)

class UploadSession(SQLModel, table=True):
    """Track multi-part/chunked uploads."""
    
    id: Optional[str] = Field(default=None, primary_key=True)  # UUID
    
    # Upload details
    filename: str
    total_size: int
    chunk_size: int = Field(default=1024*1024)  # 1MB chunks
    total_chunks: int
    uploaded_chunks: int = Field(default=0)
    
    # Status
    status: FileStatus = Field(default=FileStatus.UPLOADING)
    error_message: Optional[str] = None
    
    # Storage
    temp_path: str  # Temporary storage path
    final_file_id: Optional[int] = Field(foreign_key="file.id")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # Auto-cleanup incomplete uploads
    
    # User
    uploader_id: Optional[int] = Field(foreign_key="user.id")

# Request/Response models
class FileUploadResponse(SQLModel):
    id: int
    filename: str
    size: int
    mime_type: str
    file_type: FileType
    status: FileStatus
    download_url: str
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime

class ChunkedUploadInit(SQLModel):
    filename: str
    total_size: int = Field(gt=0)
    chunk_size: int = Field(default=1024*1024, gt=0)
    mime_type: str

class ChunkedUploadResponse(SQLModel):
    upload_id: str
    total_chunks: int
    chunk_size: int
    upload_urls: List[str]  # Pre-signed URLs for each chunk
```

## File Validation Service

```python
# app/services/validation.py
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import magic
import hashlib
from PIL import Image
from zenith import UploadFile

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    detected_mime_type: Optional[str] = None
    file_info: Dict[str, Any] = None

class FileValidator:
    """Comprehensive file validation."""
    
    def __init__(self, config: dict):
        self.config = config
        self.max_file_size = config.get('max_file_size', 100 * 1024 * 1024)  # 100MB
        self.allowed_mime_types = set(config.get('allowed_mime_types', []))
        self.blocked_extensions = set(config.get('blocked_extensions', ['.exe', '.bat', '.sh']))
        self.virus_scan_enabled = config.get('virus_scan_enabled', False)
    
    async def validate_file(
        self,
        file: UploadFile,
        content: Optional[bytes] = None
    ) -> ValidationResult:
        """Comprehensive file validation."""
        errors = []
        warnings = []
        file_info = {}
        
        # Read content if not provided
        if content is None:
            content = await file.read()
            await file.seek(0)  # Reset file pointer
        
        # File size validation
        if len(content) > self.max_file_size:
            errors.append(f"File too large: {len(content)} bytes (max: {self.max_file_size})")
        
        if len(content) == 0:
            errors.append("Empty file")
        
        # MIME type detection
        try:
            detected_mime = magic.from_buffer(content, mime=True)
            file_info['detected_mime_type'] = detected_mime
            
            # Check against allowed types
            if self.allowed_mime_types and detected_mime not in self.allowed_mime_types:
                errors.append(f"File type not allowed: {detected_mime}")
            
            # Check for mime type mismatch
            if file.content_type and file.content_type != detected_mime:
                warnings.append(
                    f"MIME type mismatch: declared {file.content_type}, detected {detected_mime}"
                )
        except Exception as e:
            errors.append(f"Could not determine file type: {str(e)}")
        
        # Extension validation
        if file.filename:
            extension = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
            if extension in self.blocked_extensions:
                errors.append(f"File extension not allowed: {extension}")
            
            file_info['extension'] = extension
        
        # Content-specific validation
        if detected_mime.startswith('image/'):
            image_info = await self._validate_image(content)
            file_info.update(image_info)
        elif detected_mime.startswith('video/'):
            video_info = await self._validate_video(content)
            file_info.update(video_info)
        
        # Calculate checksums
        file_info['md5'] = hashlib.md5(content).hexdigest()
        file_info['sha256'] = hashlib.sha256(content).hexdigest()
        
        # Virus scanning
        if self.virus_scan_enabled:
            scan_result = await self._virus_scan(content)
            if not scan_result['clean']:
                errors.append(f"Virus detected: {scan_result['threat']}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            detected_mime_type=detected_mime,
            file_info=file_info
        )
    
    async def _validate_image(self, content: bytes) -> Dict[str, Any]:
        """Image-specific validation."""
        try:
            with Image.open(io.BytesIO(content)) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
        except Exception as e:
            return {'error': f'Invalid image: {str(e)}'}
    
    async def _validate_video(self, content: bytes) -> Dict[str, Any]:
        """Video-specific validation (requires ffprobe)."""
        # Implementation would use ffprobe to extract video metadata
        return {'video_validation': 'implemented separately'}
    
    async def _virus_scan(self, content: bytes) -> Dict[str, Any]:
        """Virus scanning (requires ClamAV or similar)."""
        # Implementation would integrate with antivirus engine
        return {'clean': True, 'threat': None}
```

## Image Processing Service

```python
# app/services/processing/images.py
from PIL import Image, ImageOps, ExifTags
from typing import List, Tuple, Dict, Any, Optional
import io
import os
from dataclasses import dataclass

@dataclass
class ImageVariant:
    name: str
    width: int
    height: int
    quality: int = 85
    format: str = 'JPEG'

class ImageProcessor:
    """Advanced image processing and optimization."""
    
    def __init__(self, config: dict):
        self.config = config
        self.variants = {
            'thumbnail': ImageVariant('thumbnail', 150, 150),
            'small': ImageVariant('small', 400, 400),
            'medium': ImageVariant('medium', 800, 600),
            'large': ImageVariant('large', 1920, 1080, quality=90)
        }
    
    async def process_image(
        self,
        content: bytes,
        original_filename: str
    ) -> Dict[str, Any]:
        """Process image and create variants."""
        try:
            with Image.open(io.BytesIO(content)) as img:
                # Extract metadata
                metadata = await self._extract_metadata(img)
                
                # Auto-rotate based on EXIF
                img = ImageOps.exif_transpose(img)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Create variants
                variants = await self._create_variants(img, original_filename)
                
                # Optimize original
                optimized = await self._optimize_original(img, original_filename)
                
                return {
                    'metadata': metadata,
                    'variants': variants,
                    'optimized_original': optimized,
                    'processed': True
                }
        
        except Exception as e:
            return {
                'error': str(e),
                'processed': False
            }
    
    async def _extract_metadata(self, img: Image.Image) -> Dict[str, Any]:
        """Extract image metadata including EXIF."""
        metadata = {
            'width': img.width,
            'height': img.height,
            'format': img.format,
            'mode': img.mode,
            'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
        }
        
        # Extract EXIF data
        if hasattr(img, '_getexif') and img._getexif():
            exif = img._getexif()
            exif_data = {}
            
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                
                # Handle GPS data
                if tag == 'GPSInfo':
                    gps_data = {}
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = ExifTags.GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = str(gps_value)
                    exif_data['GPSInfo'] = gps_data
                else:
                    # Convert to string to ensure JSON serialization
                    exif_data[tag] = str(value)
            
            metadata['exif'] = exif_data
        
        return metadata
    
    async def _create_variants(
        self,
        img: Image.Image,
        filename: str
    ) -> List[Dict[str, Any]]:
        """Create different sized variants of the image."""
        variants = []
        base_name, ext = os.path.splitext(filename)
        
        for variant_name, variant_config in self.variants.items():
            try:
                # Calculate dimensions maintaining aspect ratio
                ratio = min(
                    variant_config.width / img.width,
                    variant_config.height / img.height
                )
                
                if ratio < 1:  # Only resize if smaller than original
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    
                    # Resize image
                    resized = img.resize(
                        (new_width, new_height),
                        Image.Resampling.LANCZOS
                    )
                    
                    # Save variant
                    variant_filename = f"{base_name}_{variant_name}.jpg"
                    variant_buffer = io.BytesIO()
                    
                    resized.save(
                        variant_buffer,
                        format='JPEG',
                        quality=variant_config.quality,
                        optimize=True
                    )
                    
                    variants.append({
                        'name': variant_name,
                        'filename': variant_filename,
                        'width': new_width,
                        'height': new_height,
                        'size': len(variant_buffer.getvalue()),
                        'content': variant_buffer.getvalue()
                    })
            
            except Exception as e:
                print(f"Error creating variant {variant_name}: {e}")
                continue
        
        return variants
    
    async def _optimize_original(
        self,
        img: Image.Image,
        filename: str
    ) -> Dict[str, Any]:
        """Optimize original image without resizing."""
        try:
            buffer = io.BytesIO()
            
            # Determine format
            format_map = {
                '.jpg': 'JPEG',
                '.jpeg': 'JPEG',
                '.png': 'PNG',
                '.webp': 'WebP'
            }
            
            ext = os.path.splitext(filename)[1].lower()
            output_format = format_map.get(ext, 'JPEG')
            
            # Optimize settings based on format
            save_kwargs = {'optimize': True}
            
            if output_format == 'JPEG':
                save_kwargs['quality'] = 90
                save_kwargs['progressive'] = True
            elif output_format == 'PNG':
                save_kwargs['compress_level'] = 6
            elif output_format == 'WebP':
                save_kwargs['quality'] = 85
                save_kwargs['method'] = 6
            
            img.save(buffer, format=output_format, **save_kwargs)
            
            return {
                'content': buffer.getvalue(),
                'format': output_format,
                'size': len(buffer.getvalue()),
                'optimized': True
            }
        
        except Exception as e:
            return {
                'error': str(e),
                'optimized': False
            }
```

## Upload Context

```python
# app/contexts/uploads.py
from zenith import Context, UploadFile
from app.models.file import File, UploadSession, FileStatus, FileType
from app.models.user import User
from app.services.validation import FileValidator
from app.services.processing.images import ImageProcessor
from app.services.storage.s3 import S3Storage
from sqlmodel import select
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
import tempfile

class UploadsContext(Context):
    """File upload business logic."""
    
    def __init__(
        self,
        validator: FileValidator,
        image_processor: ImageProcessor,
        storage: S3Storage
    ):
        super().__init__()
        self.validator = validator
        self.image_processor = image_processor
        self.storage = storage
    
    async def upload_single_file(
        self,
        file: UploadFile,
        uploader: Optional[User] = None,
        is_public: bool = False
    ) -> File:
        """Upload a single file."""
        # Read file content
        content = await file.read()
        
        # Validate file
        validation = await self.validator.validate_file(file, content)
        if not validation.is_valid:
            raise ValueError(f"File validation failed: {', '.join(validation.errors)}")
        
        # Determine file type
        file_type = self._determine_file_type(validation.detected_mime_type)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        extension = os.path.splitext(file.filename)[1] if file.filename else ''
        unique_filename = f"{file_id}{extension}"
        
        # Create file record
        file_record = File(
            filename=unique_filename,
            original_filename=file.filename or 'unknown',
            file_path=f"uploads/{unique_filename}",
            file_type=file_type,
            mime_type=validation.detected_mime_type,
            size=len(content),
            checksum_md5=validation.file_info.get('md5'),
            checksum_sha256=validation.file_info.get('sha256'),
            status=FileStatus.PROCESSING,
            metadata=validation.file_info,
            is_public=is_public,
            uploader_id=uploader.id if uploader else None
        )
        
        if not is_public:
            file_record.access_token = str(uuid.uuid4())
        
        # Save to database
        self.db.add(file_record)
        await self.db.commit()
        await self.db.refresh(file_record)
        
        try:
            # Upload original file
            await self.storage.upload(
                content,
                file_record.file_path,
                validation.detected_mime_type
            )
            
            # Process file if needed
            if file_type == FileType.IMAGE:
                await self._process_image(file_record, content)
            
            # Update status
            file_record.status = FileStatus.READY
            await self.db.commit()
            
            return file_record
        
        except Exception as e:
            # Update with error status
            file_record.status = FileStatus.ERROR
            file_record.error_message = str(e)
            await self.db.commit()
            raise
    
    async def upload_multiple_files(
        self,
        files: List[UploadFile],
        uploader: Optional[User] = None,
        is_public: bool = False
    ) -> List[File]:
        """Upload multiple files."""
        uploaded_files = []
        errors = []
        
        for file in files:
            try:
                uploaded_file = await self.upload_single_file(file, uploader, is_public)
                uploaded_files.append(uploaded_file)
            except Exception as e:
                errors.append({
                    'filename': file.filename,
                    'error': str(e)
                })
        
        if errors and not uploaded_files:
            raise ValueError(f"All uploads failed: {errors}")
        
        return uploaded_files
    
    async def init_chunked_upload(
        self,
        filename: str,
        total_size: int,
        mime_type: str,
        chunk_size: int,
        uploader: Optional[User] = None
    ) -> UploadSession:
        """Initialize chunked upload session."""
        upload_id = str(uuid.uuid4())
        total_chunks = (total_size + chunk_size - 1) // chunk_size
        
        # Create temporary directory
        temp_path = os.path.join(tempfile.gettempdir(), f"upload_{upload_id}")
        os.makedirs(temp_path, exist_ok=True)
        
        session = UploadSession(
            id=upload_id,
            filename=filename,
            total_size=total_size,
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            temp_path=temp_path,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            uploader_id=uploader.id if uploader else None
        )
        
        self.db.add(session)
        await self.db.commit()
        
        return session
    
    async def upload_chunk(
        self,
        upload_id: str,
        chunk_number: int,
        chunk_data: bytes
    ) -> Dict[str, Any]:
        """Upload a single chunk."""
        # Get upload session
        session = await self.db.get(UploadSession, upload_id)
        if not session:
            raise ValueError("Upload session not found")
        
        if session.status != FileStatus.UPLOADING:
            raise ValueError("Upload session is not active")
        
        # Save chunk to temporary file
        chunk_path = os.path.join(session.temp_path, f"chunk_{chunk_number}")
        with open(chunk_path, 'wb') as f:
            f.write(chunk_data)
        
        # Update session
        session.uploaded_chunks += 1
        await self.db.commit()
        
        # Check if upload is complete
        if session.uploaded_chunks >= session.total_chunks:
            await self._finalize_chunked_upload(session)
        
        return {
            'uploaded_chunks': session.uploaded_chunks,
            'total_chunks': session.total_chunks,
            'complete': session.uploaded_chunks >= session.total_chunks
        }
    
    async def _finalize_chunked_upload(self, session: UploadSession):
        """Combine chunks into final file."""
        try:
            # Combine chunks
            final_content = bytearray()
            for chunk_num in range(session.total_chunks):
                chunk_path = os.path.join(session.temp_path, f"chunk_{chunk_num}")
                with open(chunk_path, 'rb') as f:
                    final_content.extend(f.read())
            
            # Create upload file object
            class ChunkedUploadFile:
                def __init__(self, filename: str, content: bytes):
                    self.filename = filename
                    self.content_type = 'application/octet-stream'
                    self._content = content
                
                async def read(self):
                    return self._content
                
                async def seek(self, position):
                    pass
            
            upload_file = ChunkedUploadFile(session.filename, bytes(final_content))
            
            # Process as single file
            uploader = await self.db.get(User, session.uploader_id) if session.uploader_id else None
            file_record = await self.upload_single_file(upload_file, uploader)
            
            # Update session
            session.status = FileStatus.READY
            session.final_file_id = file_record.id
            await self.db.commit()
            
            # Cleanup temporary files
            await self._cleanup_temp_files(session.temp_path)
        
        except Exception as e:
            session.status = FileStatus.ERROR
            session.error_message = str(e)
            await self.db.commit()
            raise
    
    async def _process_image(self, file_record: File, content: bytes):
        """Process uploaded image."""
        processing_result = await self.image_processor.process_image(
            content, file_record.original_filename
        )
        
        if processing_result.get('processed'):
            # Update metadata
            current_metadata = file_record.metadata or {}
            current_metadata.update(processing_result['metadata'])
            file_record.metadata = current_metadata
            
            # Upload optimized original
            if 'optimized_original' in processing_result:
                opt = processing_result['optimized_original']
                if opt.get('optimized') and opt.get('content'):
                    await self.storage.upload(
                        opt['content'],
                        file_record.file_path,
                        file_record.mime_type,
                        overwrite=True
                    )
            
            # Upload variants
            for variant in processing_result.get('variants', []):
                variant_path = f"variants/{file_record.filename}_{variant['name']}.jpg"
                await self.storage.upload(
                    variant['content'],
                    variant_path,
                    'image/jpeg'
                )
                
                # Add variant to file record
                file_record.add_variant({
                    'name': variant['name'],
                    'path': variant_path,
                    'width': variant['width'],
                    'height': variant['height'],
                    'size': variant['size']
                })
            
            # Create thumbnail path reference
            thumbnail_variant = next(
                (v for v in processing_result.get('variants', []) if v['name'] == 'thumbnail'),
                None
            )
            if thumbnail_variant:
                file_record.thumbnail_path = f"variants/{file_record.filename}_thumbnail.jpg"
    
    async def get_file(self, file_id: int) -> Optional[File]:
        """Get file by ID."""
        return await self.db.get(File, file_id)
    
    async def get_user_files(
        self,
        user: User,
        skip: int = 0,
        limit: int = 20,
        file_type: Optional[FileType] = None
    ) -> List[File]:
        """Get files uploaded by user."""
        statement = select(File).where(File.uploader_id == user.id)
        
        if file_type:
            statement = statement.where(File.file_type == file_type)
        
        statement = statement.offset(skip).limit(limit).order_by(File.created_at.desc())
        
        result = await self.db.exec(statement)
        return result.all()
    
    async def delete_file(self, file_id: int, user: Optional[User] = None) -> bool:
        """Delete file."""
        file_record = await self.db.get(File, file_id)
        if not file_record:
            return False
        
        # Check permissions
        if user and file_record.uploader_id != user.id:
            raise PermissionError("Not authorized to delete this file")
        
        try:
            # Delete from storage
            await self.storage.delete(file_record.file_path)
            
            # Delete variants
            if file_record.thumbnail_path:
                await self.storage.delete(file_record.thumbnail_path)
            
            for variant in file_record.variants:
                await self.storage.delete(variant['path'])
            
            # Update database
            file_record.status = FileStatus.DELETED
            await self.db.commit()
            
            return True
        
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def _determine_file_type(self, mime_type: str) -> FileType:
        """Determine file type from MIME type."""
        if mime_type.startswith('image/'):
            return FileType.IMAGE
        elif mime_type.startswith('video/'):
            return FileType.VIDEO
        elif mime_type.startswith('audio/'):
            return FileType.AUDIO
        elif mime_type in ['application/pdf', 'application/msword',
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return FileType.DOCUMENT
        elif mime_type in ['application/zip', 'application/x-rar-compressed',
                          'application/x-tar', 'application/gzip']:
            return FileType.ARCHIVE
        else:
            return FileType.OTHER
    
    async def _cleanup_temp_files(self, temp_path: str):
        """Clean up temporary upload files."""
        try:
            import shutil
            shutil.rmtree(temp_path, ignore_errors=True)
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")
```

## Upload Routes

```python
# app/routes/uploads.py
from zenith import Router, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from zenith.auth import get_current_user
from app.contexts.uploads import UploadsContext
from app.models.file import FileUploadResponse, ChunkedUploadInit, ChunkedUploadResponse
from app.models.user import User
from typing import List, Optional

router = Router(prefix="/uploads", tags=["File Uploads"])

@router.post("/single", response_model=FileUploadResponse)
async def upload_single_file(
    file: UploadFile = File(..., description="File to upload"),
    is_public: bool = Form(False),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    uploads: UploadsContext = Depends()
):
    """Upload a single file."""
    try:
        uploaded_file = await uploads.upload_single_file(
            file, current_user, is_public
        )
        
        # Generate download URL
        download_url = f"/files/{uploaded_file.id}/download"
        if not is_public:
            download_url += f"?token={uploaded_file.access_token}"
        
        # Generate thumbnail URL if available
        thumbnail_url = None
        if uploaded_file.thumbnail_path:
            thumbnail_url = f"/files/{uploaded_file.id}/thumbnail"
            if not is_public:
                thumbnail_url += f"?token={uploaded_file.access_token}"
        
        return FileUploadResponse(
            id=uploaded_file.id,
            filename=uploaded_file.original_filename,
            size=uploaded_file.size,
            mime_type=uploaded_file.mime_type,
            file_type=uploaded_file.file_type,
            status=uploaded_file.status,
            download_url=download_url,
            thumbnail_url=thumbnail_url,
            metadata=uploaded_file.metadata,
            created_at=uploaded_file.created_at
        )
    
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

@router.post("/multiple", response_model=List[FileUploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="Files to upload"),
    is_public: bool = Form(False),
    current_user: User = Depends(get_current_user),
    uploads: UploadsContext = Depends()
):
    """Upload multiple files."""
    if len(files) > 10:  # Limit batch size
        raise HTTPException(400, "Maximum 10 files per batch")
    
    try:
        uploaded_files = await uploads.upload_multiple_files(
            files, current_user, is_public
        )
        
        responses = []
        for uploaded_file in uploaded_files:
            download_url = f"/files/{uploaded_file.id}/download"
            if not is_public:
                download_url += f"?token={uploaded_file.access_token}"
            
            thumbnail_url = None
            if uploaded_file.thumbnail_path:
                thumbnail_url = f"/files/{uploaded_file.id}/thumbnail"
                if not is_public:
                    thumbnail_url += f"?token={uploaded_file.access_token}"
            
            responses.append(FileUploadResponse(
                id=uploaded_file.id,
                filename=uploaded_file.original_filename,
                size=uploaded_file.size,
                mime_type=uploaded_file.mime_type,
                file_type=uploaded_file.file_type,
                status=uploaded_file.status,
                download_url=download_url,
                thumbnail_url=thumbnail_url,
                metadata=uploaded_file.metadata,
                created_at=uploaded_file.created_at
            ))
        
        return responses
    
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

@router.post("/chunked/init", response_model=ChunkedUploadResponse)
async def init_chunked_upload(
    upload_init: ChunkedUploadInit,
    current_user: User = Depends(get_current_user),
    uploads: UploadsContext = Depends()
):
    """Initialize chunked upload."""
    try:
        session = await uploads.init_chunked_upload(
            upload_init.filename,
            upload_init.total_size,
            upload_init.mime_type,
            upload_init.chunk_size,
            current_user
        )
        
        # Generate pre-signed URLs for each chunk
        upload_urls = []
        for chunk_num in range(session.total_chunks):
            upload_urls.append(f"/uploads/chunked/{session.id}/chunk/{chunk_num}")
        
        return ChunkedUploadResponse(
            upload_id=session.id,
            total_chunks=session.total_chunks,
            chunk_size=session.chunk_size,
            upload_urls=upload_urls
        )
    
    except Exception as e:
        raise HTTPException(500, f"Failed to initialize upload: {str(e)}")

@router.put("/chunked/{upload_id}/chunk/{chunk_number}")
async def upload_chunk(
    upload_id: str,
    chunk_number: int,
    file: UploadFile = File(...),
    uploads: UploadsContext = Depends()
):
    """Upload a single chunk."""
    try:
        chunk_data = await file.read()
        result = await uploads.upload_chunk(upload_id, chunk_number, chunk_data)
        return result
    
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Chunk upload failed: {str(e)}")

@router.get("/progress/{upload_id}")
async def get_upload_progress(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    uploads: UploadsContext = Depends()
):
    """Get chunked upload progress."""
    session = await uploads.db.get(UploadSession, upload_id)
    if not session:
        raise HTTPException(404, "Upload session not found")
    
    if session.uploader_id != current_user.id:
        raise HTTPException(403, "Not authorized")
    
    progress = (session.uploaded_chunks / session.total_chunks) * 100
    
    return {
        'upload_id': upload_id,
        'progress': round(progress, 2),
        'uploaded_chunks': session.uploaded_chunks,
        'total_chunks': session.total_chunks,
        'status': session.status,
        'error_message': session.error_message
    }
```

## Client-Side Upload Interface

```javascript
// app/static/upload.js
class FileUploader {
    constructor(token) {
        this.token = token;
        this.uploadQueue = [];
        this.activeUploads = new Map();
        this.maxConcurrentUploads = 3;
    }
    
    async uploadSingle(file, isPublic = false, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('is_public', isPublic);
        
        const xhr = new XMLHttpRequest();
        
        return new Promise((resolve, reject) => {
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const progress = (e.loaded / e.total) * 100;
                    onProgress(progress);
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(xhr.responseText));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });
            
            xhr.open('POST', '/uploads/single');
            xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
            xhr.send(formData);
        });
    }
    
    async uploadChunked(file, chunkSize = 1024 * 1024, onProgress = null) {
        // Initialize chunked upload
        const initResponse = await fetch('/uploads/chunked/init', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: file.name,
                total_size: file.size,
                chunk_size: chunkSize,
                mime_type: file.type
            })
        });
        
        if (!initResponse.ok) {
            throw new Error('Failed to initialize upload');
        }
        
        const { upload_id, total_chunks, upload_urls } = await initResponse.json();
        
        // Upload chunks
        const uploadPromises = [];
        for (let i = 0; i < total_chunks; i++) {
            const start = i * chunkSize;
            const end = Math.min(start + chunkSize, file.size);
            const chunk = file.slice(start, end);
            
            uploadPromises.push(this.uploadChunk(upload_id, i, chunk));
        }
        
        // Track progress
        let completedChunks = 0;
        const chunkPromises = uploadPromises.map(async (promise, index) => {
            const result = await promise;
            completedChunks++;
            
            if (onProgress) {
                const progress = (completedChunks / total_chunks) * 100;
                onProgress(progress);
            }
            
            return result;
        });
        
        await Promise.all(chunkPromises);
        
        // Get final result
        return await this.getUploadProgress(upload_id);
    }
    
    async uploadChunk(uploadId, chunkNumber, chunk) {
        const formData = new FormData();
        formData.append('file', chunk);
        
        const response = await fetch(`/uploads/chunked/${uploadId}/chunk/${chunkNumber}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Failed to upload chunk ${chunkNumber}`);
        }
        
        return await response.json();
    }
    
    async getUploadProgress(uploadId) {
        const response = await fetch(`/uploads/progress/${uploadId}`, {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to get progress');
        }
        
        return await response.json();
    }
}

// Initialize uploader
const token = localStorage.getItem('auth_token');
const uploader = new FileUploader(token);

// File input handler
document.getElementById('file-input').addEventListener('change', async (e) => {
    const files = Array.from(e.target.files);
    
    for (const file of files) {
        const progressDiv = createProgressElement(file.name);
        
        try {
            // Use chunked upload for large files
            if (file.size > 10 * 1024 * 1024) { // 10MB
                await uploader.uploadChunked(file, 1024 * 1024, (progress) => {
                    updateProgress(progressDiv, progress);
                });
            } else {
                await uploader.uploadSingle(file, false, (progress) => {
                    updateProgress(progressDiv, progress);
                });
            }
            
            showSuccess(progressDiv, 'Upload complete');
        } catch (error) {
            showError(progressDiv, error.message);
        }
    }
});

function createProgressElement(filename) {
    const div = document.createElement('div');
    div.className = 'upload-progress';
    div.innerHTML = `
        <div class="filename">${filename}</div>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        <div class="status">Uploading...</div>
    `;
    document.getElementById('uploads-container').appendChild(div);
    return div;
}

function updateProgress(element, progress) {
    const fill = element.querySelector('.progress-fill');
    const status = element.querySelector('.status');
    
    fill.style.width = `${progress}%`;
    status.textContent = `${Math.round(progress)}%`;
}

function showSuccess(element, message) {
    element.classList.add('success');
    element.querySelector('.status').textContent = message;
}

function showError(element, message) {
    element.classList.add('error');
    element.querySelector('.status').textContent = `Error: ${message}`;
}
```

<Aside type="tip">
  **Performance Tip**: This upload service includes automatic image optimization, chunked uploads for large files, and cloud storage integration for scalable file handling.
</Aside>

## Testing File Uploads

```python
# tests/test_uploads.py
import pytest
from zenith.testing import TestClient
from app.main import app
import io

@pytest.mark.asyncio
async def test_single_file_upload():
    async with TestClient(app) as client:
        # Create test file
        file_content = b"test file content"
        files = {
            "file": ("test.txt", io.BytesIO(file_content), "text/plain")
        }
        
        response = await client.post(
            "/uploads/single",
            files=files,
            data={"is_public": "false"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["filename"] == "test.txt"
        assert result["size"] == len(file_content)
        assert "download_url" in result

@pytest.mark.asyncio
async def test_image_processing():
    async with TestClient(app) as client:
        # Create test image (1x1 pixel PNG)
        image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {
            "file": ("test.png", io.BytesIO(image_data), "image/png")
        }
        
        response = await client.post(
            "/uploads/single",
            files=files,
            data={"is_public": "true"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["file_type"] == "image"
        assert "thumbnail_url" in result
```

## Next Steps

- Add [background tasks](/features/background-tasks) for async processing
- Implement [CDN integration](/deployment/cdn) for global file delivery
- Add [virus scanning](/concepts/middleware#virus-scanning) with ClamAV
- Scale with [Redis](/concepts/database) for upload session storage