from mongoengine import Document, StringField, DateTimeField, ReferenceField, ListField, ObjectIdField, IntField, BooleanField
from mongoengine.fields import EmbeddedDocumentField, EmbeddedDocument, DictField
from datetime import datetime
from users.models import User


class Scenario(Document):
    """
    Modèle pour représenter un scénario interactif (livre)
    """
    meta = {
        'collection': 'scenarios',
        'indexes': [
            'author_id',
            'title',
            'created_at'
        ]
    }
    
    title = StringField(required=True, max_length=200)
    description = StringField(max_length=1000)
    author_id = ReferenceField(User, required=True)
    scenes = ListField(ReferenceField('Scene'))
    is_published = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Scenario"
        verbose_name_plural = "Scenarios"


class Scene(Document):
    """
    Modèle pour représenter une scène dans un scénario
    """
    meta = {
        'collection': 'scenes',
        'indexes': [
            'scenario_id',
            'title',
            'order'
        ]
    }
    
    scenario_id = ReferenceField(Scenario, required=True)
    title = StringField(required=True, max_length=200)
    text = StringField(required=True)
    order = IntField(default=0)  # Ordre dans le scénario
    image_id = ReferenceField('Asset')  # Asset image optionnel
    sound_id = ReferenceField('Asset')  # Asset son optionnel
    choices = ListField(ReferenceField('Choice'))
    is_start_scene = BooleanField(default=False)  # Scène de début
    is_end_scene = BooleanField(default=False)    # Scène de fin
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.scenario_id.title}"
    
    class Meta:
        verbose_name = "Scene"
        verbose_name_plural = "Scenes"


class Choice(Document):
    """
    Modèle pour représenter un choix entre deux scènes
    """
    meta = {
        'collection': 'choices',
        'indexes': [
            'from_scene_id',
            'to_scene_id',
            'text'
        ]
    }
    
    from_scene_id = ReferenceField(Scene, required=True)
    to_scene_id = ReferenceField(Scene, required=True)
    text = StringField(required=True, max_length=200)
    condition = DictField()  # Condition optionnelle pour afficher le choix
    order = IntField(default=0)  # Ordre d'affichage des choix
    created_at = DateTimeField(default=datetime.utcnow)
    
    def __str__(self):
        return f"{self.text} ({self.from_scene_id.title} → {self.to_scene_id.title})"
    
    class Meta:
        verbose_name = "Choice"
        verbose_name_plural = "Choices"
