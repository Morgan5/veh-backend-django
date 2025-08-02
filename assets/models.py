from mongoengine import Document, StringField, DateTimeField, ReferenceField, ObjectIdField, DictField, IntField, BooleanField
from datetime import datetime
from users.models import User


class Asset(Document):
    """
    Modèle pour gérer les assets (images et sons) liés aux scènes
    """
    meta = {
        'collection': 'assets',
        'indexes': [
            'type',
            'name',
            'uploaded_by',
            'created_at'
        ]
    }
    
    ASSET_TYPES = [
        ('image', 'Image'),
        ('sound', 'Sound'),
        ('video', 'Video'),
    ]
    
    type = StringField(required=True, choices=[choice[0] for choice in ASSET_TYPES])
    name = StringField(required=True, max_length=200)
    filename = StringField(required=True)  # Nom du fichier sur le serveur
    url = StringField(required=True)  # URL publique de l'asset
    file_size = IntField()  # Taille en bytes
    mime_type = StringField()  # Type MIME
    metadata = DictField()  # Métadonnées (dimensions, durée, etc.)
    uploaded_by = ReferenceField(User, required=True)
    is_public = BooleanField(default=True)  # Si l'asset est public
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def get_file_extension(self):
        """Obtenir l'extension du fichier"""
        return self.filename.split('.')[-1] if '.' in self.filename else ''
    
    def get_file_size_mb(self):
        """Obtenir la taille en MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def is_image(self):
        """Vérifier si c'est une image"""
        return self.type == 'image'
    
    def is_sound(self):
        """Vérifier si c'est un son"""
        return self.type == 'sound'
    
    def is_video(self):
        """Vérifier si c'est une vidéo"""
        return self.type == 'video'
    
    def get_dimensions(self):
        """Obtenir les dimensions pour les images/vidéos"""
        if self.metadata and 'width' in self.metadata and 'height' in self.metadata:
            return f"{self.metadata['width']}x{self.metadata['height']}"
        return None
    
    def get_duration(self):
        """Obtenir la durée pour les sons/vidéos"""
        if self.metadata and 'duration' in self.metadata:
            return self.metadata['duration']
        return None
    
    def __str__(self):
        return f"{self.name} ({self.type})"
    
    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
