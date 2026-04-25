from django.core.files.storage import Storage
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import io
import logging

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024

class GoogleDriveStorage(Storage):
    def __init__(self):
        self.service = None
        logger.info("Initializing GoogleDriveStorage")
    
    def _get_service(self):
        if self.service:
            return self.service
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        creds_path = os.path.join(base_dir, 'credentials.json')
        token_path = os.path.join(base_dir, 'token.json')
        
        creds = None
        
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(creds_path):
                    logger.error(f"credentials.json not found at {creds_path}")
                    raise FileNotFoundError(f"credentials.json not found")
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
        return self.service
    
    def _save(self, name, content):
        try:
            service = self._get_service()

            max_size = MAX_UPLOAD_SIZE_BYTES
            if hasattr(content, 'size') and content.size > max_size:
                raise ValueError("File size exceeds 50 MB limit.")

            if hasattr(content, 'seek'):
                try:
                    content.seek(0)
                except Exception:
                    pass

            if hasattr(content, 'seek'):
                try:
                    content.seek(0)
                except Exception:
                    pass
            file_content = content.read()
            name = os.path.basename(name)
            file_metadata = {'name': name, 'mimeType': getattr(content, 'content_type', 'application/octet-stream') or 'application/octet-stream'}
            media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=file_metadata['mimeType'], resumable=True)

            result = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            file_id = result.get('id')
            if not file_id:
                raise ValueError('Google Drive upload returned no file ID')
            try:
                service.permissions().create(
                    fileId=file_id,
                    body={"type": "anyone", "role": "reader"},
                ).execute()
            except Exception:
                pass
            logger.info(f"Uploaded {name} to Google Drive with ID: {file_id}")
            return file_id
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {e}")
            raise

    def delete(self, name):
        try:
            service = self._get_service()
            service.files().delete(fileId=name).execute()
            logger.info(f"Deleted file {name} from Google Drive")
        except Exception as e:
            logger.warning(f"Error deleting file {name}: {e}")

    def exists(self, name):
        try:
            service = self._get_service()
            service.files().get(fileId=name).execute()
            return True
        except Exception:
            return False

    def url(self, name):
        if not name:
            return ''
        if isinstance(name, str) and (name.startswith('http://') or name.startswith('https://')):
            return name
        try:
            service = self._get_service()
            result = service.files().get(fileId=name, fields='webViewLink,webContentLink').execute()
            link = result.get('webViewLink') or result.get('webContentLink')
            if not link:
                link = f'https://drive.google.com/uc?id={name}&export=download'
            logger.info(f"Generated URL for {name}: {link}")
            return link
        except Exception as e:
            logger.warning(f"Error getting URL for {name}: {e}")
            return f'https://drive.google.com/uc?id={name}&export=download'

    def path(self, name):
        raise NotImplementedError("GoogleDriveStorage does not support local filesystem paths.")

    def open(self, name, mode='rb'):
        raise NotImplementedError("GoogleDriveStorage does not support opening files locally.")

    def size(self, name):
        try:
            service = self._get_service()
            result = service.files().get(fileId=name, fields='size').execute()
            return int(result.get('size', 0))
        except Exception:
            return 0

    def accessed_time(self, name):
        return None

    def created_time(self, name):
        return None

    def modified_time(self, name):
        return None
