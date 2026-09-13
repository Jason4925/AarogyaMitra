from pathlib import Path
try:
    from supabase import create_client
except Exception:
    create_client = None
from .config import SUPABASE_URL, SUPABASE_STORAGE_BUCKET, SUPABASE_SERVICE_KEY

def _client():
    if create_client is None: raise RuntimeError('supabase package is not installed.')
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY: raise RuntimeError('Supabase Storage service credentials are not configured.')
    return create_client(SUPABASE_URL,SUPABASE_SERVICE_KEY)

def upload_report_document(user_id, report_id, filename, content, content_type='application/pdf'):
    client=_client(); safe=Path(filename).name.replace(' ','_'); path=f'{user_id}/{report_id}/{safe}'
    client.storage.from_(SUPABASE_STORAGE_BUCKET).upload(path,content,file_options={'content-type':content_type,'upsert':True}); return path

def delete_user_documents(user_id, known_paths=None):
    """Best-effort deletion of all Storage objects under the user's folder."""
    client=_client(); bucket=client.storage.from_(SUPABASE_STORAGE_BUCKET)
    paths=list(known_paths or [])
    try:
        entries=bucket.list(user_id) or []
        for item in entries:
            name=item.get('name') if isinstance(item,dict) else getattr(item,'name',None)
            if name:
                # Report documents are stored one level below report folders; list folders too.
                try:
                    nested=bucket.list(f'{user_id}/{name}') or []
                    for n in nested:
                        nn=n.get('name') if isinstance(n,dict) else getattr(n,'name',None)
                        if nn: paths.append(f'{user_id}/{name}/{nn}')
                except Exception:
                    paths.append(f'{user_id}/{name}')
    except Exception:
        pass
    paths=sorted(set(p for p in paths if p))
    if paths: bucket.remove(paths)
