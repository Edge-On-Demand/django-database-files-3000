import os

import six

from django.core import files
from django.core.files.storage import FileSystemStorage

from .models import File
from database_files import utils
from database_files import settings as _settings


class DatabaseStorage(FileSystemStorage):
    def _open(self, name, mode='rb'):
        """
        Open file with filename `name` from the database.
        """
        try:
            # Load file from database.
            f = File.objects.get_from_name(name)
            content = f.content
            size = f.size
            if _settings.DB_FILES_AUTO_EXPORT_DB_TO_FS and not utils.is_fresh(f.name, f.content_hash):
                # Automatically write the file to the filesystem
                # if it's missing and exists in the database.
                # This happens if we're using multiple web servers connected
                # to a common databaes behind a load balancer.
                # One user might upload a file from one web server, and then
                # another might access if from another server.
                utils.write_file(f.name, f.content)
        except File.DoesNotExist:
            # If not yet in the database, check the local file system
            # and load it into the database if present.
            fqfn = self.path(name)
            if os.path.isfile(fqfn):
                self._save(name, open(fqfn, mode))
                fh = super(DatabaseStorage, self)._open(name, mode)
                content = fh.read()
                size = fh.size
            else:
                # Otherwise we don't know where the file is.
                return None
        # Normalize the content to a new file object.
        fh = six.BytesIO(content)
        fh.name = name
        fh.mode = mode
        fh.size = size
        o = files.File(fh)
        return o

    def _save(self, name, content):
        """
        Save file with filename `name` and given content to the database.
        """
        full_path = self.path(name)
        try:
            size = content.size
        except AttributeError:
            size = os.path.getsize(full_path)
        content.seek(0)
        content = content.read()
        File.objects.create(content=content, size=size, name=name)
        # Automatically write the change to the local file system.
        if _settings.DB_FILES_AUTO_EXPORT_DB_TO_FS:
            utils.write_file(name, content, overwrite=True)
        return name

    def exists(self, name):
        """
        Returns true if a file with the given filename exists in the database.
        Returns false otherwise.
        """
        if File.objects.filter(name=name).exists():
            return True
        return super(DatabaseStorage, self).exists(name)

    def delete(self, name):
        """
        Deletes the file with filename `name` from the database and filesystem.
        """
        try:
            File.objects.get_from_name(name).delete()
            hash_fn = utils.get_hash_fn(name)
            if os.path.isfile(hash_fn):
                os.remove(hash_fn)
        except File.DoesNotExist:
            pass
        return super(DatabaseStorage, self).delete(name)

    def url(self, name):
        """
        Returns the web-accessible URL for the file with filename `name`.
        """
        return _settings.DATABASE_FILES_URL_METHOD(name)

    def size(self, name):
        """
        Returns the size of the file with filename `name` in bytes.
        """
        try:
            return File.objects.get_from_name(name).size
        except File.DoesNotExist:
            return super(DatabaseStorage, self).size(name)
